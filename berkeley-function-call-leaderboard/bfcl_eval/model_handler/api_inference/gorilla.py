import json
import time

import requests
from bfcl_eval.model_handler.base_handler import BaseHandler
from bfcl_eval.model_handler.model_style import ModelStyle
from bfcl_eval.model_handler.utils import ast_parse


class GorillaHandler(BaseHandler):
    """
    Handler for interacting with Gorilla models, specifically designed for function calling capabilities. Inherits from BaseHandler and implements Gorilla-specific functionality.
    """
    def __init__(self, model_name: str, temperature: float) -> None:
        super().__init__(model_name, temperature)
        self.model_style = ModelStyle.Gorilla
        self.is_fc_model = True

    def decode_ast(self, result: str, language: str="Python") -> list[dict]:
        """
        Parses the model's output string into an abstract syntax tree (AST) representation of function calls.
        
        Args:
            result (str): The raw model output string to parse
            language (str, optional): Programming language of the output (default: 'Python')
        
        Returns:
            list[dict]: Parsed function calls as dictionaries
        """
        func = "[" + result + "]"
        decoded_output = ast_parse(func, language)
        return decoded_output

    def decode_execute(self, result: str) -> list[str]:
        """
        Converts parsed function calls into executable Python code strings.
        
        Args:
            result (str): The raw model output string to parse
        
        Returns:
            list[str]: Executable Python function call strings
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
        Sends a function calling request to the Gorilla API endpoint.
        
        Args:
            inference_data (dict): Contains message history and tool definitions
        
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
        Prepares message history for function calling request.
        
        Args:
            inference_data (dict): Current inference state
            test_entry (dict): Test case data
        
        Returns:
            dict: Updated inference data with initialized message list
        """
        inference_data["message"] = []
        return inference_data

    def _compile_tools(self, inference_data: dict, test_entry: dict) -> dict:
        """
        Prepares tool/function definitions for API request.
        
        Args:
            inference_data (dict): Current inference state
            test_entry (dict): Test case data
        
        Returns:
            dict: Updated inference data with tool definitions
        """
        # Gorilla OpenFunctions does not require any pre-processing
        inference_data["tools"] = test_entry["function"]

        return inference_data

    def _parse_query_response_FC(self, api_response: any) -> dict:
        """
        Extracts relevant data from API response.
        
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
        Adds initial system/user messages to conversation history.
        
        Args:
            inference_data (dict): Current inference state
            first_turn_message (list[dict]): Initial messages
        
        Returns:
            dict: Updated inference data
        """
        inference_data["message"].extend(first_turn_message)
        return inference_data

    def _add_next_turn_user_message_FC(
        self, inference_data: dict, user_message: list[dict]
    ) -> dict:
        """
        Adds user message to conversation history.
        
        Args:
            inference_data (dict): Current inference state
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
            inference_data (dict): Current inference state
            model_response_data (dict): Contains model response
        
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
        Adds tool execution results to conversation history.
        
        Args:
            inference_data (dict): Current inference state
            execution_results (list[str]): Results from tool executions
            model_response_data (dict): Contains model response
        
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
