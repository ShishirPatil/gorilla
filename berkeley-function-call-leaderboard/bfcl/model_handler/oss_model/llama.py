from bfcl.model_handler import constants
from bfcl.model_handler.utils import ast_parse
from bfcl.model_handler.oss_model.base import OssModelHandler


class LlamaHandler(OssModelHandler):
    system_message = constants.SYSTEM_PROMPT_FOR_CHAT_MODEL
    prompt_template = (
        '<|begin_of_text|><|start_header_id|>system<|end_header_id|>{system_message}<|eot_id|><|start_header_id|>'
        f'user<|end_header_id|>{constants.USER_PROMPT_FOR_CHAT_MODEL}'
        '<|eot_id|><|start_header_id|>assistant<|end_header_id|>'
    )

    @classmethod
    def supported_models(cls):
        return [
            'meta-llama/Meta-Llama-3-8B-Instruct',
            'meta-llama/Meta-Llama-3-70B-Instruct',
        ]
    
    def decode_ast(self, result, language="python"):
        func = result
        func = func.replace("\n", "")  # remove new line characters
        if not func.startswith("["):
            func = "[" + func
        if not func.endswith("]"):
            func = func + "]"
        decoded_output = ast_parse(func, language)
        return decoded_output

    def decode_execute(self, result):
        func = result
        func = func.replace("\n", "")  # remove new line characters
        if not func.startswith("["):
            func = "[" + func
        if not func.endswith("]"):
            func = func + "]"
        decode_output = ast_parse(func)
        execution_list = []
        for function_call in decode_output:
            for key, value in function_call.items():
                execution_list.append(
                    f"{key}({','.join([f'{k}={repr(v)}' for k, v in value.items()])})"
                )
        return execution_list
