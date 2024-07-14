import os
import re
import time

from openai import OpenAI

from bfcl.model_handler import utils
from bfcl.model_handler import constants
from bfcl.model_handler.base import BaseHandler, ModelStyle


class DatabricksHandler(BaseHandler):
    model_style = ModelStyle.OPENAI

    def __init__(self, model_name, temperature=0.7, top_p=1, max_tokens=1000) -> None:
        super().__init__(model_name, temperature, top_p, max_tokens)
        assert (api_key := os.getenv('DATABRICKS_API_KEY')), \
            'Please provide your `DATABRICKS_API_KEY` in the .env file.'
        assert (base_url := os.getenv('DATABRICKS_AZURE_ENDPOINT_URL')), \
            'Please provide your `DATABRICKS_AZURE_ENDPOINT_URL` in the .env file.'
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    @classmethod
    def supported_models(cls):
        return [
            'databricks-dbrx-instruct',
        ]

    def inference(self, prompt, functions, test_category):
        functions = utils.language_specific_pre_processing(functions, test_category, False)
        if type(functions) is not list:
            functions = [functions]
        message = [
            {"role": "system", "content": constants.SYSTEM_PROMPT_FOR_CHAT_MODEL},
            {
                "role": "user",
                "content": "Questions:" + constants.USER_PROMPT_FOR_CHAT_MODEL.format(user_prompt=prompt, 
                                                                            functions=str(functions)),
            },
        ]
        start_time = time.time()
        response = self.client.chat.completions.create(
            messages=message,
            model=self.model_name,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            top_p=self.top_p,
        )
        latency = time.time() - start_time
        result = response.choices[0].message.content
        metadata = {}
        metadata["input_tokens"] = response.usage.prompt_tokens
        metadata["output_tokens"] = response.usage.completion_tokens
        metadata["latency"] = latency
        return result, metadata

    def decode_ast(self, result, language="python"):
        func = re.sub(r"'([^']*)'", r"\1", result)
        func = func.replace("\n    ", "")
        if not func.startswith("["):
            func = "[" + func
        if not func.endswith("]"):
            func = func + "]"
        if func.startswith("['"):
            func = func.replace("['", "[")
        try:
            decode_output = utils.ast_parse(func, language)
        except:
            decode_output = utils.ast_parse(result, language)
        return decode_output

    def decode_execute(self, result, language="python"):
        func = re.sub(r"'([^']*)'", r"\1", result)
        func = func.replace("\n    ", "")
        if not func.startswith("["):
            func = "[" + func
        if not func.endswith("]"):
            func = func + "]"
        if func.startswith("['"):
            func = func.replace("['", "[")
        try:
            decode_output = utils.ast_parse(func, language)
        except:
            decode_output = utils.ast_parse(result, language)
        execution_list = []
        for function_call in decode_output:
            for key, value in function_call.items():
                execution_list.append(
                    f"{key}({','.join([f'{k}={repr(v)}' for k, v in value.items()])})"
                )
        return execution_list
