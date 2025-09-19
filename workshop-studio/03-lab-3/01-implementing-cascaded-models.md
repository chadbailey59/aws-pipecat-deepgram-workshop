# Implementing the cascaded models approach

While Amazon Nova Sonic provides a direct speech-to-speech approach, there are scenarios where a cascaded models approach might be more appropriate. In this section, we'll implement this alternative approach.

## What is the cascaded models approach?

The cascaded models approach breaks down voice AI processing into separate components:

1. **Speech-to-Text (STT)**: Converts spoken language into written text
2. **Large Language Model (LLM)**: Processes the text and generates a response
3. **Text-to-Speech (TTS)**: Converts the text response back into spoken language

This approach offers more flexibility and control over each step of the process.

![Reference Architecture - Cascaded Models](https://d2908q01vomqb2.cloudfront.net/f1f836cb4ea6efb2a0b1b99f41ad8b103eff4b59/2025/05/09/Reference-Architecture-Pipecat.png)

## Implementing the cascaded approach

1. First, let's install the required dependency:

```bash
1
pip install "pipecat-ai[aws]"==0.0.67
```

Let's create a cascaded version of our voice AI agent:

2. Create a file named `agent_cascaded.py`:

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
from pipecat.services.aws.stt import AWSTranscribeSTTService
from pipecat.services.aws.tts import AWSPollyTTSService
from pipecat.services.aws.llm import AWSBedrockLLMService
from pipecat.transports.base_transport import TransportParams
from pipecat.transports.network.small_webrtc import SmallWebRTCTransport
from pipecat.transports.network.webrtc_connection import SmallWebRTCConnection

# Load environment variables
load_dotenv()

async def run_bot(webrtc_connection, args):
    logger.info("Starting cascaded bot")
    
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
    
    # Initialize speech-to-text service
    stt = AWSTranscribeSTTService(
        api_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        region=os.getenv("AWS_REGION")
    )

    # Initialize text-to-speech service
    tts = AWSPollyTTSService(
        api_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        region=os.getenv("AWS_REGION"),
        voice_id="Joanna",
        params=AWSPollyTTSService.InputParams(
            engine="generative",
            language="en-AU",
            rate="1.1"
        )
    )

    # Initialize LLM service
    llm = AWSBedrockLLMService(
        aws_access_key=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        aws_region=os.getenv("AWS_REGION"),
        model="us.anthropic.claude-3-5-haiku-20241022-v1:0",
        params=AWSBedrockLLMService.InputParams(
            temperature=0.3,
            latency="optimized",
            additional_model_request_fields={}
        )
    )
    
    # Specify system instruction
    system_instruction = (
        "You are a helpful health assistant designed to provide general health information. "
        "You can answer health-related questions and provide information on symptoms, treatments, "
        "and preventive measures. "
    )
    
    # Create the context
    context = OpenAILLMContext(
        messages=[
            {"role": "system", "content": system_instruction},
            {
                "role": "user",
                "content": "Hello, I'd like to ask some health questions.",
            },
        ],
        tools=[],
    )
    
    # Create the context aggregator
    context_aggregator = llm.create_context_aggregator(context)
    
    # Build the pipeline
    pipeline = Pipeline(
        [
            transport.input(),
            stt,
            context_aggregator.user(),
            llm,
            tts,
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

## Running your cascaded agent

Now that we've created our cascaded agent, let's run it using the run.py script we created earlier:

1. Run your cascaded agent with the following command:

```bash
1
python run.py cascaded_agent.py
```

2. You should see output indicating that the WebRTC server has started and is listening for connections.
    
3. Open your browser and navigate to [http://localhost:7860](http://localhost:7860/)  to access the voice interface.
    

## Next steps

Now that we've implemented the cascaded approach, let's compare the approaches.
