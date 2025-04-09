import os
import time
from bfcl.model_handler.api_inference.openai import OpenAIHandler
from bfcl.model_handler.model_style import ModelStyle
from openai import OpenAI


class NovitaHandler(OpenAIHandler):
    def __init__(self, model_name, temperature) -> None:
        super().__init__(model_name, temperature)
        self.model_style = ModelStyle.NOVITA_AI
        self.client = OpenAI(
            base_url="https://api.novita.ai/v3/openai",
            api_key=os.getenv("NOVITA_API_KEY"),
        )
