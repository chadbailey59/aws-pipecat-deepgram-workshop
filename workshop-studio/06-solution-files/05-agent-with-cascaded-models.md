# Agent with cascaded models

## agent_cascaded.py

```python
import argparse
import os
from datetime import datetime

from dotenv import load_dotenv
from loguru import logger

from pipecat.adapters.schemas.function_schema import FunctionSchema
from pipecat.adapters.schemas.tools_schema import ToolsSchema
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.services.aws.stt import AWSTranscribeSTTService
from pipecat.services.aws.tts import AWSPollyTTSService
from pipecat.services.aws.llm import AWSBedrockLLMService
from pipecat.transports.base_transport import TransportParams
from pipecat.transports.network.small_webrtc import SmallWebRTCTransport
from pipecat.transports.smallwebrtc.connection import SmallWebRTCConnection

# Load environment variables
load_dotenv()

async def run_bot(transport: BaseTransport, runner_args: RunnerArguments):

    logger.info("Starting cascaded bot")
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
        await task.queue_frames([LLMRunFrame()])
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
