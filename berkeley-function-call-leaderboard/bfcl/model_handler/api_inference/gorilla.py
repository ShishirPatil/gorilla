import json
import time

import requests
from bfcl.model_handler.base_handler import BaseHandler
from bfcl.model_handler.model_style import ModelStyle
from bfcl.model_handler.utils import ast_parse


class GorillaHandler(BaseHandler):
    """
    Handler class for interacting with Gorilla models, specializing in function calling capabilities. Inherits from BaseHandler and implements specific methods for Gorilla model interactions.
    
    Args:
        model_name (str): Name of the Gorilla model to use
        temperature (float): Temperature parameter for model generation
    """
    def __init__(self, model_name: str, temperature: float) -> None:
        super().__init__(model_name, temperature)
        self.model_style = ModelStyle.Gorilla
        self.is_fc_model = True

    def decode_ast(self, result: str, language: str="Python") -> list[dict]:
        """
        Parses the model's output string into an abstract syntax tree (AST) representation.
        
        Args:
            result (str): The model's output string to parse
            language (str, optional): Programming language of the output (default: 'Python')
        
        Returns:
            list[dict]: Parsed function calls as dictionaries
        """
        func = "[" + result + "]"
        decoded_output = ast_parse(func, language)
        return decoded_output

    def decode_execute(self, result: str) -> list[str]:
        """
        Converts the model's output into executable function call strings.
        
        Args:
            result (str): The model's output string to parse
        
        Returns:
            list[str]: List of executable function call strings
        """
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
        Sends a function calling request to the Gorilla model API.
        
        Args:
            inference_data (dict): Contains message history and tools for the API call
        
        Returns:
            tuple[dict, float]: API response JSON and request duration in seconds
        """
        inference_data["inference_input_log"] = {
            "message": inference_data["message"],
            "tools": inference_data["tools"],
        }
        requestData = {
            "model": self.model_name,
            "messages": inference_data["message"],
            "functions": inference_data["tools"],
            "temperature": self.temperature,
        }
        url = "https://luigi.millennium.berkeley.edu:443/v1/chat/completions"

        start_time = time.time()
        api_response = requests.post(
            url,
            headers={
                "Content-Type": "application/json",
                "Authorization": "EMPTY",  # Hosted for free with ❤️ from UC Berkeley
            },
            data=json.dumps(requestData),
        )
        end_time = time.time()

        return api_response.json(), end_time - start_time

    def _pre_query_processing_FC(self, inference_data: dict, test_entry: dict) -> dict:
        """
        Prepares the message history before making an API call.
        
        Args:
            inference_data (dict): Current inference data state
            test_entry (dict): Test case data
        
        Returns:
            dict: Updated inference data with initialized message history
        """
        inference_data["message"] = []
        return inference_data

    def _compile_tools(self, inference_data: dict, test_entry: dict) -> dict:
        """
        Prepares the function/tools specification for the API call.
        
        Args:
            inference_data (dict): Current inference data state
            test_entry (dict): Test case data
        
        Returns:
            dict: Updated inference data with tools specification
        """
        # Gorilla OpenFunctions does not require any pre-processing
        inference_data["tools"] = test_entry["function"]

        return inference_data

    def _parse_query_response_FC(self, api_response: any) -> dict:
        """
        Processes the API response into a standardized format.
        
        Args:
            api_response (any): Raw API response
        
        Returns:
            dict: Parsed response containing model output and token counts
        """

        return {
            "model_responses": api_response["choices"][0]["message"]["content"],
            "input_token": api_response["usage"]["prompt_tokens"],
            "output_token": api_response["usage"]["completion_tokens"],
        }

    def add_first_turn_message_FC(
        self, inference_data: dict, first_turn_message: list[dict]
    ) -> dict:
        """
        Adds the initial system message to the conversation history.
        
        Args:
            inference_data (dict): Current inference data state
            first_turn_message (list[dict]): Initial system message(s)
        
        Returns:
            dict: Updated inference data with initial messages
        """
        inference_data["message"].extend(first_turn_message)
        return inference_data

    def _add_next_turn_user_message_FC(
        self, inference_data: dict, user_message: list[dict]
    ) -> dict:
        """
        Adds user messages to the conversation history.
        
        Args:
            inference_data (dict): Current inference data state
            user_message (list[dict]): User message(s) to add
        
        Returns:
            dict: Updated inference data with user messages
        """
        inference_data["message"].extend(user_message)
        return inference_data

    def _add_assistant_message_FC(
        self, inference_data: dict, model_response_data: dict
    ) -> dict:
        """
        Adds model responses to the conversation history.
        
        Args:
            inference_data (dict): Current inference data state
            model_response_data (dict): Model response to add
        
        Returns:
            dict: Updated inference data with model response
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
        Adds function execution results to the conversation history.
        
        Args:
            inference_data (dict): Current inference data state
            execution_results (list[str]): Results of function executions
            model_response_data (dict): Model response data
        
        Returns:
            dict: Updated inference data with execution results
        """
        for execution_result in execution_results:
            tool_message = {
                "role": "tool",
                "content": execution_result,
            }
            inference_data["message"].append(tool_message)

        return inference_data
