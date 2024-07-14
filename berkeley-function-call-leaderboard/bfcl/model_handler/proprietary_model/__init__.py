from .anthropic import AnthropicFCHandler, AnthropicPromptHandler
from .cohere import CohereHandler
from .databricks import DatabricksHandler
from .firework_ai import FireworkAIHandler
from .functionary import FunctionaryHandler
from .gemini import GeminiHandler
from .gorilla import GorillaHandler
from .mistral import MistralHandler
from .nexus import NexusHandler
from .nvidia import NvidiaHandler
from .openai import OpenAIHandler
from .snowflake import SnowflakeHandler

__all__ = [
    'AnthropicFCHandler',
    'AnthropicPromptHandler',
    'CohereHandler',
    'DatabricksHandler',
    'FireworkAIHandler',
    'FunctionaryHandler',
    'GeminiHandler',
    'GorillaHandler',
    'MistralHandler',
    'NexusHandler',
    'NvidiaHandler',
    'OpenAIHandler',
    'SnowflakeHandler',
]

MODEL_TO_HANDLER_CLS = {}
for handler_name in __all__:
    handler_class = globals()[handler_name]
    for model in handler_class.supported_models():
        MODEL_TO_HANDLER_CLS[model] = handler_class