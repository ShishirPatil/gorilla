from typing import Any
import json
import os
import time

from bfcl.model_handler.base_handler import BaseHandler
from bfcl.constants.type_mappings import GORILLA_TO_OPENAPI
from bfcl.model_handler.model_style import ModelStyle
from bfcl.model_handler.utils import (
    convert_to_function_call,
    convert_to_tool,
    func_doc_language_specific_pre_processing,
)
from openai import OpenAI


class YiHandler(BaseHandler):
    """
    A handler class for interacting with the Yi API, extending BaseHandler. This class provides methods for processing and managing API calls to the Yi language model, including function calling capabilities.
    """
    def __init__(self, model_name: str, temperature: float) -> None:
        super().__init__(model_name, temperature)
        self.model_style = ModelStyle.OpenAI
        self.base_url = "https://api.01.ai/v1"
        self.client = OpenAI(base_url=self.base_url, api_key=os.getenv("YI_API_KEY"))

    def decode_ast(self, result: list[dict], language: str="Python") -> list[dict]:
        """
        Decodes the abstract syntax tree (AST) from the API response into a more usable dictionary format.
        
        Args:
            result (`list[dict]`): The raw API response containing function calls
            language (`str`, optional): The programming language of the functions (default: 'Python')
        
        Returns:
            `list[dict]`: A list of dictionaries with function names as keys and their parameters as values
        """
        decoded_output = []
        for invoked_function in result:
            name = list(invoked_function.keys())[0]
            params = json.loads(invoked_function[name])
            decoded_output.append({name: params})

        return decoded_output

    def decode_execute(self, result: dict) -> dict:
        """
        Converts the API response into a function call format.
        
        Args:
            result (`dict`): The raw API response
        
        Returns:
            `dict`: A dictionary representing the function call
        """
        function_call = convert_to_function_call(result)
        return function_call

    #### FC methods ####

    def _query_FC(self, inference_data: dict) -> tuple[Any, float]:
        """
        Makes an API call to the Yi model with function calling capabilities.
        
        Args:
            inference_data (`dict`): Contains the message and tools for the API call
        
        Returns:
            `tuple[Any, float]`: A tuple containing the API response and the execution time
        """
        message: list[dict] = inference_data["message"]
        tools = inference_data["tools"]
        inference_data["inference_input_log"] = {"message": repr(message), "tools": tools}

        start_time = time.time()
        if len(tools) > 0:
            api_response = self.client.chat.completions.create(
                messages=message,
                model=self.model_name.replace("-FC", ""),
                temperature=self.temperature,
                tools=tools,
            )
        else:
            api_response = self.client.chat.completions.create(
                messages=message,
                model=self.model_name.replace("-FC", ""),
                temperature=self.temperature,
            )
        end_time = time.time()

        return api_response, end_time - start_time

    def _pre_query_processing_FC(self, inference_data: dict, test_entry: dict) -> dict:
        """
        Prepares the inference data before making an API call.
        
        Args:
            inference_data (`dict`): The data to be processed
            test_entry (`dict`): Additional test data
        
        Returns:
            `dict`: The processed inference data
        """
        inference_data["message"] = []
        return inference_data

    def _compile_tools(self, inference_data: dict, test_entry: dict) -> dict:
        """
        Compiles function definitions into tools format for the API call.
        
        Args:
            inference_data (`dict`): The inference data to be updated
            test_entry (`dict`): Contains function definitions
        
        Returns:
            `dict`: The updated inference data with compiled tools
        """
        functions: list = test_entry["function"]
        test_category: str = test_entry["id"].rsplit("_", 1)[0]

        functions = func_doc_language_specific_pre_processing(functions, test_category)
        tools = convert_to_tool(functions, GORILLA_TO_OPENAPI, self.model_style)

        inference_data["tools"] = tools

        return inference_data

    def _parse_query_response_FC(self, api_response: any) -> dict:
        """
        Parses the API response from a function call request.
        
        Args:
            api_response (`Any`): The raw API response
        
        Returns:
            `dict`: A dictionary containing parsed response data including model responses, tokens used, etc.
        """
        try:
            model_responses = [
                {func_call.function.name: func_call.function.arguments}
                for func_call in api_response.choices[0].message.tool_calls
            ]
            tool_call_ids = [
                func_call.id for func_call in api_response.choices[0].message.tool_calls
            ]
            tool_call_func_names = [
                func_call.function.name
                for func_call in api_response.choices[0].message.tool_calls
            ]
        except:
            model_responses = api_response.choices[0].message.content
            tool_call_ids = []
            tool_call_func_names = []

        model_responses_message_for_chat_history = api_response.choices[0].message

        return {
            "model_responses": model_responses,
            "model_responses_message_for_chat_history": model_responses_message_for_chat_history,
            "tool_call_ids": tool_call_ids,
            "tool_call_func_names": tool_call_func_names,
            "input_token": api_response.usage.prompt_tokens,
            "output_token": api_response.usage.completion_tokens,
        }

    def add_first_turn_message_FC(
        self, inference_data: dict, first_turn_message: list[dict]
    ) -> dict:
        """
        Adds the initial message to the conversation history.
        
        Args:
            inference_data (`dict`): The inference data to update
            first_turn_message (`list[dict]`): The initial message(s) to add
        
        Returns:
            `dict`: The updated inference data
        """
        inference_data["message"].extend(first_turn_message)
        return inference_data

    def _add_next_turn_user_message_FC(
        self, inference_data: dict, user_message: list[dict]
    ) -> dict:
        """
        Adds a user message to the conversation history.
        
        Args:
            inference_data (`dict`): The inference data to update
            user_message (`list[dict]`): The user message(s) to add
        
        Returns:
            `dict`: The updated inference data
        """
        inference_data["message"].extend(user_message)
        return inference_data

    def _add_assistant_message_FC(
        self, inference_data: dict, model_response_data: dict
    ) -> dict:
        """
        Adds an assistant message to the conversation history.
        
        Args:
            inference_data (`dict`): The inference data to update
            model_response_data (`dict`): Contains the assistant's response
        
        Returns:
            `dict`: The updated inference data
        """
        inference_data["message"].append(
            model_response_data["model_responses_message_for_chat_history"]
        )
        return inference_data

    def _add_execution_results_FC(
        self,
        inference_data: dict,
        execution_results: list[str],
        model_response_data: dict,
    ) -> dict:
        """
        Adds execution results of function calls to the conversation history.
        
        Args:
            inference_data (`dict`): The inference data to update
            execution_results (`list[str]`): Results of function executions
            model_response_data (`dict`): Contains tool call information
        
        Returns:
            `dict`: The updated inference data
        """
        # Add the execution results to the current round result, one at a time
        for execution_result, tool_call_id, tool_call_func_name in zip(
            execution_results,
            model_response_data["tool_call_ids"],
            model_response_data["tool_call_func_names"],
        ):
            tool_message = {
                "tool_call_id": tool_call_id,
                "role": "tool",
                "name": tool_call_func_name,
                "content": execution_result,
            }
            inference_data["message"].append(tool_message)

        return inference_data
