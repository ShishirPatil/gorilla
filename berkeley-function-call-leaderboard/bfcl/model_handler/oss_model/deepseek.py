import re

from bfcl.model_handler.utils import ast_parse
from bfcl.model_handler.oss_model.base import OssModelHandler


class DeepseekHandler(OssModelHandler):
    system_message = (
        'You are an AI programming assistant, utilizing the DeepSeek Coder model, developed by DeepSeek Company, and you only answer questions related to computer science. For politically sensitive questions, security and privacy issues, and other non-computer science questions, you will refuse to answer.\n'
        '### Instruction:\n'
        'You are a helpful assistant with access to the following functions. Use them if required -'
    )
    prompt_template = (
        '{system_message}\n'
        '{functions}\n'
        'Here is the question you need to answer:\n'
        '{user_input}\n'
        'Your job is to solve the above question using ONLY and strictly ONE line of python code given the above functions. If you think no function should be invoked return "[]".\n'
        'If you think one or more function should be invoked, return the function call in the format of [func1(params_name=params_value, params_name2=params_value2...), func2(params)] wrapped in python code'
        '### Response:\n'
    )

    @classmethod
    def supported_models(cls):
        return [
            'deepseek-ai/deepseek-coder-6.7b-instruct',
        ]
    
    def decode_ast(self, result, language="python"):
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
