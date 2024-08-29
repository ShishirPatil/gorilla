from bfcl.model_handler.base_handler import BaseHandler
from bfcl.model_handler.model_style import ModelStyle
from bfcl.model_handler.utils import (
    ast_parse,
    func_doc_language_specific_pre_processing,
)
import requests, json, re, time


class GorillaHandler(BaseHandler):
    def __init__(self, model_name, temperature=0.001, top_p=1, max_tokens=1000) -> None:
        super().__init__(model_name, temperature, top_p, max_tokens)
        self.model_style = ModelStyle.Gorilla

    def _get_gorilla_response(self, prompt, functions):
        requestData = {
            "model": self.model_name,
            "messages": prompt,
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
        metadata["input_token_count"] = jsonResponse["usage"]["prompt_tokens"]
        metadata["output_token_count"] = jsonResponse["usage"]["completion_tokens"]
        metadata["latency"] = latency
        metadata["processed_message"] = prompt
        metadata["processed_tool"] = functions
        directCode = jsonResponse["choices"][0]["message"]["content"]
        return directCode, metadata

    def inference(self, prompt, functions, test_category):
        functions = func_doc_language_specific_pre_processing(functions, test_category)

        result, metadata = self._get_gorilla_response(prompt, functions)

        return result, metadata

    def decode_ast(self, result, language="Python"):
        func = "[" + result + "]"
        decoded_output = ast_parse(func, language)
        return decoded_output

    def decode_execute(self, result):
        func = "[" + result + "]"
        decoded_output = ast_parse(func)
        execution_list = []
        for function_call in decoded_output:
            for key, value in function_call.items():
                execution_list.append(
                    f"{key}({','.join([f'{k}={repr(v)}' for k, v in value.items()])})"
                )
        return execution_list
