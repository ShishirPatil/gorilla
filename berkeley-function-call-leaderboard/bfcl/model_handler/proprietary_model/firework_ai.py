import os
import time

from openai import OpenAI

from bfcl.model_handler.constants import GORILLA_TO_OPENAPI
from bfcl.model_handler.base import ModelStyle
from bfcl.model_handler.proprietary_model.openai import OpenAIHandler
from bfcl.model_handler.utils import convert_to_tool, language_specific_pre_processing



class FireworkAIHandler(OpenAIHandler):
    model_style = ModelStyle.FIREWORK_AI

    def __init__(self, model_name, temperature=0.0, top_p=1, max_tokens=1000) -> None:
        super().__init__(model_name=model_name, temperature=0.0, top_p=top_p, max_tokens=max_tokens)
        self.client = OpenAI(
            base_url="https://api.fireworks.ai/inference/v1",
            api_key=os.getenv("FIREWORKS_API_KEY"),
        )

    @classmethod
    def supported_models(cls):
        return [
            'firefunction-v1-FC',
            'firefunction-v2-FC',
        ]
    
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
