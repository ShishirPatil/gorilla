from .anthropic import AnthropicFCHandler, AnthropicPromptHandler
from .cohere import CohereHandler
from .databricks import DatabricksHandler
from .firework_ai import FireworkAIHandler
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
    module = globals()[handler_name]
    handler_class = getattr(module, handler_name)
    for model in handler_class.supported_models():
        MODEL_TO_HANDLER_CLS[model] = handler_class