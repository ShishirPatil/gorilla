from model_handler.model_style import ModelStyle
from model_handler.handler import BaseHandler
from model_handler.utils import (
    ast_parse,
    augment_prompt_by_languge,
    language_specific_pre_processing,
)
import requests, time


class NexusHandler(BaseHandler):
    def __init__(self, model_name, temperature=0.7, top_p=1, max_tokens=1000) -> None:
        super().__init__(model_name, temperature, top_p, max_tokens)
        self.model_style = ModelStyle.NEXUS

    def _format_raven_function(self, user_prompt, functions):
        """
        Nexus-Raven requires a specific format for the function description.
        This function formats the function description in the required format.
        """
        raven_prompt = """"""
        for function in functions:
            # Extracting details from the JSON
            func_name = function["name"]  # Extracting the function name
            func_desc = function["description"]
            if "properties" not in function["parameters"]:
                function["parameters"]["properties"] = function["parameters"].copy()
                function["parameters"]["type"] = "object"
                for key in list(function["parameters"].keys()).copy():
                    if key != "properties" and key != "type" and key != "required":
                        del function["parameters"][key]
                for key in list(function["parameters"]["properties"].keys()).copy():
                    if key == "required" or key == "type":
                        del function["parameters"]["properties"][key]
            params = function["parameters"]["properties"]

            raven_prompt += "Function: " + "\n"
            raven_prompt += f"def {func_name}(" + "\n"
            raven_prompt += '"""\n'
            raven_prompt += func_desc + "\n\n"
            raven_prompt += "Args:" + "\n"
            for param in params:
                if "type" not in params[param].keys():
                    param_type = "object"
                else:
                    param_type = params[param]["type"]
                if "description" not in params[param].keys():
                    param_desc = ""
                else:
                    param_desc = params[param]["description"]
                raven_prompt += f"\t{param}({param_type}): {param_desc}" + "\n"
            raven_prompt += "\n"
        raven_prompt += "User Query:" + user_prompt + "<human_end>"
        return raven_prompt

    def _query_raven(self, prompt):
        """
        Query Nexus-Raven.
        """

        API_URL = "http://nexusraven.nexusflow.ai"
        headers = {"Content-Type": "application/json"}

        def query(payload):
            """
            Sends a payload to a TGI endpoint.
            """
            response = requests.post(API_URL, headers=headers, json=payload)
            return response.json()

        start = time.time()
        output = query(
            {
                "inputs": prompt,
                "parameters": {
                    "temperature": self.temperature,
                    "stop": ["<bot_end>"],
                    "do_sample": False,
                    "max_new_tokens": self.max_tokens,
                    "return_full_text": False,
                },
            }
        )
        latency = time.time() - start
        call = output[0]["generated_text"].replace("Call:", "").strip()
        return call, {"input_tokens": 0, "output_tokens": 0, "latency": latency}

    def inference(self, prompt, functions, test_category):
        prompt = augment_prompt_by_languge(prompt, test_category)
        functions = language_specific_pre_processing(functions, test_category, False)
        raven_prompt = self._format_raven_function(prompt, functions)
        result, metadata = self._query_raven(raven_prompt)
        return result, metadata

    def decode_ast(self, result, language="Python"):
        if result.endswith(";"):
            result = result[:-1]
        result = result.replace(";", ",")
        func = "[" + result + "]"
        decoded_output = ast_parse(func, language)
        return decoded_output

    def decode_execute(self, result):
        if result.endswith(";"):
            result = result[:-1]
        result = result.replace(";", ",")
        func = "[" + result + "]"
        decoded_output = ast_parse(func)
        execution_list = []
        for function_call in decoded_output:
            for key, value in function_call.items():
                execution_list.append(
                    f"{key}({','.join([f'{k}={repr(v)}' for k, v in value.items()])})"
                )
        return execution_list
