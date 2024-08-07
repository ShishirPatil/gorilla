from bfcl.model_handler.gpt_handler import OpenAIHandler
from bfcl.model_handler.model_style import ModelStyle
import os, json
from openai import OpenAI

# For setup instructions, please refer to https://github.com/MeetKai/functionary for setup details. 
class FunctionaryHandler(OpenAIHandler):
    def __init__(self, model_name, temperature=0.7, top_p=1, max_tokens=1000) -> None:
        self.temperature = temperature
        self.top_p = top_p
        self.max_tokens = max_tokens
        self.model_name = model_name
        self.model_style = ModelStyle.OpenAI

        self.client = OpenAI(base_url="http://localhost:8000/v1", api_key="functionary")
