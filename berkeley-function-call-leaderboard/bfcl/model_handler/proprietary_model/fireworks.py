import os
import time

from bfcl.model_handler.constant import GORILLA_TO_OPENAPI
from bfcl.model_handler.proprietary_model.openai import OpenAIHandler
from bfcl.model_handler.model_style import ModelStyle
from bfcl.model_handler.utils import (
    convert_to_tool,
    func_doc_language_specific_pre_processing,
)
from openai import OpenAI


class FireworksHandler(OpenAIHandler):
    def __init__(self, model_name, temperature=0.001, top_p=1, max_tokens=1000) -> None:
        super().__init__(model_name, temperature, top_p, max_tokens)
        self.model_style = ModelStyle.FIREWORK_AI

        self.client = OpenAI(
            base_url="https://api.fireworks.ai/inference/v1",
            api_key=os.getenv("FIRE_WORKS_API_KEY"),
        )

    def inference(self, prompt, functions, test_category):
        functions = func_doc_language_specific_pre_processing(functions, test_category)

        message = prompt
        oai_tool = convert_to_tool(
            functions, GORILLA_TO_OPENAPI, self.model_style, test_category
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
        metadata["input_token_count"] = response.usage.prompt_tokens
        metadata["output_token_count"] = response.usage.completion_tokens
        metadata["latency"] = latency
        metadata["processed_message"] = message
        metadata["processed_tool"] = oai_tool
        return result, metadata
