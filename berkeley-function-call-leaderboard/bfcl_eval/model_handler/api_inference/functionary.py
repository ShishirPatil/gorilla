from bfcl_eval.model_handler.api_inference.openai import OpenAIHandler
from bfcl_eval.model_handler.model_style import ModelStyle
from openai import OpenAI

# For setup instructions, please refer to https://github.com/MeetKai/functionary for setup details. 
class FunctionaryHandler(OpenAIHandler):
    """
    A handler class for interacting with Functionary models through OpenAI's API interface. This class extends OpenAIHandler to provide specific configuration for Functionary models.
    
    Args:
        model_name (`str`):
            The name of the Functionary model to use
        temperature (`float`):
            The temperature parameter for model generation (controls randomness)
    
    Attributes:
        model_style (`ModelStyle`):
            Set to ModelStyle.OpenAI to indicate compatibility with OpenAI's API
        client (`OpenAI`):
            Configured OpenAI client instance pointing to local Functionary server
    """
    def __init__(self, model_name: str, temperature: float) -> None:
        super().__init__(model_name, temperature)
        self.model_style = ModelStyle.OpenAI

        self.client = OpenAI(base_url="http://localhost:8000/v1", api_key="functionary")
