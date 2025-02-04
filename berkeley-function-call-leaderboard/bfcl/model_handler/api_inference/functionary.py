from bfcl.model_handler.api_inference.openai import OpenAIHandler
from bfcl.model_handler.model_style import ModelStyle
from openai import OpenAI

# For setup instructions, please refer to https://github.com/MeetKai/functionary for setup details. 
class FunctionaryHandler(OpenAIHandler):
    def __init__(self, model_name, temperature) -> None:
        super().__init__(model_name, temperature)
        self.model_style = ModelStyle.OpenAI

        self.client = OpenAI(base_url="http://localhost:8000/v1", api_key="functionary")
