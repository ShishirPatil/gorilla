import json
import os

from model_handler.gpt_handler import OpenAIHandler
from model_handler.model_style import ModelStyle
from openai import OpenAI


class FireworkAIHandler(OpenAIHandler):
    def __init__(self, model_name, temperature=0.7, top_p=1, max_tokens=1000) -> None:
        super().__init__(model_name, temperature, top_p, max_tokens)
        # self.model_name = "accounts/fireworks/models/firefunction-v1-FC"
        # self.model_name = "accounts/fireworks/models/fc-pawel-v2-14-FC"
        self.model_name = "accounts/fireworks/models/dt-fc-rc-v5-FC"
        self.temperature = 0
        self.model_style = ModelStyle.FIREWORK_AI

        self.client = OpenAI(
            base_url="https://api.fireworks.ai/inference/v1",
            api_key=os.getenv("FIRE_WORKS_API_KEY"),
        )

    def write(self, result, file_to_open):
        # This method is used to write the result to the file.
        if not os.path.exists("./result"):
            os.mkdir("./result")
        if not os.path.exists("./result/fire-function-v1-FC"):
            os.mkdir("./result/fire-function-v1-FC")
        with open(
            "./result/fire-function-v1-FC/"
            + file_to_open.replace(".json", "_result.json"),
            "a+",
        ) as f:
            f.write(json.dumps(result) + "\n")
