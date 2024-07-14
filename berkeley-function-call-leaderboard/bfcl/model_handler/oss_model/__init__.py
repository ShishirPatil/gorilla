from .deepseek import DeepseekHandler
from .gemma import GemmaHandler
from .glaive import GlaiveHandler
from .hermes import HermesHandler
from .llama import LlamaHandler

__all__ = [
    'DeepseekHandler',
    'GemmaHandler',
    'GlaiveHandler',
    'HermesHandler',
    'LlamaHandler',
]

MODEL_TO_HANDLER_CLS = {}
for handler_name in __all__:
    handler_class = globals()[handler_name]
    for model in handler_class.supported_models():
        MODEL_TO_HANDLER_CLS[model] = handler_class