import os
from bfcl_eval.model_handler.api_inference.openai_completion import OpenAICompletionsHandler
from bfcl_eval.model_handler.model_style import ModelStyle
from openai import OpenAI


class KimiHandler(OpenAICompletionsHandler):
    def __init__(self, model_name: str, temperature: float) -> None:
        super().__init__(model_name, temperature)

        self.client = OpenAI(
            base_url="https://platform.moonshot.ai", 
            api_key=os.getenv("KIMI_API_KEY")
        )
