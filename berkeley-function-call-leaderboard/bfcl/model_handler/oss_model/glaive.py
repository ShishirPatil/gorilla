import json

from bfcl.model_handler.utils import convert_to_function_call
from bfcl.model_handler.oss_model.base import OssModelHandler


class GlaiveHandler(OssModelHandler):
    prompt_template = 'SYSTEM: {system_message}\n{functions}\nUSER: {user_input}\n'

    @classmethod
    def supported_models(cls):
        return [
            'glaiveai/glaive-function-calling-v1',
        ]

    def decode_ast(self, result, language="python"):
        function_call = result.split("<functioncall>")[-1]
        function_call = function_call.replace("'", "")
        decoded_function = json.loads(function_call)
        for key, value in decoded_function["arguments"].items():
            if language.lower() != "python":
                # all values of the json are casted to string for java and javascript
                decoded_function["arguments"][key] = str(decoded_function["arguments"][key])
        decoded_result = [{decoded_function["name"]: decoded_function["arguments"]}]
        return decoded_result

    def decode_execute(self, result):
        function_call = result.split("<functioncall>")[-1]
        function_call = function_call.replace("'", "")
        decoded_function = json.loads(function_call)
        decoded_result = [{decoded_function["name"]: decoded_function["arguments"]}]
        return convert_to_function_call(decoded_result)
