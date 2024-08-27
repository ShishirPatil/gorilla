from bfcl.model_handler.nvidia_handler import NvidiaHandler
from bfcl.model_handler.utils import ast_parse

class ArcticHandler(NvidiaHandler):
    def __init__(self, model_name, temperature=0.001, top_p=1, max_tokens=1000) -> None:
        super().__init__(model_name, temperature, top_p, max_tokens)
        
    def decode_ast(self, result, language="Python"):
        result = result.replace("\n", "")
        if not result.startswith("["):
            result = "[ " + result
        if not result.endswith("]"):
            result = result + " ]"
        if result.startswith("['"):
            result = result.replace("['", "[")
            result = result.replace("', '", ", ")
            result = result.replace("','", ", ")
        if result.endswith("']"):
            result = result.replace("']", "]")
        decode_output = ast_parse(result, language)
        return decode_output
        
    def decode_execute(self, result, language="Python"):
        result = result.replace("\n", "")
        if not result.startswith("["):
            result = "[ " + result
        if not result.endswith("]"):
            result = result + " ]"
        if result.startswith("['"):
            result = result.replace("['", "[")
            result = result.replace("', '", ", ")
            result = result.replace("','", ", ")
        if result.endswith("']"):
            result = result.replace("']", "]")
        decode_output = ast_parse(result, language)
        execution_list = []
        for function_call in decode_output:
            for key, value in function_call.items():
                execution_list.append(
                    f"{key}({','.join([f'{k}={repr(v)}' for k, v in value.items()])})"
                )
        return execution_list