# Agent with delegated tool selection

## strands_agent.py

```python
from mcp import stdio_client, StdioServerParameters
from strands import Agent, tool
from strands.tools.mcp import MCPClient
from strands.models import BedrockModel
import boto3 
import os
import json
import requests
import re

@tool
def weather(lat, lon: float) -> str:
    """Get weather information for a given lat and lon

    Args:
        lat: latitude of the location
        lon: logitude of the location
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": str(lat),
        "longitude": str(lon),
        "current_weather": True
    }
    response = requests.get(url, params=params)
    return response.json()["current_weather"]

class StrandsAgent:

    def __init__(self):
        # Launch AWS Location Service MCP Server and create a client object
        env = {"FASTMCP_LOG_LEVEL": "ERROR"}
        env['AWS_SECRET_ACCESS_KEY']=os.getenv("AWS_SECRET_ACCESS_KEY")
        env['AWS_ACCESS_KEY_ID']=os.getenv("AWS_ACCESS_KEY_ID")
        env['AWS_REGION']=os.getenv("AWS_REGION")

        self.aws_location_srv_client = MCPClient(lambda: stdio_client(
            StdioServerParameters(
                command="uvx", 
                args=["awslabs.aws-location-mcp-server@latest"],
                env=env)
            ))
        self._server_context = self.aws_location_srv_client.__enter__()
        self.aws_location_srv_tools = self.aws_location_srv_client.list_tools_sync()

        session = boto3.Session(
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name='us-east-1'
        )
        # Specify Bedrock LLM for the Agent
        bedrock_model = BedrockModel(
            model_id="amazon.nova-lite-v1:0",
            boto_session=session
        )
        # Create a Strands Agent
        tools = self.aws_location_srv_tools
        tools.append(weather)
        self.agent = Agent(
            tools=tools, 
            model=bedrock_model,
        )


    '''
    Send the input to the agent, allowing it to handle tool selection and invocation. 
    The response will be generated after the selected LLM performs reasoning. 
    This approach is suitable when you want to delegate tool selection logic to the agent, and have a generic toolUse definition in Sonic ToolUse.
    Note that the reasoning process may introduce latency, so it's recommended to use a lightweight model such as Nova Lite.
    Sample parameters: input="largest zoo in Seattle?"
    '''
    def query(self, input):
        output = str(self.agent(input))
        if "<response>" in output and "</response>" in output:
            output = re.search(r"<response>(.*?)</response>", output, re.DOTALL)
        elif "<answer>" in output and "</answer>" in output:
            output = re.search(r"<answer>(.*?)</answer>", output, re.DOTALL)
        return output

    '''
    Invoke the tool directly and return the raw response without any reasoning.
    This approach is suitable when tool selection is managed within Sonic and the exact toolName is already known. 
    It offers lower query latency, as no additional reasoning is performed by the agent.
    Sample parameters: tool_name="search_places", input="largest zoo in Seattle"
    '''
    def call_tool(self, tool_name, input):
        if isinstance(input, str):
            input = json.loads(input)
        if "query" in input:
            input = input.get("query")

        tool_func = getattr(self.agent.tool, tool_name)
        return tool_func(query=input)

    def close(self):
        # Cleanup the MCP server context
        self.aws_location_srv_client.__exit__(None, None, None)
```

## agent_delegated.py

```python
import argparse
import os
from datetime import datetime
from dotenv import load_dotenv
from loguru import logger

from pipecat.adapters.schemas.function_schema import FunctionSchema
from pipecat.adapters.schemas.tools_schema import ToolsSchema
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.services.aws_nova_sonic import AWSNovaSonicLLMService
from pipecat.services.llm_service import FunctionCallParams
from pipecat.transports.base_transport import TransportParams
from pipecat.transports.network.small_webrtc import SmallWebRTCTransport
from pipecat.transports.network.webrtc_connection import SmallWebRTCConnection

# Load environment variables
load_dotenv(override=True)

# Import our StrandsAgent
from strands_agent import StrandsAgent

# Create a global StrandsAgent instance
strands_agent = StrandsAgent()

# Function to handle queries using our StrandsAgent
async def handle_query(params: FunctionCallParams):
    query = params.arguments.get("query", "")
    if not query:
        await params.result_callback({"result": "No query provided."})
        return
        
    response = strands_agent.query(query)
    if response:
        result = response.group(1) if hasattr(response, "group") else str(response)
        await params.result_callback({
            "result": result,
            "query": query,
            "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
        })
    else:
        await params.result_callback({
            "result": "I couldn't process that request.",
            "query": query,
            "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
        })

# Create a function schema for the Strands agent query
query_function = FunctionSchema(
    name="handle_query",
    description="Delegates queries to a Strands agent that can access location and weather information",
    properties={
        "query": {
            "type": "string",
            "description": "The query to delegate to the Strands agent"
        }
    },
    required=["query"],
)

# Create tools schema
tools = ToolsSchema(standard_tools=[query_function])

async def run_bot(webrtc_connection: SmallWebRTCConnection, _: argparse.Namespace):
    logger.info(f"Starting bot with Strands agent integration")

    # Initialize the SmallWebRTCTransport with the connection
    transport = SmallWebRTCTransport(
        webrtc_connection=webrtc_connection,
        params=TransportParams(
            audio_in_enabled=True,
            audio_in_sample_rate=16000,
            audio_out_enabled=True,
            camera_in_enabled=False,
            vad_analyzer=SileroVADAnalyzer(params=VADParams(stop_secs=0.8)),
        ),
    )
    
    # Initialize services
    llm = AWSNovaSonicLLMService(
        secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        region=os.getenv("AWS_REGION"),  # as of 2025-05-06, us-east-1 is the only supported region
        voice_id="tiffany",  # matthew, tiffany, amy
    )
    
    # Register our handle_query function
    llm.register_function("handle_query", handle_query)
    
    # Specify initial system instruction
    system_instruction = (
        "You are a helpful health assistant designed to provide general health information. "
        "When users ask about location-based information or weather conditions, use the handle_query "
        "function to delegate the request to a Strands agent that has access to location and weather tools. "
        "Keep your responses short, generally two or three sentences. "
        "Remember that you are providing general information only, not medical advice. "
        f"{AWSNovaSonicLLMService.AWAIT_TRIGGER_ASSISTANT_RESPONSE_INSTRUCTION}"
    )
    
    # Set up context and context management
    context = OpenAILLMContext(
        messages=[
            {"role": "system", "content": f"{system_instruction}"},
            {
                "role": "user",
                "content": "Hello, I'm interested in health information.",
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
        logger.info(f"Client connected")
        # Kick off the conversation
        await task.queue_frames([context_aggregator.user().get_context_frame()])
        # Trigger the first assistant response
        await llm.trigger_assistant_response()

    # Handle client disconnection events
    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info(f"Client disconnected")

    @transport.event_handler("on_client_closed")
    async def on_client_closed(transport, client):
        logger.info(f"Client closed connection")
        await task.cancel()
        # Clean up Strands agent resources
        strands_agent.close()
    
    # Run the pipeline
    runner = PipelineRunner(handle_sigint=False)
    await runner.run(task)

if __name__ == "__main__":
    from run import main
    main()
```
