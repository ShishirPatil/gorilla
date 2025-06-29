import os

from bfcl_eval.model_handler.api_inference.openai import OpenAIHandler
from openai import OpenAI


class GoGoAgentHandler(OpenAIHandler):
    """
    A handler class for interacting with the GoGoAgent API, which extends the OpenAIHandler. This class provides a specialized interface for making requests to the GoGoAgent service using the OpenAI client format.
    
    Args:
        model_name (`str`):
            The name of the model to use for generating responses.
        temperature (`float`):
            The temperature parameter for controlling randomness in generation. Lower values make responses more deterministic.
    
    Attributes:
        is_fc_model (`bool`):
            Flag indicating whether this is a function calling model (defaults to False).
        client (`OpenAI`):
            The OpenAI client instance configured to connect to the GoGoAgent API endpoint.
    """
    def __init__(self, model_name: str, temperature: float) -> None:
        super().__init__(model_name, temperature)
        self.is_fc_model = False

        self.client = OpenAI(
            base_url="https://api.gogoagent.ai", api_key=os.getenv("GOGOAGENT_API_KEY")
        )
