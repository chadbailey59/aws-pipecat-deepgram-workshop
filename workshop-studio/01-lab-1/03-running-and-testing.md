# Running and testing your voice agent

## Running your voice agent

Now that you've built your voice agent and created the run script, it's time to run it:

1. Run your voice agent with the following command:
    
    ```bash
    python run.py agent.py
    ```
    

Initial Loading Time

It may take up to 2 minutes for the agent to first load up. This is normal as the system initializes all the necessary components and establishes connections to the required services.

2. You should see output indicating that the WebRTC server has started and is listening for connections.
    
    The server will start on port 7860 by default. Once it's running, you can access the voice agent interface at [http://localhost:7860](http://localhost:7860/) .
    
    You can specify a different port using the `--port` option:
    
    ```bash
    python run.py agent.py --port 9090
    ```
    
3. When a client connects, your agent will automatically start the conversation with "Tell me a fun fact!" and respond accordingly.
    

## Testing your voice agent

Now that your voice agent is running, follow these steps to test it and explore ways to improve it.

### Testing the weather function

To test the weather function, try asking the following questions:

- "What's the weather like in Seattle?"
- "How's the weather in New York today?"
- "Tell me the current temperature in London"
- "Is it raining in Tokyo right now?"

Your agent should respond with weather information for the requested location, demonstrating its ability to make function calls to external APIs.

### Testing conversation capabilities

Test your agent's conversational abilities with these prompts:

- "Tell me a joke"
- "What can you help me with?"
- "Tell me about yourself"
- "What's your favorite color?"

These prompts will help you evaluate how well your agent handles general conversation and maintains context.

### Testing interruptions

One of the key features of your voice agent is its ability to handle interruptions. Try these scenarios:

1. Start asking a long question, then interrupt yourself with a different question
2. Ask the agent to tell you a long story, then interrupt it with a new question
3. Ask a question, then quickly ask another before the agent finishes responding

The agent should gracefully handle these interruptions, stopping its current response and addressing your new input.

## Improving your voice agent

Here are some ways you can enhance your voice agent:

### Customize the system instruction

The system instruction defines your agent's personality and behavior. Try modifying the system instruction in your `agent.py` file to create different agent personas:

```python
# Example of a more specialized system instruction
system_instruction = (
    "You are a friendly weather expert assistant. The user and you will engage in a spoken dialog "
    "exchanging the transcripts of a natural real-time conversation. Keep your responses short, "
    "generally two or three sentences for chatty scenarios. When discussing weather, provide "
    "helpful context about how the weather might affect daily activities. "
    f"{AWSNovaSonicLLMService.AWAIT_TRIGGER_ASSISTANT_RESPONSE_INSTRUCTION}"
)
```

### Add more functions

You can expand your agent's capabilities by adding more functions. For example, you could add functions to:

- Get news headlines
- Provide restaurant recommendations
- Set reminders or timers
- Perform calculations

For each new function, follow the same pattern you used for the weather function:

1. Define the function
2. Add it to the tools list
3. Register it with the LLM service

### Try different voices

Amazon Nova Sonic offers multiple voice options. Try changing the `voice_id` parameter in your LLM service configuration:

```python
llm = AWSNovaSonicLLMService(
    secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    region=os.getenv("AWS_REGION"),
    voice_id="matthew",  # Try different voices: matthew, tiffany, amy
)
```

### Adjust response length

You can influence the length of your agent's responses by modifying the system instruction. For shorter responses, emphasize brevity:

```python
"Keep your responses very brief, generally one short sentence for most questions."
```

For more detailed responses, you can adjust accordingly:

```python
"Provide detailed, informative responses with examples when appropriate."
```

Remember that longer responses may be more likely to be interrupted in a voice conversation, so finding the right balance is important.
