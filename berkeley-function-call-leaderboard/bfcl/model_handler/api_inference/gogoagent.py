import os

from bfcl.model_handler.api_inference.openai import OpenAIHandler
from openai import OpenAI


class GoGoAgentHandler(OpenAIHandler):
    def __init__(self, model_name, temperature) -> None:
        super().__init__(model_name, temperature)
        self.is_fc_model = False

        self.client = OpenAI(
            base_url="https://api.gogoagent.ai", api_key=os.getenv("GOGOAGENT_API_KEY")
        )
