# Implementing guardrails for off-topic conversations and escalations

A health assistant should be able to gracefully handle off-topic conversations, recognize emergency situations requiring escalation, and redirect users appropriately. In this section, we'll continue extending our voice AI agent to include these capabilities.

## Understanding off-topic handling and escalation

Users may intentionally or unintentionally steer conversations away from health topics, or they may present with urgent situations requiring immediate attention. Effective handling of these scenarios:

- Maintains the agent's focus and purpose
- Sets appropriate boundaries
- Prevents misuse of the health assistant
- Ensures users get the intended value from the service
- Provides critical guidance during emergencies
- Directs users to appropriate resources when needed

Responsible AI and Amazon Nova models

Nova models offer inherent Responsible AI (RAI) that aligns its models with the AWS Acceptable Use Policy, helping mitigate undesired outcomes while ensuring a positive customer experience. For more information on Nova RAI (Responsible AI), please refer to [responsible use documentation](https://docs.aws.amazon.com/nova/latest/userguide/responsible-use.html) .

## Creating the topic management module

First, let's create a module to detect and handle off-topic conversations and emergency situations:

1. Create a file named `topic_management.py` in the same directory as your `agent_retrieval.py` file:

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

## Implementing off-topic and emergency handling

Now, let's create a new agent that builds on our previous knowledge retrieval capabilities and adds off-topic and emergency handling:

1. First, copy your existing agent_retrieval.py file to create a new file named agent_guardrail.py:

```bash
1
cp agent_retrieval.py agent_guardrail.py
```

2. Now, let's modify the new agent_guardrail.py file to add off-topic and emergency handling capabilities.

## Add imports to your new file

Add this new import at the top of your `agent_guardrail.py` file, after your existing imports:

```python
# Import the topic management functions
from topic_management import is_off_topic, get_redirection_response, get_emergency_response
```

## Add the off-topic and emergency handling functions

Add these new functions to your `agent_guardrail.py` file, after your existing `retrieve_health_info` function:

```python
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
```

## Add new function schemas

Add these new function schemas to your `agent_guardrail.py` file, after your existing function schemas:

```python
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
```

## Update your tools schema

Replace your existing tools schema with this expanded version that includes all functions:

```python
# Create tools schema with all functions
tools = ToolsSchema(standard_tools=[weather_function, health_info_function, emergency_function, off_topic_function])
```

## Update the system instruction

Update the system instruction in your `run_bot` function to include guidance on using the new functions:

```python
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
```

## Register the new functions

Add these lines to register the new functions with the LLM service (after registering the existing functions):

```python
llm.register_function("handle_off_topic", handle_off_topic)
llm.register_function("handle_emergency", handle_emergency)
```

## Testing off-topic and emergency handling

To test the off-topic handling and emergency escalation capabilities:

1. Run your new agent:

```bash
1
python agent_guardrail.py -t daily # or -t webrtc
```

2. Open your browser and navigate to [http://localhost:7860](http://localhost:7860/)  to access the voice interface.
    
3. Try various off-topic queries:
    

- "What movies are playing this weekend?"
- "Who will win the next election?"
- "Can you tell me a joke?"
- "What's the stock market doing today?"

4. Try emergency scenarios (these should trigger the emergency response):

- "I'm having chest pain and difficulty breathing"
- "I think I'm having a stroke"
- "I'm feeling suicidal"
- "There's severe bleeding from my arm"

5. Observe how the agent detects off-topic queries and redirects the conversation back to health topics, or how it provides emergency guidance for critical situations.

Function Calling Process

When you interact with the agent, the following happens:

1. The LLM analyzes your input to determine if it's health-related, off-topic, or an emergency
2. For off-topic content, it calls the `handle_off_topic` function to generate an appropriate redirection
3. For emergencies, it calls the `handle_emergency` function to provide critical guidance
4. For health-related questions, it either answers directly or uses the `retrieve_health_info` function
5. The response is converted to speech and played back to you

## Next steps

Now that we've implemented knowledge retrieval capabilities and added guardrails for off-topic and emergency handling, our health assistant is more robust and responsible. In the next module, we'll explore how to enhance the conversational experience with personalization and context management.
