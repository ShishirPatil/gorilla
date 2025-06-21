import os
from bfcl_eval.model_handler.model_style import ModelStyle
from openai import OpenAI
from bfcl_eval.model_handler.api_inference.mining import MiningHandler

class DMCitoHandler(MiningHandler):
    """
    Handler for interacting with the DMCito API for mining operations. This class extends the MiningHandler base class and implements OpenAI-style API interactions.
    
    Args:
        model_name (`str`):
            Name of the model to use for mining operations.
        temperature (`float`):
            Temperature parameter for controlling randomness in model outputs.
    
    Attributes:
        model_style (`ModelStyle`):
            The style of model being used (set to OpenAI for this handler).
        client (`OpenAI`):
            The OpenAI client instance configured with DMCito-specific API settings.
    """
    def __init__(self, model_name: str, temperature: float) -> None:
        super().__init__(model_name, temperature)
        self.model_style = ModelStyle.OpenAI
        self.client = OpenAI(
            base_url= os.getenv("DMCITO_BASE_URL"),
            api_key=os.getenv("DMCITO_API_KEY"),
        )