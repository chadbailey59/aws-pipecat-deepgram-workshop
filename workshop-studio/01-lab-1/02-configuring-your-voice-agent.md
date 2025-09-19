# Configuring your voice agent

Let's continue building our voice agent by adding the Amazon Nova Sonic service configuration and other components:

1. Add the system instruction and **Amazon Nova Sonic** service configuration to your `agent.py` file:
    
    ```python
        # Specify initial system instruction
        system_instruction = (
            "You are a friendly assistant. The user and you will engage in a spoken dialog exchanging "
            "the transcripts of a natural real-time conversation. Keep your responses short, generally "
            "two or three sentences for chatty scenarios. "
            f"{AWSNovaSonicLLMService.AWAIT_TRIGGER_ASSISTANT_RESPONSE_INSTRUCTION}"
        )
    
        # Create the AWS Nova Sonic LLM service
        llm = AWSNovaSonicLLMService(
            secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            region=os.getenv("AWS_REGION"),  # as of 2025-05-06, us-east-1 is the only supported region
            voice_id="tiffany",  # matthew, tiffany, amy
        )
    
        # Register function for function calls
        llm.register_function("get_current_weather", fetch_weather_from_api)
    ```
    
2. Set up the conversation context:
    
    ```python
        # Set up context and context management
        context = OpenAILLMContext(
            messages=[
                {"role": "system", "content": f"{system_instruction}"},
                {
                    "role": "user",
                    "content": "Tell me a fun fact!",
                },
            ],
            tools=tools,
        )
        context_aggregator = llm.create_context_aggregator(context)
    ```
    

The `OpenAILLMContext` is a Pipecat context manager that organizes conversation history and manages the state of interactions. Note it does **not** invoke any OpenAI models - it simply provides a standardized format for managing conversation context that works with various LLM services, including Amazon Nova Sonic.

3. Build the pipeline:
    
    ```python
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
    ```
    

Understanding Pipecat Pipelines

The pipeline is a fundamental concept in Pipecat that defines how data flows through your voice agent:

- **Asynchronous Processing**: Pipelines operate asynchronously, allowing real-time processing of audio streams without blocking
- **Component Chain**: Each component in the pipeline processes frames of data and passes them to the next component
- **Simple Example**: This example shows a basic pipeline with minimal components:
    - `transport.input()`: Receives audio from the user
    - `context_aggregator.user()`: Adds user messages to the conversation context
    - `llm`: Processes the input and generates responses using Amazon Nova Sonic
    - `transport.output()`: Sends audio responses back to the user
    - `context_aggregator.assistant()`: Adds assistant responses to the conversation context

In production environments, pipelines can include additional components such as:

- Pre-processing filters for noise reduction
- Multiple LLM services for different tasks
- Fallback handlers for error scenarios

The pipeline architecture makes Pipecat highly extensible, allowing you to add, remove, or replace components to customize your voice agent's behavior without changing the core application logic.

4. Add event handlers for client connections:
    
    ```python
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
    ```
    

Understanding Event Handlers

Event handlers are crucial for managing the lifecycle of your voice agent's connections:

- The `@transport.event_handler` decorator registers functions to respond to specific events
- `on_client_connected` is triggered when a new client establishes a connection
    - It initializes the conversation context and triggers the first assistant response
    - This creates a seamless experience where the agent speaks first without waiting for user input
- `on_client_disconnected` and `on_client_closed` handle cleanup when connections end
    - Proper cleanup prevents resource leaks and ensures your agent can handle multiple sessions
    - `task.cancel()` stops the pipeline processing for that specific client

These event handlers create a responsive system that manages the full lifecycle of each conversation from initiation to completion.

5. Run the pipeline:
    
    ```python
        # Run the pipeline
        runner = PipelineRunner(handle_sigint=False)
        await runner.run(task)
    ```
    

Understanding the Pipeline Execution

The pipeline execution is a critical part of your voice agent:

- `PipelineRunner` creates an environment for running your pipeline tasks
- `handle_sigint=False` tells the runner not to handle interrupt signals (Ctrl+C) itself, allowing your main application to handle them
- `await runner.run(task)` starts the pipeline and processes audio frames asynchronously
- The pipeline will continue running until the task is canceled (which happens when a client disconnects)

This asynchronous execution model allows your voice agent to process audio input, generate responses, and handle function calls all in real-time while maintaining a responsive user experience.

6. Add the `bot()` function and main entry point to your `agent.py` file:
    
    ```python
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
    ```
    

### Running your bot.

To run your bot, you need two things:

1. A way to trigger and manage a new bot session
2. A transport for sending and receiving audio (and video) between the bot and the user

The Pipecat framework includes a `runner` module that handles the first part for you. It follows the same pattern as [Pipecat Cloud](https://docs.pipecat.ai/deployment/pipecat-cloud/introduction): When you run your botfile, the runner preloads your code. When you're ready to start a session, the runner calls the `bot()` function to set up a transport and start the session.

This `bot()` function includes configuration for both `SmallWebRTCTransport` and `DailyTransport`. The `if __name__ == "__main__":` condition is a Python convention that manages what happens when you run this file directly from the terminal. The `main()` function from the runner module parses some predefined command line arguments, so you can choose which transport you want to use when you run the bot. We'll explore runner options in the next section.


TKTKTK Should this move somewhere else?

### Understanding VAD and Silero

The **Voice Activity Detection (VAD)** analyzer helps detect when the user has finished speaking, with a silence threshold of 0.8 seconds.
    
- _Voice Activity Detection (VAD)_ is a technology used to detect the presence or absence of human speech in audio. In voice AI applications, VAD is crucial for determining when a user has started or stopped speaking, allowing the system to process speech input at appropriate times.
    
- _Silero VAD_ is a specific implementation of voice activity detection that uses deep learning models to accurately detect speech segments in audio streams. It's particularly effective at distinguishing between speech and background noise, making it ideal for real-time voice applications. The `stop_secs` parameter (set to 0.8 seconds in our code) defines how long the system should wait after detecting silence before considering that the user has finished speaking.
    

## Next steps

Now that we've set up the core components of our voice agent, we need to create the run script that will handle the WebRTC server and client connections. Continue to the next section to create this script and learn how to run your voice agent.
