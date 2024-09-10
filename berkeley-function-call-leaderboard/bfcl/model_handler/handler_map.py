from bfcl.model_handler.proprietary_model.claude import ClaudeHandler
from bfcl.model_handler.proprietary_model.cohere import CohereHandler
from bfcl.model_handler.proprietary_model.databricks import DatabricksHandler
from bfcl.model_handler.oss_model.deepseek import DeepseekHandler
from bfcl.model_handler.proprietary_model.fireworks import FireworksHandler
from bfcl.model_handler.proprietary_model.functionary import FunctionaryHandler
from bfcl.model_handler.proprietary_model.gemini import GeminiHandler
from bfcl.model_handler.oss_model.gemma import GemmaHandler
from bfcl.model_handler.oss_model.glaive import GlaiveHandler
from bfcl.model_handler.proprietary_model.gorilla import GorillaHandler
from bfcl.model_handler.proprietary_model.openai import OpenAIHandler
from bfcl.model_handler.oss_model.hermes import HermesHandler
from bfcl.model_handler.oss_model.llama import LlamaHandler
from bfcl.model_handler.proprietary_model.mistral import MistralHandler
from bfcl.model_handler.proprietary_model.nexus import NexusHandler
from bfcl.model_handler.oss_model.base_oss_handler import OSSHandler
from bfcl.model_handler.oss_model.granite import GraniteHandler
from bfcl.model_handler.proprietary_model.nvidia import NvidiaHandler
from bfcl.model_handler.oss_model.glm import GLMHandler
from bfcl.model_handler.proprietary_model.yi import YiHandler
from bfcl.model_handler.oss_model.salesforce import SalesforceHandler
from bfcl.model_handler.oss_model.hammer import HammerHandler

handler_map = {
    "gorilla-openfunctions-v0": GorillaHandler,
    "gorilla-openfunctions-v2": GorillaHandler,
    "gpt-4o-2024-08-06": OpenAIHandler,
    "gpt-4o-2024-08-06-FC": OpenAIHandler,
    "gpt-4o-2024-05-13": OpenAIHandler,
    "gpt-4o-2024-05-13-FC": OpenAIHandler,
    "gpt-4o-mini-2024-07-18": OpenAIHandler,
    "gpt-4o-mini-2024-07-18-FC": OpenAIHandler,
    "gpt-4-turbo-2024-04-09-FC": OpenAIHandler,
    "gpt-4-turbo-2024-04-09": OpenAIHandler,
    "gpt-4-1106-preview-FC": OpenAIHandler,
    "gpt-4-1106-preview": OpenAIHandler,
    "gpt-4-0125-preview-FC": OpenAIHandler,
    "gpt-4-0125-preview": OpenAIHandler,
    "gpt-4-0613-FC": OpenAIHandler,
    "gpt-4-0613": OpenAIHandler,
    "gpt-3.5-turbo-0125-FC": OpenAIHandler,
    "gpt-3.5-turbo-0125": OpenAIHandler,
    "claude-2.1": ClaudeHandler,
    "claude-instant-1.2": ClaudeHandler,
    "claude-3-opus-20240229": ClaudeHandler,
    "claude-3-opus-20240229-FC": ClaudeHandler,
    "claude-3-sonnet-20240229": ClaudeHandler,
    "claude-3-sonnet-20240229-FC": ClaudeHandler,
    "claude-3-haiku-20240307": ClaudeHandler,
    "claude-3-haiku-20240307-FC": ClaudeHandler,
    "claude-3-5-sonnet-20240620": ClaudeHandler,
    "claude-3-5-sonnet-20240620-FC": ClaudeHandler,
    "open-mistral-nemo-2407": MistralHandler,
    "open-mistral-nemo-2407-FC-Any": MistralHandler,
    "open-mistral-nemo-2407-FC-Auto": MistralHandler,
    "open-mixtral-8x22b": MistralHandler,
    "open-mixtral-8x22b-FC-Any": MistralHandler,
    "open-mixtral-8x22b-FC-Auto": MistralHandler,
    "open-mixtral-8x7b": MistralHandler,
    "mistral-large-2407": MistralHandler,
    "mistral-large-2407-FC-Any": MistralHandler,
    "mistral-large-2407-FC-Auto": MistralHandler,
    "mistral-medium-2312": MistralHandler,
    "mistral-small-2402": MistralHandler,
    "mistral-small-2402-FC-Any": MistralHandler,
    "mistral-small-2402-FC-Auto": MistralHandler,
    "mistral-tiny-2312": MistralHandler,
    "firefunction-v1-FC": FireworksHandler,
    "firefunction-v2-FC": FireworksHandler,
    "Nexusflow-Raven-v2": NexusHandler,
    "gemini-1.0-pro": GeminiHandler,
    "gemini-1.5-pro-preview-0409": GeminiHandler,
    "gemini-1.5-pro-preview-0514": GeminiHandler,
    "gemini-1.5-flash-preview-0514": GeminiHandler,
    "google/gemma-7b-it": GemmaHandler,
    "glaiveai/glaive-function-calling-v1": GlaiveHandler,
    "deepseek-ai/deepseek-coder-6.7b-instruct": DeepseekHandler,
    "meetkai/functionary-small-v3.1-FC": FunctionaryHandler,
    "meetkai/functionary-small-v3.2-FC": FunctionaryHandler,
    "meetkai/functionary-medium-v3.1-FC": FunctionaryHandler,
    "databricks-dbrx-instruct": DatabricksHandler,
    "NousResearch/Hermes-2-Pro-Llama-3-8B": HermesHandler,
    "NousResearch/Hermes-2-Pro-Llama-3-70B": HermesHandler,
    "NousResearch/Hermes-2-Pro-Mistral-7B": HermesHandler,
    "NousResearch/Hermes-2-Theta-Llama-3-8B": HermesHandler,
    "NousResearch/Hermes-2-Theta-Llama-3-70B": HermesHandler,
    "meta-llama/Meta-Llama-3-8B-Instruct": LlamaHandler,
    "meta-llama/Meta-Llama-3-70B-Instruct": LlamaHandler,
    "command-r-plus-FC": CohereHandler,
    "command-r-plus": CohereHandler,
    "command-r-plus-FC-optimized": CohereHandler,
    "command-r-plus-optimized": CohereHandler,
    "snowflake/arctic": NvidiaHandler,
    "ibm-granite/granite-20b-functioncalling": GraniteHandler,
    "nvidia/nemotron-4-340b-instruct": NvidiaHandler,
    "THUDM/glm-4-9b-chat": GLMHandler,
    "yi-large-fc": YiHandler,
    "Salesforce/xLAM-1b-fc-r": SalesforceHandler,
    "Salesforce/xLAM-7b-fc-r": SalesforceHandler,
    "Salesforce/xLAM-7b-r": SalesforceHandler,
    "Salesforce/xLAM-8x7b-r": SalesforceHandler,
    "Salesforce/xLAM-8x22b-r": SalesforceHandler,
    "MadeAgents/Hammer-7b": HammerHandler
}
