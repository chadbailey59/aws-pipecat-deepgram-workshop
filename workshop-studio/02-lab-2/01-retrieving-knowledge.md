# Retrieving knowledge

To make our voice AI agent more informative and useful, we'll implement knowledge retrieval capabilities. This allows our agent to access external information sources and provide more accurate, up-to-date responses. In this module, we'll implement a simple web retrieval example as one approach to knowledge retrieval.

## Understanding knowledge retrieval

Knowledge retrieval enables AI agents to:

1. Access information beyond their training data
2. Provide current and accurate information
3. Cite sources for better transparency and trust
4. Answer specific questions with authoritative information

Knowledge retrieval approaches

There are many approaches to knowledge retrieval, including:

- Web search and scraping (what we'll implement today)
- Vector databases for semantic search
- API integrations with knowledge bases
- Document retrieval from enterprise systems
- Structured data access (databases, knowledge graphs)

## Setting up web retrieval dependencies

For our simple example, we'll implement web retrieval using googlesearch-python. This allows our health assistant to search for information online without requiring paid API services.

First, let's install the necessary packages:

```bash
pip install googlesearch-python requests beautifulsoup4
```

The googlesearch-python package provides a simple way to perform Google searches programmatically, and we'll use BeautifulSoup to extract information from the search results.

## Creating a knowledge retrieval tool

Now, let's create a retrieval tool that our agent can use to search for health information:

1. Create a file named `retrieval.py`:

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

Note on Web Scraping

This implementation is for educational purposes only. In a production environment, you should respect robots.txt files, implement proper rate limiting, and consider using official APIs when available.

## Creating a new agent with knowledge retrieval

Instead of modifying our existing agent, let's create a new version with knowledge retrieval capabilities:

1. First, copy your existing agent.py file to create a new file named agent_retrieval.py:

```bash
1
cp agent.py agent_retrieval.py
```

2. Now, let's modify the new agent_retrieval.py file to add knowledge retrieval capabilities.

## Add imports to your new file

Add these new imports at the top of your `agent_retrieval.py` file, after your existing imports:

```python
1
from retrieval import search_health_info, summarize_search_results
```

## Add the health information retrieval function

Add this new function to your `agent_retrieval.py` file, after your existing `fetch_weather_from_api` function:

```python
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
```

## Update your function schemas

Replace your existing `weather_function` and `tools` definitions in `agent_retrieval.py` with this expanded version that includes both functions:

```python
# Define the weather function schema (keep your existing weather function)
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
```

## Update the run_bot function

Now, modify the `run_bot` function in your `agent_retrieval.py` file with these changes:

1. Update the system instruction to reflect the health assistant capabilities:

```python
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
```

2. Register the new function with the LLM service (add this line after registering the weather function):

```python
# Register functions for function calls
llm.register_function("get_current_weather", fetch_weather_from_api)
llm.register_function("retrieve_health_info", retrieve_health_info)  # Add this line
```

3. Update the initial user message in the context:

```python
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
```

## Testing knowledge retrieval

To test the knowledge retrieval capability:

1. Run your new agent with the following command:

```bash
python agent_retrieval.py -t daily # or -t webrtc
```

2. Open your browser and navigate to [http://localhost:7860](http://localhost:7860/)  to access the voice interface.
    
3. Ask health-related questions that might benefit from knowledge retrieval:
    

- "What are the symptoms of the flu?"
- "How can I prevent heart disease?"
- "What causes migraines?"

4. Observe how the agent uses retrieved information to provide more informative responses.

Function Calling Process

When you ask a health-related question, the following happens:

1. The LLM determines that it needs more information to answer accurately
2. It calls the `retrieve_health_info` function with your query
3. The function performs a web search and summarizes the results
4. The LLM receives the search results and uses them to formulate a response
5. The response is converted to speech and played back to you

## Next steps

Now that we've implemented knowledge retrieval capabilities, let's move on to creating emergency detection and redirect functionality.

Did you know?

[Amazon Nova Sonic is integrated with Amazon Bedrock Knowledge Bases](https://aws.amazon.com/blogs/aws/introducing-amazon-nova-sonic-human-like-voice-conversations-for-generative-ai-applications/) . In production, Knowledge Bases on Amazon Bedrock can be used to implement more sophisticated retrieval capabilities using your own documents and data sources.
