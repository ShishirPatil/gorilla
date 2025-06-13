import json
from bfcl.model_handler.local_inference.base_oss_handler import OSSHandler
from overrides import override

class LlamaJsonHandler(OSSHandler):
    def __init__(self, model_name, temperature) -> None:
        super().__init__(model_name, temperature)

    def _convert_functions_format(self, functions):
        if isinstance(functions, dict):
            return {
                "name": functions["name"],
                "description": functions["description"],
                "parameters": {
                    k: v for k, v in functions["parameters"].get("properties", {}).items()
                }
            }
        elif isinstance(functions, list):
            return [self._convert_functions_format(f) for f in functions]
        else:
            return functions

    @override
    def _format_prompt(self, messages, function):
        # We first format the function signature and then add the messages
        tools = self._convert_functions_format(function)

        formatted_prompt = f"""<|begin_of_text|><|begin_of_text|><|begin_of_text|><|start_header_id|>system<|end_header_id|>
Cutting Knowledge Date: December 2023
Today Date: 07 Dec 2024

<|eot_id|><|start_header_id|>user<|end_header_id|>

Given the following functions, please respond with a JSON for a function call with its proper arguments that best answers the given prompt.

Respond in the format {{"name": function name, "parameters": dictionary of argument name and its value}}.Do not use variables.

{tools}

"""
        
        for message in messages:
            formatted_prompt += f"{message['content']}<|eot_id|>\n"

        formatted_prompt += "<|start_header_id|>assistant<|end_header_id|>\n"
        return formatted_prompt
    
    @override
    def decode_ast(self, result, language="Python"):
        # The output is a list of dictionaries, where each dictionary contains the function name and its arguments
        result = result.strip()
        result = result.replace("'", '"') # replace single quotes with double quotes
        result = json.loads(result)

        func_calls = []
        for item in result:
            function_name = item["name"]
            arguments = item["arguments"]
            func_calls.append({function_name: arguments})

        return func_calls
    
    @override
    def decode_execute(self, result):
        # The output is a list of dictionaries, where each dictionary contains the function name and its arguments
        result = result.strip()
        result = result.replace("'", '"') # replace single quotes with double quotes
        result = json.loads(result)

        # put the functions in format function_name(arguments)
        function_call_list = []
        for item in result:
            function_name = item["name"]
            arguments = item["arguments"]
            function_call_list.append(f"{function_name}({arguments})")

        execution_list = []
        for function_call in function_call_list:
            for key, value in function_call.items():
                execution_list.append(
                    f"{key}({','.join([f'{k}={repr(v)}' for k,v in value.items()])})"
                )
        return execution_list