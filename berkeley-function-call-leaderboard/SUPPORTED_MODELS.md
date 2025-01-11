# Table of Supported Models

Below is a comprehensive table of models supported for running leaderboard evaluations. Each model entry indicates whether it supports native Function Calling (FC) or requires a special prompt format to generate function calls. Models marked with `💻` are intended to be hosted locally (using vllm or sglang), while models without the `💻` icon are accessed via API calls. To quickly see all available models, you can also run the `bfcl models` command.

**Note:**  

- **Function Calling (FC)** models directly support the function calling schema as documented by their respective providers.
- **Prompt** models do not natively support function calling. For these, we supply a consistent system message prompting the model to produce function calls in the desired format.

|Model | Type |
|---|---|
|gorilla-openfunctions-v2 | Function Calling|
|DeepSeek-V3 | Function Calling|
|claude-3-opus-20240229-FC | Function Calling |
|claude-3-opus-20240229 | Prompt |
|claude-3-5-sonnet-20241022-FC | Function Calling |
|claude-3-5-sonnet-20241022 | Prompt |
|claude-3-5-haiku-20241022-FC | Function Calling |
|claude-3-5-haiku-20241022 | Prompt |
|gpt-3.5-turbo-0125-FC| Function Calling|
|gpt-3.5-turbo-0125| Prompt|
|gpt-4-turbo-2024-04-09-FC| Function Calling|
|gpt-4-turbo-2024-04-09| Prompt|
|gpt-4o-2024-11-20-FC | Function Calling|
|gpt-4o-2024-11-20 | Prompt|
|gpt-4o-mini-2024-07-18-FC | Function Calling|
|gpt-4o-mini-2024-07-18 | Prompt|
|o1-2024-12-17-FC | Function Calling|
|o1-2024-12-17 | Prompt|
|o1-mini-2024-09-12 | Prompt|
|gemini-1.0-pro-002-FC | Function Calling|
|gemini-1.0-pro-002 | Prompt|
|gemini-1.5-pro-{001,002}-FC | Function Calling|
|gemini-1.5-pro-{001,002} | Prompt|
|gemini-1.5-flash-{001,002}-FC | Function Calling|
|gemini-1.5-flash-{001,002} | Prompt|
|gemini-2.0-flash-exp-FC | Function Calling|
|gemini-2.0-flash-exp | Prompt|
|gemini-exp-1206-FC | Function Calling|
|gemini-exp-1206 | Prompt|
|open-mixtral-{8x7b,8x22b} | Prompt|
|open-mixtral-8x22b-FC | Function Calling|
|open-mistral-nemo-2407 | Prompt|
|open-mistral-nemo-2407-FC | Function Calling|
|mistral-large-2407-FC | Function Calling|
|mistral-large-2407 | Prompt|
|mistral-medium-2312 | Prompt|
|mistral-small-2402-FC | Function Calling|
|mistral-small-2402 | Prompt|
|mistral-tiny-2312 | Prompt|
|nova-pro-v1.0| Function Calling|
|nova-lite-v1.0| Function Calling|
|nova-macro-v1.0| Function Calling|
|command-r-plus-FC | Function Calling|
|command-r7b-12-2024-FC | Function Calling|
|databrick-dbrx-instruct | Prompt|
|firefunction-{v1,v2}-FC | Function Calling|
|yi-large-fc | Function Calling|
|grok-beta | Function Calling|
|nvidia/nemotron-4-340b-instruct| Prompt|
|meetkai/functionary-{small,medium}-v3.1-FC| Function Calling|
|Nexusflow-Raven-v2 | Function Calling|
|palmyra-x-004 | Function Calling|
|snowflake/arctic | Prompt|
|palmyra-x-004 | Function Calling|
|BitAgent/GoGoAgent | Prompt|
|google/gemma-2-{2b,9b,27b}-it 💻| Prompt|
|mistralai/Ministral-8B-Instruct-2410 💻| Function Calling|
|meta-llama/Meta-Llama-3-{8B,70B}-Instruct 💻| Prompt|
|meta-llama/Llama-3.1-{8B,70B}-Instruct-FC 💻| Function Calling|
|meta-llama/Llama-3.1-{8B,70B}-Instruct 💻| Prompt|
|meta-llama/Llama-3.2-{1B,3B}-Instruct 💻| Prompt|
|meta-llama/Llama-3.3-70B-Instruct 💻| Prompt|
|meta-llama/Llama-3.3-70B-Instruct-FC 💻| Function Calling|
|deepseek-ai/DeepSeek-V2.5 💻| Function Calling|
|deepseek-ai/DeepSeek-V2-{Chat-0628,Lite-Chat} 💻| Prompt|
|deepseek-ai/DeepSeek-Coder-V2-{Instruct-0724,Lite-Instruct} 💻| Function Calling|
|Qwen/Qwen2.5-{0.5B,1.5B,3B,7B,14B,32B,72B}-Instruct 💻| Prompt|
|Qwen/Qwen2-{1.5B,7B}-Instruct 💻| Prompt|
|Salesforce/xLAM-1b-fc-r 💻| Function Calling|
|Salesforce/xLAM-7b-fc-r 💻| Function Calling|
|Salesforce/xLAM-7b-r 💻| Function Calling|
|Salesforce/xLAM-8x7b-r 💻| Function Calling|
|Salesforce/xLAM-8x22b-r 💻| Function Calling|
|microsoft/Phi-3.5-mini-instruct 💻| Prompt|
|microsoft/Phi-3-medium-{4k,128k}-instruct 💻| Prompt|
|microsoft/Phi-3-small-{8k,128k}-instruct 💻| Prompt|
|microsoft/Phi-3-mini-{4k,128k}-instruct 💻| Prompt|
|ibm-granite/granite-20b-functioncalling 💻| Function Calling|
|NousResearch/Hermes-2-Pro-Llama-3-{8B,70B} 💻| Function Calling|
|NousResearch/Hermes-2-Pro-Mistral-7B 💻| Function Calling|
|NousResearch/Hermes-2-Theta-Llama-3-{8B,70B} 💻| Function Calling|
|MadeAgents/Hammer2.1-{7b,3b,1.5b,0.5b} 💻| Function Calling|
|openbmb/MiniCPM3-4B-FC 💻| Function Calling|
|openbmb/MiniCPM3-4B 💻| Prompt|
|THUDM/glm-4-9b-chat 💻| Function Calling|
|Team-ACE/ToolACE-8B 💻| Function Calling|
|watt-ai/watt-tool-{8B,70B} 💻| Function Calling|
|ZJared/Haha-7B 💻| Prompt|

---

## Understanding Versioned Models

For model names containing `{...}`, multiple versions are available. For example, `meta-llama/Llama-3.1-{8B,70B}-Instruct` means we support both models: `meta-llama/Llama-3.1-8B-Instruct` and `meta-llama/Llama-3.1-70B-Instruct`.

## Additional Requirements for Certain Models

- **Gemini Models:**  
  For `Gemini` models, we use the Google Vertex AI endpoint for inference. Ensure you have set the `VERTEX_AI_PROJECT_ID` and `VERTEX_AI_LOCATION` in your `.env` file.

- **Databricks Models:**  
  For `databrick-dbrx-instruct`, you must create an Azure Databricks workspace and set up a dedicated inference endpoint. Provide the endpoint URL via `DATABRICKS_AZURE_ENDPOINT_URL` in `.env`.

- **Nova Models (AWS Bedrock):**  
  For `Nova` models, set your `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` in your `.env` file. Make sure the necessary AWS Bedrock permissions are granted in the `us-east-1` region.

---

For more details and a summary of feature support across different models, see the [Berkeley Function Calling Leaderboard blog post](https://gorilla.cs.berkeley.edu/blogs/8_berkeley_function_calling_leaderboard.html#prompt).
