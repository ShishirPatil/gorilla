from bfcl.model_handler.oss_model.llama import LlamaHandler
from bfcl.model_handler.utils import ast_parse

class ToolACEHandler(LlamaHandler):
    def decode_execute(self, result):
        decoded_output = ast_parse(result)
        execution_list = []
        for function_call in decoded_output:
            for key, value in function_call.items():
                execution_list.append(
                    f"{key}({','.join([f'{k}={repr(v)}' for k, v in value.items()])})"
                )
        return execution_list
