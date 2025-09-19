# Delegating tool selection with Strands agent

In this section, we'll explore how to implement a delegated architecture using the [Strands](https://aws.amazon.com/blogs/opensource/introducing-strands-agents-an-open-source-ai-agents-sdk/)  framework. This approach allows you to offload tool selection and invocation to an intelligent agent that uses foundation models to make decisions.

## What is the Strands SDK?

Strands is an open source AI agents framework from AWS designed to simplify the creation and orchestration of AI agents. It provides a unified interface for defining tools, managing agent state, and coordinating complex workflows across multiple AI services. Key features include:

- **Tool definition**: Easily define tools using Python decorators
- **Tool orchestration**: Automatically handle the selection and execution of tools
- **MCP integration**: Seamless integration with Model Context Protocol servers
- **Model flexibility**: Support for various LLMs including Amazon Bedrock models
- **Reasoning capabilities**: Built-in support for multi-step reasoning

![Strands Architecture](https://static.us-east-1.prod.workshops.aws/public/80e2f4fb-7fe5-4c2c-88fb-fb5de05b1533/static/images/strands-architecture.jpg)

### Strands compared to other frameworks

While many open source AI agent frameworks exist, Strands offers several distinct advantages:

- **Lightweight design**: Strands provides a minimalist API with fewer abstractions, making it easier to learn and use
- **Model-driven agents**: Strands emphasizes letting the model drive agent behavior rather than complex state machines
- **First-class AWS integration**: Native support for Amazon Bedrock models and AWS services
- **Built-in agentic patterns**: Includes ready-to-use patterns for common agent workflows
- **MCP compatibility**: Seamless integration with the Model Context Protocol ecosystem

Strands is particularly well-suited for developers who want to quickly build capable agents without managing complex state transitions or learning extensive framework-specific concepts.

For more information, visit the [Strands GitHub repository](https://github.com/strands-agents/sdk-python)  and [official documentation](https://strandsagents.com/) . The documentation includes several multi-agent patterns including Agents as Tools, Swarm, Graph and Workflow patterns that enable complex agent orchestration scenarios.

## Prerequisite: Enable Amazon Nova Lite model

Before proceeding, ensure you have enabled the Amazon Nova Lite model in your AWS account:

1. Navigate to the [Amazon Bedrock](https://console.aws.amazon.com/bedrock/home?#/modelaccess)  console
2. Go to **Model access** in the left navigation panel
3. Click **Modify model access** and find **Amazon Nova Lite** in the model list
4. Click **Next** and then **Submit**
5. Verify **Access Granted** in Amazon Nova Lite

## Understanding delegated architecture

In a delegated architecture, your application hands off complex tasks to an agent that can:

- Understand natural language requests
- Select appropriate tools based on the request
- Execute those tools with proper parameters
- Return meaningful responses

This differs from the direct integration approach we saw earlier, where our application explicitly decides which tools to use.

## Setting up your environment

1. First, install the required dependencies for Strands:

```bash
1
pip install strands-agents strands-agents-tools
```

2. Second, install the required dependencies for the [AWS Location Service MCP Server](https://awslabs.github.io/mcp/servers/aws-location-mcp-server/) . You will be installing this MCP server locally.

```bash
1
pip install uv
```

Deploying MCP Servers in Production

While this workshop uses locally running MCP servers, for production environments you can deploy on AWS Lambda for serverless operation with automatic scaling and pay-per-use pricing, Amazon ECS/Fargate for container-based deployment, or other AWS compute services. For an example of Lambda deployment, see the [AWS Lambda MCP Server repository](https://github.com/awslabs/run-model-context-protocol-servers-with-aws-lambda) . For comprehensive architecture patterns and implementation guidance, refer to [AWS Solutions Guidance for Deploying Model Context Protocol Servers](https://aws.amazon.com/solutions/guidance/deploying-model-context-protocol-servers-on-aws/) .

## Implementing the Strands agent

1. Let's create a new file called `strands_agent.py` in your project directory with the following `StrandsAgent` class that integrates a weather tool and [AWS Location Service MCP Server](https://awslabs.github.io/mcp/servers/aws-location-mcp-server/)  as tools:

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

    def __init__(self):1
        # Launch AWS Location Service MCP Server and create a client object
        env = {"FASTMCP_LOG_LEVEL": "ERROR"}
        env['AWS_SECRET_ACCESS_KEY']=os.getenv("AWS_SECRET_ACCESS_KEY")
        env['AWS_ACCESS_KEY_ID']=access_key_id=os.getenv("AWS_ACCESS_KEY_ID")
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

2. Verify that you have AWS credentials setup in `.env` to be able to access AWS Location Service. This should have been setup previously. See [Configure AWS Credentials](https://catalog.workshops.aws/voice-ai-agents/en-US/getting-started/development-environment#configure-aws-credentials).

### Two approaches to tool invocation

Our StrandsAgent class provides two different methods for handling requests. In this workshop, you will use delegated query handling.

#### Delegated query handling

The `query()` method sends the input to the agent, allowing it to handle tool selection and invocation:

```python
agent = StrandsAgent()
response = agent.query("What's the weather like in Seattle?")
print(response)
agent.close()
```

This approach delegates tool selection logic to the agent and performs reasoning using the LLM.

#### Alternative Option: Direct tool calling

Alternatively, the `call_tool()` method invokes a specific tool directly:

```python
agent = StrandsAgent()
response = agent.call_tool("search_places", "largest zoo in Seattle")
print(response)
agent.close()
```

This approach bypasses the reasoning step and offers lower query latency.

## Integrating with Pipecat

Now, let's see how we can integrate our Strands agent with Pipecat.

1. Create a new file called `agent_delegated.py`:

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
```

2. Observe how you are now implementing the "agent as tool" as pattern with `handle_query` handled by the Strands agent.

## Running your delegated agent

Now that we've created our delegated agent, let's run it using the run.py script we created earlier:

1. Run your delegated agent with the following command:
    
    ```bash
    1
    python run.py agent_delegated.py
    ```
    
2. You should see output indicating that the WebRTC server has started and is listening for connections.
    
3. Open your browser and navigate to [http://localhost:7860](http://localhost:7860/)  to access the voice interface.
    
4. The agent will automatically start the conversation and you can begin interacting with it.
    

## Testing complex multi-step queries

Try asking complex, multi-step questions that demonstrate Strands' ability to orchestrate multiple tool calls:

- "What's the current weather at the Space Needle in Seattle?"
    
- "Compare the weather conditions between the Seattle Zoo and the Seattle Aquarium, and tell me which would be better to visit today."
    

## Comparing direct and delegated approaches

Let's compare the two approaches:

|Feature|Direct Integration (MCP)|Delegated Architecture (Strands)|
|---|---|---|
|Tool Selection|Application decides|Agent decides|
|Reasoning|Minimal|Extensive|
|Best for|Known use cases|Open-ended queries|

## Congratulations!

You've successfully implemented a delegated architecture using the Strands agents framework, enabling your voice AI agent to handle complex, multi-step queries by orchestrating multiple tool calls. This powerful approach allows your health assistant to provide rich, contextual responses that combine location data, weather information, and routing capabilities, significantly enhancing the user experience with more intelligent and comprehensive interactions.
