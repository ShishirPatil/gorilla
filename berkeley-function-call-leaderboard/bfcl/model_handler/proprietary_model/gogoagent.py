import os
from openai import OpenAI
from bfcl.model_handler.model_style import ModelStyle
from bfcl.model_handler.base_handler import BaseHandler
from bfcl.model_handler.proprietary_model.openai import OpenAIHandler

class GoGoAgentHandler(OpenAIHandler):
    def __init__(self, model_name, temperature) -> None:
        BaseHandler.__init__(self, model_name, temperature)
        self.model_style = ModelStyle.OpenAI
        self.is_fc_model = False

        self.client = OpenAI(base_url="https://api.gogoagent.ai", api_key=os.getenv("GOGOAGENT_API_KEY"))
