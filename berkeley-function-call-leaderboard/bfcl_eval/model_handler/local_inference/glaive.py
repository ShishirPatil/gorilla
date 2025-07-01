from typing import Any
import json

from bfcl_eval.model_handler.local_inference.base_oss_handler import OSSHandler
from bfcl_eval.model_handler.utils import convert_to_function_call
from overrides import override


class GlaiveHandler(OSSHandler):
    """
    A handler class for processing and decoding function call results from the Glaive model. Extends OSSHandler to provide specific decoding functionality for function call outputs.
    """
    def __init__(self, model_name: str, temperature: float) -> None:
        super().__init__(model_name, temperature)

    @override
    def decode_ast(self, result: str, language: str="Python") -> list[dict[str, dict[str, Any]]]:
        """
        Decodes the function call result into an abstract syntax tree (AST) representation.
        
        Args:
            result (str): The raw result string containing the function call
            language (str, optional): The target programming language (defaults to 'Python')
        
        Returns:
            list[dict[str, dict[str, Any]]]: A list containing dictionary representations of the function calls with their arguments
        """
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
    def decode_execute(self, result: str):
        """
        Decodes and prepares the function call result for execution.
        
        Args:
            result (str): The raw result string containing the function call
        
        Returns:
            The converted function call ready for execution
        """
        function_call = result.split("<functioncall>")[-1]
        function_call = function_call.replace("'", "")
        decoded_function = json.loads(function_call)
        decoded_result = [{decoded_function["name"]: decoded_function["arguments"]}]
        return convert_to_function_call(decoded_result)
