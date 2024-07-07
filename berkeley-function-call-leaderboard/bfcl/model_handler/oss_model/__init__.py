from .deepseek import DeepseekHandler
from .functionary import FunctionaryHandler
from .gemma import GemmaHandler
from .glaive import GlaiveHandler
from .hermes import HermesHandler
from .llama import LlamaHandler

__all__ = [
    'DeepseekHandler',
    'FunctionaryHandler',
    'GemmaHandler',
    'GlaiveHandler',
    'HermesHandler',
    'LlamaHandler',
]

MODEL_TO_HANDLER_CLS = {}
for handler_name in __all__:
    module = globals()[handler_name]
    handler_class = getattr(module, handler_name)
    for model in handler_class.supported_models():
        MODEL_TO_HANDLER_CLS[model] = handler_class