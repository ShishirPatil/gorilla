from typing import Any
import os
import time

import boto3
from bfcl.model_handler.base_handler import BaseHandler
from bfcl.constants.type_mappings import GORILLA_TO_OPENAPI
from bfcl.model_handler.model_style import ModelStyle
from bfcl.model_handler.utils import (
    combine_consecutive_user_prompts,
    convert_to_function_call,
    convert_to_tool,
    extract_system_prompt,
    func_doc_language_specific_pre_processing,
    retry_with_backoff,
)


class NovaHandler(BaseHandler):
    """
    Handler for interacting with Amazon's Nova model through AWS Bedrock. This class provides methods for processing function calls, generating responses, and managing conversation history with the Nova model.
    """
    def __init__(self, model_name: str, temperature: float) -> None:
        super().__init__(model_name, temperature)
        self.model_style = ModelStyle.AMAZON
        self.is_fc_model = True
        self.client = boto3.client(
            service_name="bedrock-runtime",
            region_name="us-east-1",  # Currently only available in us-east-1
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        )

    def decode_ast(self, result, language: str="Python") -> list:
        """
        Decodes the abstract syntax tree (AST) from the model's response. Currently returns an empty list if the result is not a list.
        
        Args:
            result (Any): The result to decode
            language (str, optional): The programming language of the AST. Defaults to 'Python'.
        
        Returns:
            list: The decoded AST or empty list if input is invalid
        """
        if type(result) != list:
            return []
        return result

    def decode_execute(self, result) -> list:
        """
        Decodes the execution result from the model's response and converts it to a function call format.
        
        Args:
            result (Any): The result to decode
        
        Returns:
            list: The decoded function calls or empty list if input is invalid
        """
        if type(result) != list:
            return []
        return convert_to_function_call(result)

    @retry_with_backoff(error_message_pattern=r".*\(ThrottlingException\).*")
    def generate_with_backoff(self, **kwargs) -> tuple[dict, float]:
        """
        Generates a response from the Nova model with exponential backoff retry for throttling errors.
        
        Args:
            **kwargs: Arguments to pass to the model's converse method
        
        Returns:
            tuple[dict, float]: The API response and the time taken for the request
        """
        start_time = time.time()
        api_response = self.client.converse(**kwargs)
        end_time = time.time()

        return api_response, end_time - start_time

    #### FC methods ####

    def _query_FC(self, inference_data: dict) -> dict:
        """
        Sends a query to the Nova model for function calling.
        
        Args:
            inference_data (dict): Contains message, tools, and system prompt information
        
        Returns:
            dict: The API response from the model
        """
        message: list[dict] = inference_data["message"]
        tools = inference_data["tools"]

        if "system_prompt" in inference_data:
            system_prompt = inference_data["system_prompt"]
        else:
            system_prompt = []

        inference_data["inference_input_log"] = {
            "message": repr(message),
            "tools": tools,
            "system_prompt": system_prompt,
        }

        if len(tools) > 0:
            # toolConfig requires minimum number of 1 item.
            return self.generate_with_backoff(
                modelId=f"us.amazon.{self.model_name.replace('.', ':')}",
                messages=message,
                system=system_prompt,
                inferenceConfig={"temperature": self.temperature},
                toolConfig={"tools": tools},
            )
        else:
            return self.generate_with_backoff(
                modelId=f"us.amazon.{self.model_name.replace('.', ':')}",
                messages=message,
                system=system_prompt,
                inferenceConfig={"temperature": self.temperature},
            )

    def _pre_query_processing_FC(self, inference_data: dict, test_entry: dict) -> dict:
        """
        Pre-processes the test entry data before querying the model.
        
        Args:
            inference_data (dict): The inference data to populate
            test_entry (dict): The test data containing questions
        
        Returns:
            dict: Updated inference data with processed messages
        """
        for round_idx in range(len(test_entry["question"])):
            test_entry["question"][round_idx] = combine_consecutive_user_prompts(
                test_entry["question"][round_idx]
            )

        inference_data["message"] = []

        system_prompt = extract_system_prompt(test_entry["question"][0])
        if system_prompt:
            inference_data["system_prompt"] = [{"text": system_prompt}]

        return inference_data

    def _compile_tools(self, inference_data: dict, test_entry: dict) -> dict:
        """
        Compiles function definitions into tools format for the model.
        
        Args:
            inference_data (dict): The inference data to populate
            test_entry (dict): The test data containing function definitions
        
        Returns:
            dict: Updated inference data with compiled tools
        """
        functions: list = test_entry["function"]
        test_category: str = test_entry["id"].rsplit("_", 1)[0]

        functions = func_doc_language_specific_pre_processing(functions, test_category)
        tools = convert_to_tool(functions, GORILLA_TO_OPENAPI, self.model_style)

        inference_data["tools"] = tools

        return inference_data

    def _parse_query_response_FC(self, api_response: any) -> dict:
        """
        Parses the model's response for function calls.
        
        Args:
            api_response (any): The raw API response from the model
        
        Returns:
            dict: Parsed response containing model responses, chat history, and token counts
        """
        model_responses_message_for_chat_history = api_response["output"]["message"]

        if api_response["stopReason"] == "tool_use":
            model_responses = []
            tool_call_ids = []
            """
            Note: Not every response will have a toolUse, so we skip any content that does not have a toolUse
            Example API response:
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [
                        {"text": "`"},
                        {
                            "toolUse": {
                                "toolUseId": "tooluse_kF0BECcNSd6WITS9W4afbQ",
                                "name": "calculate_triangle_area",
                                "input": {"base": 10, "height": 5},
                            }
                        },
                        {"text": "`"},
                    ],
                }
            },
            """
            for func_call in api_response["output"]["message"]["content"]:
                if "toolUse" not in func_call:
                    continue

                func_call = func_call["toolUse"]
                func_name = func_call["name"]
                func_args = func_call["input"]
                model_responses.append({func_name: func_args})
                tool_call_ids.append(func_call["toolUseId"])

        else:
            model_responses = api_response["output"]["message"]["content"][0]["text"]
            tool_call_ids = []

        return {
            "model_responses": model_responses,
            "model_responses_message_for_chat_history": model_responses_message_for_chat_history,
            "tool_call_ids": tool_call_ids,
            "input_token": api_response["usage"]["inputTokens"],
            "output_token": api_response["usage"]["outputTokens"],
        }

    def add_first_turn_message_FC(
        self, inference_data: dict, first_turn_message: list[dict]
    ) -> dict:
        """
        Adds the first turn message to the conversation history.
        
        Args:
            inference_data (dict): The inference data to update
            first_turn_message (list[dict]): The initial message(s) to add
        
        Returns:
            dict: Updated inference data with first turn message
        """
        for message in first_turn_message:
            message["content"] = [{"text": message["content"]}]
        inference_data["message"].extend(first_turn_message)
        return inference_data

    def _add_next_turn_user_message_FC(
        self, inference_data: dict, user_message: list[dict]
    ) -> dict:
        """
        Adds a user message to the conversation history.
        
        Args:
            inference_data (dict): The inference data to update
            user_message (list[dict]): The user message(s) to add
        
        Returns:
            dict: Updated inference data with user message
        """
        for message in user_message:
            message["content"] = [{"text": message["content"]}]
        inference_data["message"].extend(user_message)
        return inference_data

    def _add_assistant_message_FC(
        self, inference_data: dict, model_response_data: dict
    ) -> dict:
        """
        Adds an assistant message to the conversation history.
        
        Args:
            inference_data (dict): The inference data to update
            model_response_data (dict): Contains the assistant's response
        
        Returns:
            dict: Updated inference data with assistant message
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
        Adds tool execution results to the conversation history.
        
        Args:
            inference_data (dict): The inference data to update
            execution_results (list[str]): Results from tool executions
            model_response_data (dict): Contains tool call IDs
        
        Returns:
            dict: Updated inference data with execution results
        """
        # Nova use the `user` role for the tool result message
        tool_message = {
            "role": "user",
            "content": [],
        }
        for execution_result, tool_call_id in zip(
            execution_results, model_response_data["tool_call_ids"]
        ):
            tool_message["content"].append(
                {
                    "toolResult": {
                        "toolUseId": tool_call_id,
                        # Nova models supports json or text content
                        # Our pipeline force execution results to be text for all models
                        # So we will just use text here to be consistent
                        "content": [{"text": execution_result}],
                    }
                }
            )

        inference_data["message"].append(tool_message)

        return inference_data
