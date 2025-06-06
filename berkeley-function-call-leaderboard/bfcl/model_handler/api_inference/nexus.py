from typing import Union
import time

import requests
from bfcl.model_handler.base_handler import BaseHandler
from bfcl.model_handler.model_style import ModelStyle
from bfcl.model_handler.utils import (
    ast_parse,
    func_doc_language_specific_pre_processing,
)


class NexusHandler(BaseHandler):
    """
    A handler class for interacting with the Nexus Raven model, implementing function calling capabilities and conversation management.
    """
    def __init__(self, model_name: str, temperature: float) -> None:
        super().__init__(model_name, temperature)
        self.model_style = ModelStyle.NEXUS
        self.is_fc_model = True

    @staticmethod
    def _generate_functions_from_dict(func_dicts: list[dict]) -> list[str]:
        """
        Generates formatted function descriptions from a list of function dictionaries for Nexus Raven model.
        
        Args:
            func_dicts (list[dict]): List of function dictionaries containing name, description and parameters
        
        Returns:
            list[str]: List of formatted function description strings
        """
        func_template = """
    Function:
    def {func_name}({func_args}) -> None:
        \"\"\"
        {description}

        Parameters:
        {param_descriptions}
        \"\"\"

    """

        functions = []
        for func_dict in func_dicts:
            func_name = func_dict["name"]
            description = func_dict["description"]
            parameters = func_dict["parameters"]["properties"]
            required_params = func_dict["parameters"].get("required", [])

            func_args_list = []
            param_descriptions = []

            for param, details in parameters.items():
                param_type = details["type"]
                if "enum" in details:
                    param_type = (
                        f"""String[{', '.join(f"'{e}'" for e in details['enum'])}]"""
                    )

                param_type = (
                    param_type.replace("string", "str")
                    .replace("number", "float")
                    .replace("integer", "int")
                    .replace("object", "dict")
                    .replace("array", "list")
                    .replace("boolean", "bool")
                )

                type_hint = param_type

                if param in required_params:
                    func_args_list.append(f"{param}: {type_hint}")
                else:
                    func_args_list.append(f"{param}: {type_hint} = None")

                param_description = f"{param} ({param_type}): {details.get('description', 'No description available. Please make a good guess.')}"

                if "enum" in details:
                    param_description += f""". Choose one of {', '.join(f"'{e}'" for e in details['enum'])}."""

                if param not in required_params:
                    param_description += " (Optional)"
                param_descriptions.append(param_description)

            func_args = ", ".join(func_args_list)
            param_descriptions_str = "\n    ".join(param_descriptions)

            function_str = func_template.format(
                func_name=func_name,
                func_args=func_args,
                description=description,
                param_descriptions=param_descriptions_str,
            )

            functions.append(function_str)

        functions.append(
            '''
    Function:
    def out_of_domain(user_query: str) -> str:
        """
        This function is designed to handle out-of-domain queries from the user.
        If the user provides any input user query that is out of the domain of the other APIs provided above,
        this function should be used with the input user query as the string.

        - user_query (str): The input string that is out of domain.

        Returns nothing.
        """

            '''
        )

        return functions

    def _format_raven_function(self, user_prompts: list[dict[str, str]], functions: list[str]) -> str:
        """
        Nexus-Raven requires a specific format for the function description.
        This function formats the function description in the required format.
        """
        raven_prompt = "\n".join(functions) + "\n\n"
        raven_prompt += "Setting: Allowed to issue multiple calls with semicolon\n"
        for user_prompt in user_prompts:
            raven_prompt += f"{user_prompt['role']}: {user_prompt['content']}\n"

        raven_prompt += f"<human_end>"

        return raven_prompt

    def decode_ast(self, result: str, language: str="Python") -> Union[list[dict], str]:
        """
        Decodes the model's function call output into abstract syntax tree format.
        
        Args:
            result (str): Raw model output string
            language (str): Programming language of output (default: "Python")
        
        Returns:
            Union[list[dict], str]: Parsed function calls or 'irrelevant' if out of domain
        """
        if result.endswith(";"):
            result = result[:-1]
        result = result.replace(";", ",")
        func = "[" + result + "]"
        decoded_output = ast_parse(func, language)
        if "out_of_domain" in result:
            return "irrelevant"

        return decoded_output

    def decode_execute(self, result: str) -> list[str]:
        """
        Decodes the model's function call output into executable function call strings.
        
        Args:
            result (str): Raw model output string
        
        Returns:
            list[str]: List of executable function call strings
        """
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

    #### FC methods ####

    def _query_FC(self, inference_data: dict) -> tuple[dict, float]:
        """
        Sends query to Nexus Raven API and returns response.
        
        Args:
            inference_data (dict): Data containing messages and tools for the query
        
        Returns:
            tuple[dict, float]: API response and execution time
        """
        API_URL = "http://nexusraven.nexusflow.ai"
        headers = {"Content-Type": "application/json"}
        prompt = self._format_raven_function(
            inference_data["message"], inference_data["tools"]
        )
        payload = {
            "inputs": prompt,
            "parameters": {
                "temperature": self.temperature,
                "stop": ["<bot_end>"],
                "do_sample": False,
                "return_full_text": False,
            },
        }
        start_time = time.time()
        api_response = requests.post(
            "http://nexusraven.nexusflow.ai", headers=headers, json=payload
        )
        end_time = time.time()

        return api_response.json(), end_time - start_time

    def _pre_query_processing_FC(self, inference_data: dict, test_entry: dict) -> dict:
        """
        Prepares inference data before sending to model.
        
        Args:
            inference_data (dict): Initial inference data
            test_entry (dict): Test case data
        
        Returns:
            dict: Processed inference data
        """
        inference_data["message"] = []
        return inference_data

    def _compile_tools(self, inference_data: dict, test_entry: dict) -> dict:
        """
        Compiles and formats function tools for Nexus Raven model.
        
        Args:
            inference_data (dict): Inference data container
            test_entry (dict): Test case containing function definitions
        
        Returns:
            dict: Inference data with compiled tools
        """
        functions: list = test_entry["function"]
        test_category: str = test_entry["id"].rsplit("_", 1)[0]

        functions = func_doc_language_specific_pre_processing(functions, test_category)
        # Nexus requires functions to be in a specific format
        inference_data["tools"] = self._generate_functions_from_dict(functions)

        return inference_data

    def _parse_query_response_FC(self, api_response: any) -> dict:
        """
        Parses the raw API response into standardized format.
        
        Args:
            api_response (any): Raw API response
        
        Returns:
            dict: Parsed response containing model output
        """
        return {
            "model_responses": api_response[0]["generated_text"]
            .replace("Call:", "")
            .strip(),
            "input_token": "N/A",
            "output_token": "N/A",
        }

    def add_first_turn_message_FC(
        self, inference_data: dict, first_turn_message: list[dict]
    ) -> dict:
        """
        Adds initial conversation message to inference data.
        
        Args:
            inference_data (dict): Inference data container
            first_turn_message (list[dict]): Initial message(s)
        
        Returns:
            dict: Updated inference data
        """
        inference_data["message"].extend(first_turn_message)
        return inference_data

    def _add_next_turn_user_message_FC(
        self, inference_data: dict, user_message: list[dict]
    ) -> dict:
        """
        Adds user message to ongoing conversation.
        
        Args:
            inference_data (dict): Inference data container
            user_message (list[dict]): User message(s)
        
        Returns:
            dict: Updated inference data
        """
        inference_data["message"].extend(user_message)
        return inference_data

    def _add_assistant_message_FC(
        self, inference_data: dict, model_response_data: dict
    ) -> dict:
        """
        Adds assistant response to conversation history.
        
        Args:
            inference_data (dict): Inference data container
            model_response_data (dict): Model response data
        
        Returns:
            dict: Updated inference data
        """
        inference_data["message"].append(
            {
                "role": "assistant",
                "content": model_response_data["model_responses"],
            }
        )
        return inference_data

    def _add_execution_results_FC(
        self, inference_data: dict, execution_results: list[str], model_response_data: dict
    ) -> dict:
        """
        Adds function execution results to conversation history.
        
        Args:
            inference_data (dict): Inference data container
            execution_results (list[str]): Results from function executions
            model_response_data (dict): Model response data
        
        Returns:
            dict: Updated inference data
        """
        for execution_result in execution_results:
            tool_message = {
                "role": "tool",
                "content": execution_result,
            }
            inference_data["message"].append(tool_message)

        return inference_data
