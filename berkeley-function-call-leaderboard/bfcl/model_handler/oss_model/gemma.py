import re

from bfcl.model_handler.utils import ast_parse
from bfcl.model_handler.oss_model.base import OssModelHandler


class GemmaHandler(OssModelHandler):
    prompt_template = (
        '<bos><start_of_turn>user\n'
        '{system_message}\n'
        '{functions}\n'
        'Here is the question you need to answer:\n'
        '{user_input}\n'
        'Your job is to solve the above question using ONLY and strictly ONE line of python code given the above functions. If you think no function should be invoked return "[]".\n'
        'If you think one or more function should be invoked, return the function call in the format of [func1(params_name=params_value, params_name2=params_value2...), func2(params)] wrapped in python code'
        '<end_of_turn>\n'
        '<start_of_turn>model\n'
    )

    @classmethod
    def supported_models(cls):
        return [
            'google/gemma-7b-it',
        ]

    def decode_ast(self, result, language="python"):
        match = re.search(r"\[(.*)\]", result, re.DOTALL)
        raw_input = match.group(1)
        func = "[" + raw_input + "]"
        decoded_output = ast_parse(func, language=language)
        return decoded_output

    def decode_execute(self, result):
        match = re.search(r"\[(.*)\]", result, re.DOTALL)
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
