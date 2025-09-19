# Agent with guardrails

## topic_management.py

```python
def is_off_topic(text):
    """
    Detect if the user's input is off-topic for a health assistant
    """
    # Health-related keywords (simplified list)
    health_keywords = [
        "health", "medical", "doctor", "hospital", "symptom", "treatment",
        "medicine", "disease", "condition", "pain", "diet", "exercise",
        "wellness", "therapy", "diagnosis", "prescription", "vaccine",
        "injury", "recovery", "allergy", "nutrition", "mental health",
        "sleep", "stress", "anxiety", "depression", "blood pressure",
        "heart", "lung", "brain", "stomach", "skin", "bone", "muscle"
    ]
    
    # Explicitly off-topic categories and examples
    off_topic_categories = {
        "entertainment": ["movie", "tv show", "music", "concert", "celebrity", "actor", "singer"],
        "politics": ["politics", "election", "president", "government", "democrat", "republican"],
        "finance": ["stock", "investment", "bitcoin", "crypto", "money", "loan", "bank"],
        "technology": ["computer", "smartphone", "app", "software", "hardware", "coding"],
        "sports": ["football", "basketball", "baseball", "soccer", "tennis", "athlete", "team"],
        "inappropriate": ["joke", "funny", "date", "dating", "relationship", "sex", "illegal"]
    }
    
    # Emergency keywords that should trigger escalation
    emergency_keywords = [
        "emergency", "911", "help me", "chest pain", "heart attack", "stroke", 
        "can't breathe", "difficulty breathing", "severe bleeding", "unconscious",
        "suicide", "kill myself", "overdose", "poisoning", "severe injury",
        "head injury", "seizure", "allergic reaction", "anaphylaxis"
    ]
    
    text_lower = text.lower()
    
    # First check for emergency keywords - these take priority
    for keyword in emergency_keywords:
        if keyword in text_lower:
            return False, None, True  # Not off-topic, but emergency
    
    # Check if any health keyword is in the text
    for keyword in health_keywords:
        if keyword in text_lower:
            return False, None, False  # Not off-topic, not emergency
    
    # Check if any off-topic keyword is in the text
    for category, keywords in off_topic_categories.items():
        for keyword in keywords:
            if keyword in text_lower:
                return True, category, False  # Off-topic, not emergency
    
    # If no health keywords and no explicit off-topic keywords, analyze further
    # This is a simplified approach - in a real application, you might use more sophisticated NLP
    question_starters = ["what", "how", "why", "can", "could", "would", "should", "is", "are", "do"]
    
    # If it's a question but doesn't contain health keywords, it's likely off-topic
    for starter in question_starters:
        if text_lower.startswith(starter):
            return True, "general", False  # Off-topic, not emergency
    
    # Default to not off-topic if we can't determine
    return False, None, False

def get_redirection_response(category=None):
    """
    Generate an appropriate redirection response based on the off-topic category
    """
    general_redirection = (
        "I'm a health assistant designed to help with health-related questions. "
        "Is there something specific about your health or wellness that I can help you with?"
    )
    
    # Specific redirections for certain categories
    specific_redirections = {
        "entertainment": (
            "I'm not able to discuss entertainment topics as I'm designed to assist with health-related questions. "
            "Is there something about your health or wellness that I can help you with instead?"
        ),
        "politics": (
            "I'm not able to discuss political topics as I'm designed to assist with health-related questions. "
            "Is there something about your health or wellness that I can help you with instead?"
        ),
        "finance": (
            "I'm not able to provide financial advice as I'm designed to assist with health-related questions. "
            "Is there something about your health or wellness that I can help you with instead?"
        ),
        "technology": (
            "While technology can certainly impact health, I'm primarily designed to assist with health-related questions. "
            "Is there a specific health concern or wellness topic I can help you with?"
        ),
        "sports": (
            "While physical activity is important for health, I'm not able to discuss sports topics in detail. "
            "I'd be happy to discuss exercise and its health benefits if you're interested."
        ),
        "inappropriate": (
            "I'm designed to provide health information and support. "
            "Please keep our conversation focused on health-related topics that I can assist you with."
        )
    }
    
    if category and category in specific_redirections:
        return specific_redirections[category]
    
    return general_redirection

def get_emergency_response(text):
    """
    Generate an appropriate emergency response based on the detected situation
    """
    # Default emergency response
    general_emergency = (
        "This sounds like a medical emergency. Please call emergency services (911 in the US) immediately. "
        "Do not wait for symptoms to worsen."
    )
    
    # Specific emergency responses
    text_lower = text.lower()
    
    if any(keyword in text_lower for keyword in ["chest pain", "heart attack", "cardiac"]):
        return (
            "You may be experiencing a cardiac emergency. Call 911 or your local emergency number immediately. "
            "If available and you're not allergic, consider taking aspirin while waiting for help. "
            "Try to remain calm and seated or lying down."
        )
    
    if any(keyword in text_lower for keyword in ["stroke", "face drooping", "arm weakness", "speech difficulty"]):
        return (
            "You may be experiencing stroke symptoms. Call 911 immediately. "
            "Note the time when symptoms started. Do not eat, drink, or take medication. "
            "Lie down with your head slightly elevated and wait for emergency services."
        )
    
    if any(keyword in text_lower for keyword in ["breathing", "breathe", "suffocating", "choking"]):
        return (
            "Difficulty breathing is a serious emergency. Call 911 immediately. "
            "Try to remain calm, loosen any tight clothing, and sit upright if possible. "
            "If you have prescribed rescue medications like an inhaler, use them as directed."
        )
    
    if any(keyword in text_lower for keyword in ["suicide", "kill myself", "end my life", "don't want to live"]):
        return (
            "I'm concerned about what you're saying. Please call the National Suicide Prevention Lifeline at 988 or 1-800-273-8255 immediately. "
            "They have trained counselors available 24/7. You can also text HOME to 741741 to reach the Crisis Text Line. "
            "Please reach out for help - you're not alone."
        )
    
    if any(keyword in text_lower for keyword in ["bleeding", "blood", "hemorrhage"]):
        return (
            "For severe bleeding, call 911 immediately. Apply direct pressure to the wound with a clean cloth or bandage. "
            "If possible, elevate the injured area above the heart. Do not remove the cloth if it becomes soaked - add more on top."
        )
    
    return general_emergency
```

## agent_guardrail.py

```python
# agent_guardrail.py
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
from topic_management import is_off_topic, get_redirection_response, get_emergency_response

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

# New function for handling off-topic conversations
async def handle_off_topic(params: FunctionCallParams):
    """
    Handle off-topic conversations and redirect to health topics
    """
    user_input = params.arguments.get("user_input", "")
    if not user_input:
        await params.result_callback({"result": "No user input provided."})
        return
    
    # Check if this is off-topic or an emergency
    off_topic, category, is_emergency = is_off_topic(user_input)
    
    # If it's an emergency, handle it with priority
    if is_emergency:
        emergency_response = get_emergency_response(user_input)
        await params.result_callback({
            "is_emergency": True,
            "response": emergency_response,
        })
        return
    
    if off_topic:
        # Get appropriate redirection response
        response = get_redirection_response(category)
        
        # Return the redirection response
        await params.result_callback({
            "is_off_topic": True,
            "response": response,
            "category": category if category else "general",
        })
    else:
        # Not off-topic
        await params.result_callback({
            "is_off_topic": False,
            "response": "This appears to be a health-related topic.",
        })

# New function for handling emergency situations
async def handle_emergency(params: FunctionCallParams):
    """
    Handle emergency situations with appropriate guidance
    """
    user_input = params.arguments.get("user_input", "")
    if not user_input:
        await params.result_callback({"result": "No user input provided."})
        return
    
    # Generate emergency response based on the input
    emergency_response = get_emergency_response(user_input)
    
    # Return the emergency response
    await params.result_callback({
        "is_emergency": True,
        "response": emergency_response,
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

# Create a function schema for off-topic detection
off_topic_function = FunctionSchema(
    name="handle_off_topic",
    description="Detect and respond to off-topic conversations",
    properties={
        "user_input": {
            "type": "string",
            "description": "The user's input to check for off-topic content",
        },
    },
    required=["user_input"],
)

# Create a function schema for emergency handling
emergency_function = FunctionSchema(
    name="handle_emergency",
    description="Handle emergency situations with appropriate guidance",
    properties={
        "user_input": {
            "type": "string",
            "description": "The user's input to check for emergency situations",
        },
    },
    required=["user_input"],
)

# Create tools schema with all functions
tools = ToolsSchema(standard_tools=[weather_function, health_info_function, emergency_function, off_topic_function])

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

    # Specify initial system instruction with health assistant capabilities and guardrails
    system_instruction = (
        "You are a helpful health assistant designed to provide general health information. "
        "You can answer health-related questions and provide information on symptoms, treatments, "
        "and preventive measures. For specific medical questions, you can search for information "
        "using the retrieve_health_info function. "
        "IMPORTANT: If a user mentions any symptoms or situations that could be a medical emergency "
        "(like chest pain, difficulty breathing, severe bleeding, stroke symptoms, or suicidal thoughts), "
        "use the handle_emergency function immediately to provide appropriate guidance. "
        "If a user asks about topics unrelated to health (like entertainment, politics, or technology), "
        "use the handle_off_topic function to politely redirect the conversation back to health topics. "
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
    llm.register_function("handle_off_topic", handle_off_topic)
    llm.register_function("handle_emergency", handle_emergency)

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
