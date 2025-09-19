# Building a voice agent with function calling

In this section, you'll build a voice AI agent using **Amazon Nova Sonic** and **Pipecat**. Follow these steps to create your agent.

## Start creating your voice AI agent

1. In your terminal, create a new file named `agent.py` in your project directory.

```
touch agent.py
```

2. Add the following import statements to the top of your `agent.py` file:

```python
# agent.py
import os
from datetime import datetime

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
from pipecat.services.aws_nova_sonic import AWSNovaSonicLLMService
from pipecat.services.llm_service import FunctionCallParams
from pipecat.transports.base_transport import BaseTransport, TransportParams
from pipecat.transports.daily.transport import DailyParams
```

TKTKTK Check imports with new botfile!

Did you know that Pipecat supports multiple transport options?

In this workshop, you can use [SmallWebRTCTransport](https://docs.pipecat.ai/server/services/transport/small-webrtc) if you're running locally. It is a simplified implementation designed specifically for local development environments, providing the necessary functionality to establish audio connections between your application and the browser without requiring complex infrastructure.

If you're running in the VS Code cloud environment, you can use [DailyTransport](https://docs.pipecat.ai/server/services/transport/daily). Daily provides global, low-latency WebRTC infrastructure that's great for production deployments at scale.


### Understanding the Imported Components

The imports above include several key components from the Pipecat framework that work together to build a voice AI agent:

- **Schema Components**: `FunctionSchema` and `ToolsSchema` define the structure for function calling capabilities
- **Audio Processing**: `SileroVADAnalyzer` and `VADParams` handle voice activity detection
- **Pipeline Components**: `Pipeline`, `PipelineRunner`, and `PipelineTask` manage the flow of data through the agent
- **LLM Integration**: `AWSNovaSonicLLMService` provide the speech-to-speech AI capabilities
- **Transport Layer**: `SmallWebRTCTransport` and related components handle the audio streaming between user and agent

These components form the foundation of our voice agent's architecture, enabling speech processing, AI reasoning, and real-time communication.

3. Add the following code to load environment variables:
    
    ```python
    # Load environment variables
    load_dotenv(override=True)
    ```
    

## Implementing function calling

Now you'll add a function that your agent can call to retrieve weather information:

1. Add the weather function implementation to your `agent.py` file:

```python
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
```

This is a mock implementation for demonstration purposes. In a real application, you would call an actual weather API.

2. Define the schema for your weather function:

```python
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

# Create tools schema
tools = ToolsSchema(standard_tools=[weather_function])
```

## Creating the main bot function

Now you'll implement the main function that will run your voice agent:

1. Add the `run_bot` function to your `agent.py` file:
    
    ```python
    async def run_bot(transport: BaseTransport, runner_args: RunnerArguments):
        logger.info(f"Starting bot")
    ```

    

## Congratulations!

You've successfully laid the foundation for your voice AI agent by:

- Setting up the basic structure of your agent with Pipecat
- Implementing a function calling capability for weather information
- Configuring Voice Activity Detection with Silero VAD
- Creating the initial transport layer for audio communication

This foundation provides the essential components needed for a voice-enabled AI agent that can understand user requests and respond with both voice and actions.

In the next section, you'll continue building your agent by adding the Amazon Nova Sonic service configuration and implementing the complete pipeline to process user interactions. You'll also learn how to run your agent and test its capabilities.

What's Next?

Continue to the next section to complete your voice agent implementation and learn how to run it.
