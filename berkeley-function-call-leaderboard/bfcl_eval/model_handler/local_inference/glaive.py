import json

from bfcl_eval.model_handler.local_inference.base_oss_handler import OSSHandler
from bfcl_eval.model_handler.utils import convert_to_function_call
from overrides import override


class GlaiveHandler(OSSHandler):
    def __init__(self, model_name, temperature) -> None:
        super().__init__(model_name, temperature)

    @override
    def decode_ast(self, result, language="Python"):
        function_call = result.split("<functioncall>")[-1]
        function_call = function_call.replace("'", "")
        decoded_function = json.loads(function_call)
        for key, value in decoded_function["arguments"].items():
            if language == "Python":
                pass
            else:
                # all values of the json are casted to string for java and javascript
                decoded_function["arguments"][key] = str(
                    decoded_function["arguments"][key]
                )
        decoded_result = [{decoded_function["name"]: decoded_function["arguments"]}]
        return decoded_result

    @override
    def decode_execute(self, result):
        function_call = result.split("<functioncall>")[-1]
        function_call = function_call.replace("'", "")
        decoded_function = json.loads(function_call)
        decoded_result = [{decoded_function["name"]: decoded_function["arguments"]}]
        return convert_to_function_call(decoded_result)
