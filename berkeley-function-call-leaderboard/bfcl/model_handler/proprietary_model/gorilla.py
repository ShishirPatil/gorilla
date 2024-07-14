import json
import time

import requests

from bfcl.model_handler import utils
from bfcl.model_handler.base import BaseHandler, ModelStyle


class GorillaHandler(BaseHandler):
    model_style = ModelStyle.GORILLA
    
    @classmethod
    def supported_models(cls):
        return [
            'gorilla-openfunctions-v0',
            'gorilla-openfunctions-v2',
        ]

    def inference(self, prompt, functions, test_category):
        prompt = utils.augment_prompt_by_languge(prompt, test_category)
        functions = utils.language_specific_pre_processing(functions, test_category, False)
        if type(functions) is not list:
            functions = [functions]
        try:
            result, metadata = self._get_gorilla_response(prompt, functions)
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except:
            result = "Error"
            metadata = {"input_tokens": 0, "output_tokens": 0, "latency": 0}
        return result, metadata

    def decode_ast(self, result, language="python"):
        func = "[" + result + "]"
        decoded_output = utils.ast_parse(func, language)
        return decoded_output

    def decode_execute(self, result):
        func = "[" + result + "]"
        decoded_output = utils.ast_parse(func)
        execution_list = []
        for function_call in decoded_output:
            for key, value in function_call.items():
                execution_list.append(
                    f"{key}({','.join([f'{k}={repr(v)}' for k, v in value.items()])})"
                )
        return execution_list

    def _get_gorilla_response(self, prompt, functions):
        requestData = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "functions": functions,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_tokens": self.max_tokens,
        }
        url = "https://luigi.millennium.berkeley.edu:443/v1/chat/completions"
        start = time.time()
        response = requests.post(
            url,
            headers={
                "Content-Type": "application/json",
                "Authorization": "EMPTY",  # Hosted for free with ❤️ from UC Berkeley
            },
            data=json.dumps(requestData),
        )
        latency = time.time() - start
        jsonResponse = response.json()
        metadata = {}
        metadata["input_tokens"] = jsonResponse["usage"]["prompt_tokens"]
        metadata["output_tokens"] = jsonResponse["usage"]["completion_tokens"]
        metadata["latency"] = latency
        directCode = jsonResponse["choices"][0]["message"]["content"]
        return directCode, metadata
