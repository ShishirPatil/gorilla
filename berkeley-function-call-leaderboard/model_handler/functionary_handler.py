from model_handler.gpt_handler import OpenAIHandler
from model_handler.model_style import ModelStyle
import os, json
from openai import OpenAI


class FunctionaryHandler(OpenAIHandler):
    def __init__(self, model_name, temperature=0.7, top_p=1, max_tokens=1000) -> None:
        super().__init__(model_name, temperature, top_p, max_tokens)
        self.model_name = model_name
        self.model_style = ModelStyle.OpenAI

        self.client = OpenAI(base_url="http://localhost:8000/v1", api_key="functionary")

    def write(self, result, file_to_open):
        if not os.path.exists("./result"):
            os.mkdir("./result")
        if not os.path.exists("./result/" + self.model_name.replace("/", "_")):
            os.mkdir("./result/" + self.model_name.replace("/", "_"))
        with open(
            "./result/" + self.model_name.replace("/", "_") + "/" + file_to_open, "a+"
        ) as f:
            f.write(json.dumps(result) + "\n")
