# Agent with knowledge retrieval

## retrieval.py

```python
import os
import json
import requests
from bs4 import BeautifulSoup
from googlesearch import search

def search_health_info(query):
    """
    Search for health information using Google Search
    """
    # Add "health" to the query to focus on health-related results
    search_query = f"{query} health information"
    
    # Perform the search - get top 5 results
    search_results = []
    try:
        for url in search(search_query, num_results=5):
            search_results.append(url)
    except Exception as e:
        print(f"Search error: {e}")
        return []
    
    # Format the results
    formatted_results = []
    for url in search_results:
        try:
            # Get the page content
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                # Parse the HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract title
                title = soup.title.string if soup.title else url
                
                # Extract a snippet (first paragraph or meta description)
                snippet = ""
                meta_desc = soup.find('meta', attrs={'name': 'description'})
                if meta_desc and meta_desc.get('content'):
                    snippet = meta_desc.get('content')
                else:
                    first_p = soup.find('p')
                    if first_p:
                        snippet = first_p.get_text()[:200] + "..."
                
                # Extract source domain
                source = url.split('//')[1].split('/')[0]
                
                formatted_results.append({
                    "title": title,
                    "snippet": snippet,
                    "link": url,
                    "source": source
                })
        except Exception as e:
            print(f"Error processing {url}: {e}")
    
    return formatted_results

def summarize_search_results(results, query):
    """
    Create a summary of search results that can be used by the agent
    """
    if not results:
        return f"I couldn't find any information about '{query}'."
    
    summary = f"Here's what I found about '{query}':\n\n"
    
    for i, result in enumerate(results[:3], 1):  # Limit to top 3 results
        summary += f"{i}. {result['title']}\n"
        summary += f"   {result['snippet']}\n"
        summary += f"   Source: {result['source']}\n\n"
    
    summary += "This information is from web searches and should not replace professional medical advice."
    
    return summary
```

## agent_retrieval.py

```python
# agent_retrieval.py
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

from retrieval import search_health_info, summarize_search_results

# Load environment variables
load_dotenv(override=True)

async def fetch_weather_from_api(params: FunctionCallParams):
    temperature = 75 if params.arguments["format"] == "fahrenheit" else 24
    await params.result_callback(
        {
            "conditions": "nice",
            "temperature": temperature,
            "format": params.arguments["format"],
            "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
        }
    )

async def retrieve_health_info(params: FunctionCallParams):
    query = params.arguments.get("query", "")
    if not query:
        await params.result_callback({"result": "No query provided."})
        return
    
    # Search for health information
    search_results = search_health_info(query)
    
    # Summarize the results
    summary = summarize_search_results(search_results, query)
    
    # Return the results
    await params.result_callback({
        "result": summary,
        "query": query,
        "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
    })

# Define the weather function schema
weather_function = FunctionSchema(
    name="get_current_weather",
    description="Get the current weather",
    properties={
        "location": {
            "type": "string",
            "description": "The city and state, e.g. San Francisco, CA",
        },
        "format": {
            "type": "string",
            "enum": ["celsius", "fahrenheit"],
            "description": "The temperature unit to use. Infer this from the users location.",
        },
    },
    required=["location", "format"],
)

# Create a function schema for health information retrieval
health_info_function = FunctionSchema(
    name="retrieve_health_info",
    description="Retrieve health information about a specific topic or question",
    properties={
        "query": {
            "type": "string",
            "description": "The health-related query or question",
        },
    },
    required=["query"],
)

# Create tools schema with both functions
tools = ToolsSchema(standard_tools=[weather_function, health_info_function])

async def run_bot(webrtc_connection: SmallWebRTCConnection, _: argparse.Namespace):
    logger.info(f"Starting bot")

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

    # Specify initial system instruction with health assistant capabilities
    system_instruction = (
        "You are a helpful health assistant designed to provide general health information. "
        "You can answer health-related questions and provide information on symptoms, treatments, "
        "and preventive measures. For specific medical questions, you can search for information "
        "using the retrieve_health_info function. "
        "Keep your responses short, generally two or three sentences for chatty scenarios. "
        "Always attribute information to sources when using search results. "
        "Remember that you are providing general information only, not medical advice. "
        f"{AWSNovaSonicLLMService.AWAIT_TRIGGER_ASSISTANT_RESPONSE_INSTRUCTION}"
    )

    # Create the AWS Nova Sonic LLM service
    llm = AWSNovaSonicLLMService(
        secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        region=os.getenv("AWS_REGION"),  # as of 2025-05-06, us-east-1 is the only supported region
        voice_id="tiffany",  # matthew, tiffany, amy
    )

    # Register functions for function calls
    llm.register_function("get_current_weather", fetch_weather_from_api)
    llm.register_function("retrieve_health_info", retrieve_health_info)

    # Set up context and context management
    context = OpenAILLMContext(
        messages=[
            {"role": "system", "content": f"{system_instruction}"},
            {
                "role": "user",
                "content": "Hello, I'd like to ask some health questions.",
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

    # Run the pipeline
    runner = PipelineRunner(handle_sigint=False)
    await runner.run(task)

if __name__ == "__main__":
    from run import main
    main()
```
