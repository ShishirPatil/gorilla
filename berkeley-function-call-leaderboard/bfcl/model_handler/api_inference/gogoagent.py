import os

from bfcl.model_handler.api_inference.openai import OpenAIHandler
from openai import OpenAI


class GoGoAgentHandler(OpenAIHandler):
    """
    A handler class for interacting with the GoGoAgent AI API, extending OpenAIHandler functionality.
    
    Args:
        model_name (`str`):
            Name of the model to use for completions.
        temperature (`float`):
            Sampling temperature to use for generation, between 0 and 2. Higher values make output more random.
    """
    def __init__(self, model_name: str, temperature: float) -> None:
        super().__init__(model_name, temperature)
        self.is_fc_model = False

        self.client = OpenAI(
            base_url="https://api.gogoagent.ai", api_key=os.getenv("GOGOAGENT_API_KEY")
        )
