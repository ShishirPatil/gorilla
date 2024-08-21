from bfcl.model_handler.oss_handler import OSSHandler
from bfcl.model_handler.utils import ast_parse
import re


class DeepseekHandler(OSSHandler):
    def __init__(self, model_name, temperature=0.001, top_p=1, max_tokens=1000) -> None:
        super().__init__(model_name, temperature, top_p, max_tokens)

    def decode_ast(self, result, language="Python"):
        function_call = result.split("```")[1]
        matches = re.findall(r"\[[^\]]*\]", function_call)
        decoded_output = ast_parse(matches[0], language)
        return decoded_output

    def decode_execute(self, result):
        function_call = result.split("```")[1]
        matches = re.findall(r"\[[^\]]*\]", function_call)
        decoded_output = ast_parse(matches[0])
        execution_list = []
        for function_call in decoded_output:
            for key, value in function_call.items():
                execution_list.append(
                    f"{key}({','.join([f'{k}={repr(v)}' for k, v in value.items()])})"
                )
        return execution_list
