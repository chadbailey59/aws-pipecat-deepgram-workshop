# Lab 1: Building a basic voice AI agent with Amazon Nova Sonic

In this lab, we'll explore how to build voice AI agents using Amazon Nova Sonic and the Pipecat framework. You'll learn the fundamentals of creating interactive voice experiences with real-time conversation capabilities.

## Architecture overview

When building a voice AI agent with Amazon Nova Sonic and Pipecat, the high-level architecture looks like this:

![Voice AI Agent Architecture](https://static.us-east-1.prod.workshops.aws/public/80e2f4fb-7fe5-4c2c-88fb-fb5de05b1533/static/images/voice-ai-architecture.png)

The architecture consists of:

1. **User**: Interacts with the voice AI agent through speech
2. **Pipecat Framework**: Orchestrates all the components needed for the voice AI agent:
    - **WebRTC Transport**: Handles audio streaming between the user and the pipeline
    - **Silero Voice Activity Detection (VAD) Analyzer**: Detects when users start and stop speaking
    - **Pipecat Pipeline**: Orchestrates the flow of data through the system
    - **LLM Context**: Maintains conversation history, state and control of tool use (function calling)
    - **Amazon Nova Sonic**: Processes audio input and generates responses
    - **Tools (or function calling)**: Includes an example `weather_function` implementation and its associated `FunctionSchema`

## Understanding Amazon Nova Sonic

Amazon Nova Sonic is a direct speech-to-speech AI service that enables natural, fluid voice interactions. Unlike traditional approaches that use separate components for speech-to-text, language processing, and text-to-speech, Nova Sonic provides an integrated solution for building voice AI agents.

### Key features of Amazon Nova Sonic

- **Direct Speech-to-Speech Processing**: Processes spoken language and generates spoken responses without intermediate text conversion
- **Low Latency**: Provides faster response times for more natural conversations
- **Context Awareness**: Maintains conversation context for coherent interactions
- **Function Calling**: Supports calling external functions to retrieve information or perform actions
- **Voice Selection**: Offers multiple voice options (e.g., Matthew, Tiffany, Amy)

Region Availability

As of May 2025, Amazon Nova Sonic is only available in the us-east-1 region.

## Introduction to Pipecat

Pipecat is an open-source framework that simplifies the creation of voice AI agents. It provides a structured way to build pipelines for processing audio, managing context, and integrating with various AI services.

### Why use Pipecat with speech-to-speech models?

While speech-to-speech models like Amazon Nova Sonic simplify voice AI development, production systems still face several challenges. Pipecat addresses these by handling:

- Real-time audio streaming with precise timing control
- User interruptions and silence detection
- Integration with fallback services and external tools
- Conversation context preservation across interactions
- WebRTC and telephony connections

Pipecat manages these complex technical aspects so you can focus on designing great conversational experiences rather than dealing with low-level audio processing and stream management.

## In this lab

In the following sections, we'll:

- Build a voice agent with function calling capabilities
- Configure your voice agent with Amazon Nova Sonic
- Test and improve your voice agent
