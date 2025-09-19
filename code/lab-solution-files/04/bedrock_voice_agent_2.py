# bedrock_voice_agent.py
import argparse
import os
from datetime import datetime

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from loguru import logger
from pipecat.adapters.schemas.function_schema import FunctionSchema
from pipecat.adapters.schemas.tools_schema import ToolsSchema
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.frames.frames import LLMRunFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.runner.types import RunnerArguments
from pipecat.runner.utils import create_transport
from pipecat.services.aws.llm import AWSBedrockLLMService
from pipecat.services.aws.stt import AWSTranscribeSTTService
from pipecat.services.aws.tts import AWSPollyTTSService
from pipecat.services.aws_nova_sonic import AWSNovaSonicLLMService
from pipecat.services.llm_service import FunctionCallParams
from pipecat.transports.base_transport import BaseTransport, TransportParams
from pipecat.transports.daily.transport import DailyParams

# Load environment variables
load_dotenv(override=True)

# Bedrock Knowledge Base Configuration
KNOWLEDGE_BASE_ID = "STFZ4NQBSR"


class BedrockKnowledgeBaseClient:
    """Client for interacting with Amazon Bedrock Knowledge Base"""

    def __init__(self, knowledge_base_id: str):
        self.knowledge_base_id = knowledge_base_id
        self.bedrock_agent_runtime = boto3.client(
            "bedrock-agent-runtime",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION", "us-east-1"),
        )
        logger.info(
            f"Initialized Bedrock Knowledge Base client for KB: {knowledge_base_id}"
        )

    async def query_knowledge_base(self, query: str, max_results: int = 10) -> str:
        """Query the Bedrock Knowledge Base and return formatted response"""
        try:
            logger.info(f"Querying knowledge base with: {query}")

            # Enhanced query for better claim ID matching
            enhanced_query = query
            if any(
                keyword in query.lower()
                for keyword in ["claim", "id", "number", "reference", "ticket"]
            ):
                enhanced_query = f"claim ID {query}"

            response = self.bedrock_agent_runtime.retrieve(
                knowledgeBaseId=self.knowledge_base_id,
                retrievalQuery={"text": enhanced_query},
                retrievalConfiguration={
                    "vectorSearchConfiguration": {
                        "numberOfResults": max_results,
                        "overrideSearchType": "HYBRID",  # Use both semantic and keyword search
                    }
                },
            )

            # Extract and format the results
            results = response.get("retrievalResults", [])

            if not results:
                # Try alternative query if no results found
                logger.info(f"No results found, trying alternative query: {query}")
                alt_response = self.bedrock_agent_runtime.retrieve(
                    knowledgeBaseId=self.knowledge_base_id,
                    retrievalQuery={"text": query},
                    retrievalConfiguration={
                        "vectorSearchConfiguration": {
                            "numberOfResults": max_results,
                            "overrideSearchType": "SEMANTIC",
                        }
                    },
                )
                results = alt_response.get("retrievalResults", [])

            if not results:
                return f"I couldn't find any information about '{query}' in the knowledge base. Please check if the claim ID exists or try rephrasing your question."

            # Format the response with more detail
            formatted_response = f"Found {len(results)} result(s) for your query:\n\n"

            for i, result in enumerate(results[:5], 1):  # Show top 5 results
                content = result.get("content", {}).get("text", "")
                score = result.get("score", 0)
                source = (
                    result.get("location", {})
                    .get("s3Location", {})
                    .get("uri", "Unknown source")
                )

                if content:
                    # Show more content for claim-related queries
                    content_length = (
                        400
                        if any(keyword in query.lower() for keyword in ["claim", "id"])
                        else 200
                    )
                    truncated_content = content[:content_length]
                    if len(content) > content_length:
                        truncated_content += "..."

                    formatted_response += f"{i}. {truncated_content}\n"
                    formatted_response += f"   (Relevance: {score:.2f})\n\n"

            return formatted_response.strip()

        except ClientError as e:
            error_msg = f"Error querying knowledge base: {e}"
            logger.error(error_msg)
            return f"I encountered an error while searching for '{query}'. Please try again or contact support if the issue persists."
        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            logger.error(error_msg)
            return "I'm sorry, something went wrong while processing your request."


# Initialize Bedrock client
bedrock_client = BedrockKnowledgeBaseClient(KNOWLEDGE_BASE_ID)


async def search_knowledge_base(params: FunctionCallParams):
    """Single function to search Bedrock Knowledge Base for any query or claim ID"""
    query = params.arguments.get("query", "")

    if not query:
        await params.result_callback(
            {
                "error": "No query provided",
                "response": "Please provide a question or claim ID to search the knowledge base.",
            }
        )
        return

    logger.info(f"Searching knowledge base for: {query}")

    try:
        # Use the knowledge base client to search
        response_text = await bedrock_client.query_knowledge_base(query)

        await params.result_callback(
            {
                "query": query,
                "response": response_text,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "knowledge_base_id": KNOWLEDGE_BASE_ID,
            }
        )

    except Exception as e:
        logger.error(f"Error searching for {query}: {e}")
        await params.result_callback(
            {
                "query": query,
                "response": f"I encountered an error while searching for '{query}'. Please try again.",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "knowledge_base_id": KNOWLEDGE_BASE_ID,
            }
        )


# Define the single search function schema
search_function = FunctionSchema(
    name="search_knowledge_base",
    description="Search and retrieve information from the Amazon Bedrock Knowledge Base. Use this for any questions about claims, claim IDs, tickets, policy information, or general inquiries.",
    properties={
        "query": {
            "type": "string",
            "description": "The question, search query, claim ID, or ticket number to search for. Can be numbers like '1234', '3456', or questions like 'what is a claim?'",
        }
    },
    required=["query"],
)

# Create tools schema with single function
tools = ToolsSchema(standard_tools=[search_function])


async def run_bot(transport: BaseTransport, runner_args: RunnerArguments):
    logger.info("Starting Bedrock Knowledge Base Voice Agent")

    # System instruction for knowledge base integration
    system_instruction = (
        "You are a helpful AI assistant with access to a specialized knowledge base containing claim information. "
        "Use the search_knowledge_base function for all queries - whether they are specific claim IDs like '1234', '3456', or general questions. "
        "When users mention numbers, treat them as claim IDs and search for them directly. "
        "For claim estimates, costs, amounts, or any other information, always search for that specific information. "
        "Always provide helpful information about claims when found. "
        f"{AWSNovaSonicLLMService.AWAIT_TRIGGER_ASSISTANT_RESPONSE_INSTRUCTION}"
    )

    # Create the AWS Nova Sonic LLM service
    llm = AWSNovaSonicLLMService(
        secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        region=os.getenv("AWS_REGION", "us-east-1"),
        voice_id="tiffany",  # matthew, tiffany, amy
    )

    # Register the single search function
    llm.register_function("search_knowledge_base", search_knowledge_base)

    # Set up context and context management
    context = OpenAILLMContext(
        messages=[
            {"role": "system", "content": system_instruction},
            {
                "role": "user",
                "content": "Hello! I'm ready to help you find information from the knowledge base.",
            },
        ],
        tools=tools,
    )
    context_aggregator = llm.create_context_aggregator(context)

    # Build the pipeline
    pipeline = Pipeline(
        [
            transport.input(),
            context_aggregator.user(),
            llm,
            transport.output(),
            context_aggregator.assistant(),
        ]
    )

    # Configure the pipeline task
    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            allow_interruptions=True,
            enable_metrics=True,
            enable_usage_metrics=True,
        ),
    )

    # Handle client connection event
    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        logger.info("Client connected to Bedrock Knowledge Base Voice Agent")
        # Kick off the conversation
        await task.queue_frames([LLMRunFrame()])
        # Trigger the first assistant response
        await llm.trigger_assistant_response()

    # Handle client disconnection events
    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info("Client disconnected from Bedrock Knowledge Base Voice Agent")

    @transport.event_handler("on_client_closed")
    async def on_client_closed(transport, client):
        logger.info("Client closed connection to Bedrock Knowledge Base Voice Agent")
        await task.cancel()

    # Run the pipeline
    runner = PipelineRunner(handle_sigint=False)
    await runner.run(task)


async def bot(runner_args: RunnerArguments):
    """Main bot entry point for the bot starter."""

    transport_params = {
        "daily": lambda: DailyParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            vad_analyzer=SileroVADAnalyzer(),
        ),
        "webrtc": lambda: TransportParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            vad_analyzer=SileroVADAnalyzer(),
        ),
    }

    transport = await create_transport(runner_args, transport_params)

    await run_bot(transport, runner_args)


if __name__ == "__main__":
    from pipecat.runner.run import main

    main()
