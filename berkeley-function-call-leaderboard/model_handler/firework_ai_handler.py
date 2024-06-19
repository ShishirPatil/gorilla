import json
import os
import time

from model_handler.constant import GORILLA_TO_OPENAPI
from model_handler.gpt_handler import OpenAIHandler
from model_handler.model_style import ModelStyle
from model_handler.utils import convert_to_tool, language_specific_pre_processing
from openai import OpenAI


class FireworkAIHandler(OpenAIHandler):
    def __init__(self, model_name, temperature=0.0, top_p=1, max_tokens=1000) -> None:
        super().__init__(model_name, temperature, top_p, max_tokens)
        self.model_style = ModelStyle.FIREWORK_AI
        self.temperature = 0.0

        self.client = OpenAI(
            base_url="https://api.fireworks.ai/inference/v1",
            api_key=os.getenv("FIRE_WORKS_API_KEY"),
        )

    def write(self, result, file_to_open):
        # This method is used to write the result to the file.
        if not os.path.exists("./result"):
            os.mkdir("./result")
        if not os.path.exists(f"./result/{self.model_name}"):
            os.mkdir(f"./result/{self.model_name}")
        with open(
            f"./result/{self.model_name}/"
            + file_to_open.replace(".json", "_result.json"),
            "a+",
        ) as f:
            f.write(json.dumps(result) + "\n")

    def inference(self, prompt, functions, test_category):
        functions = language_specific_pre_processing(functions, test_category, True)
        if type(functions) is not list:
            functions = [functions]
        message = [{"role": "user", "content": prompt}]
        oai_tool = convert_to_tool(
            functions, GORILLA_TO_OPENAPI, self.model_style, test_category, True
        )
        start_time = time.time()
        model_name = self.model_name.replace("-FC", "")
        model_name = f"accounts/fireworks/models/{model_name}"
        if len(oai_tool) > 0:
            response = self.client.chat.completions.create(
                messages=message,
                model=model_name,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                top_p=self.top_p,
                tools=oai_tool,
                frequency_penalty=0.4,
            )
        else:
            response = self.client.chat.completions.create(
                messages=message,
                model=model_name,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                top_p=self.top_p,
            )
        latency = time.time() - start_time
        try:
            result = [
                {func_call.function.name: func_call.function.arguments}
                for func_call in response.choices[0].message.tool_calls
            ]
        except:
            result = response.choices[0].message.content
        metadata = {}
        metadata["input_tokens"] = response.usage.prompt_tokens
        metadata["output_tokens"] = response.usage.completion_tokens
        metadata["latency"] = latency
        return result, metadata
