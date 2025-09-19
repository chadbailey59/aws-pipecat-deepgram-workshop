# Comparing speech-to-speech and cascaded models

Now that we've implemented both the direct speech-to-speech approach using Nova Sonic and the cascaded models approach, let's compare them in detail to understand their strengths and limitations.

## Comparing the two approaches

|Criteria|Speech-to-Speech (Nova Sonic)|Cascaded Models|
|---|---|---|
|**Latency**|Optimized end-to-end processing|Can use best-of-breed models for each step with potential tradeoffs|
|**Architecture**|Simplified|More complex|
|**Development complexity**|Reduced|Higher|
|**Control**|Less control over individual components|More control over each step|
|**Customization**|Tool use and agentic RAG|Ability to customize each component|
|**Model selection**|Amazon Nova Sonic|Can optimize model selection. This includes models from [Amazon Bedrock Marketplace](https://aws.amazon.com/bedrock/model-marketplace/)  and fine-tuned models|
|**Language and accent support**|Languages supported by Nova Sonic|Broader language support through specialized STT and TTS models|
|**Cost structure**|Single API call per interaction|Multiple API calls (STT, LLM, TTS)|
|**Billing complexity**|Simple|More complex|

## When to use each approach

Use speech-to-speech when:

- Simplicity of implementation is important
- The use case fits within Nova Sonic's capabilities
- You want a more natural and conversational experience

Use cascaded models when:

- Customization of individual components is required
- You need to use specialized models from the [Amazon Bedrock Marketplace](https://aws.amazon.com/bedrock/model-marketplace/)  or fine-tuned models for your specific domain
- You need support for languages or accents not covered by Nova Sonic
- The use case requires specialized processing at specific stages

## Next steps

Now that we understand the differences between the two approaches, let's move on to enhancing our voice agent with additional capabilities.
