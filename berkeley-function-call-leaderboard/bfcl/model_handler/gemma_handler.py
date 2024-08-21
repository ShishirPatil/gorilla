from bfcl.model_handler.oss_handler import OSSHandler
from bfcl.model_handler.utils import ast_parse
import re


class GemmaHandler(OSSHandler):
    def __init__(self, model_name, temperature=0.001, top_p=1, max_tokens=1000) -> None:
        super().__init__(model_name, temperature, top_p, max_tokens)

    def decode_ast(self, result, language="Python"):
        pattern = r"\[(.*)\]"

        # Searching for the pattern in the input text
        match = re.search(pattern, result, re.DOTALL)
        raw_input = match.group(1)
        func = "[" + raw_input + "]"
        decoded_output = ast_parse(func, language=language)
        return decoded_output

    def decode_execute(self, result):
        pattern = r"\[(.*)\]"

        # Searching for the pattern in the input text
        match = re.search(pattern, result, re.DOTALL)
        raw_input = match.group(1)
        func = "[" + raw_input + "]"
        decoded_output = ast_parse(func)
        execution_list = []
        for function_call in decoded_output:
            for key, value in function_call.items():
                execution_list.append(
                    f"{key}({','.join([f'{k}={repr(v)}' for k, v in value.items()])})"
                )
        return execution_list
