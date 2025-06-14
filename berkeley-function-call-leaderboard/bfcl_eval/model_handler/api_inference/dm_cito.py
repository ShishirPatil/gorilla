import os
from bfcl_eval.model_handler.model_style import ModelStyle
from openai import OpenAI
from bfcl_eval.model_handler.api_inference.mining import MiningHandler

class DMCitoHandler(MiningHandler):
    def __init__(self, model_name, temperature) -> None:
        super().__init__(model_name, temperature)
        self.model_style = ModelStyle.OpenAI_Completions
        self.client = OpenAI(
            base_url= os.getenv("DMCITO_BASE_URL"),
            api_key=os.getenv("DMCITO_API_KEY"),
        )