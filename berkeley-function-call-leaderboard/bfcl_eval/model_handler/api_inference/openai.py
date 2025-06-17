from typing import Any
import json
import os
import time

from bfcl_eval.model_handler.base_handler import BaseHandler
from bfcl_eval.constants.type_mappings import GORILLA_TO_OPENAPI
from bfcl_eval.model_handler.model_style import ModelStyle
from bfcl_eval.model_handler.utils import (
    convert_to_function_call,
    convert_to_tool,
    default_decode_ast_prompting,
    default_decode_execute_prompting,
    format_execution_results_prompting,
    func_doc_language_specific_pre_processing,
    retry_with_backoff,
    system_prompt_pre_processing_chat_model,
)
from openai import OpenAI, RateLimitError


class OpenAIHandler(BaseHandler):
    """
    A handler class for interacting with OpenAI models, providing functionality for both function calling and prompting-based approaches. This class inherits from BaseHandler and implements methods specific to OpenAI's API.
    """
    def __init__(self, model_name: str, temperature: float) -> None:
        super().__init__(model_name, temperature)
        self.model_style = ModelStyle.OpenAI
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def decode_ast(self, result: list[dict] | str, language: str="Python") -> list[dict]:
        """
        Decodes the abstract syntax tree (AST) from the model's output. Handles both function calling and prompting-based outputs differently.
        
        Args:
            result (list[dict] | str): The raw output from the model to be decoded
            language (str): The programming language of the output (default: 'Python')
        
        Returns:
            list[dict]: The decoded AST representation
        """
        if "FC" in self.model_name or self.is_fc_model:
            decoded_output = []
            for invoked_function in result:
                name = list(invoked_function.keys())[0]
                params = json.loads(invoked_function[name])
                decoded_output.append({name: params})
            return decoded_output
        else:
            return default_decode_ast_prompting(result, language)

    def decode_execute(self, result: list[dict] | str) -> list[dict]:
        """
        Decodes the execution output from the model's response.
        
        Args:
            result (list[dict] | str): The raw output from the model
        
        Returns:
            list[dict]: The decoded execution output
        """
        if "FC" in self.model_name or self.is_fc_model:
            return convert_to_function_call(result)
        else:
            return default_decode_execute_prompting(result)

    @retry_with_backoff(error_type=RateLimitError)
    def generate_with_backoff(self, **kwargs) -> tuple[Any, float]:
        """
        Wrapper for OpenAI API calls with automatic retry on rate limits.
        
        Args:
            **kwargs: Arguments to pass to the OpenAI API
        
        Returns:
            tuple[Any, float]: The API response and the time taken for the call
        """
        start_time = time.time()
        api_response = self.client.chat.completions.create(**kwargs)
        end_time = time.time()

        return api_response, end_time - start_time

    #### FC methods ####

    def _query_FC(self, inference_data: dict) -> tuple[Any, float]:
        """
        Handles the query for function calling mode.
        
        Args:
            inference_data (dict): Data needed for the inference
        
        Returns:
            tuple[Any, float]: The API response and the time taken
        """
        message: list[dict] = inference_data["message"]
        tools = inference_data["tools"]
        inference_data["inference_input_log"] = {"message": repr(message), "tools": tools}

        if len(tools) > 0:
            # Reasoning models don't support temperature parameter
            # Beta limitation: https://platform.openai.com/docs/guides/reasoning/beta-limitations
            if "o1" in self.model_name or "o3-mini" in self.model_name:
                return self.generate_with_backoff(
                    messages=message,
                    model=self.model_name.replace("-FC", ""),
                    tools=tools,
                )
            else:
                return self.generate_with_backoff(
                    messages=message,
                    model=self.model_name.replace("-FC", ""),
                    temperature=self.temperature,
                    tools=tools,
                )
        else:
            if "o1" in self.model_name or "o3-mini" in self.model_name:
                return self.generate_with_backoff(
                    messages=message,
                    model=self.model_name.replace("-FC", ""),
                )
            else:
                return self.generate_with_backoff(
                    messages=message,
                    model=self.model_name.replace("-FC", ""),
                    temperature=self.temperature,
                )

    def _pre_query_processing_FC(self, inference_data: dict, test_entry: dict) -> dict:
        """
        Pre-processes data before function calling query.
        
        Args:
            inference_data (dict): The inference data to process
            test_entry (dict): The test case data
        
        Returns:
            dict: Processed inference data
        """
        inference_data["message"] = []
        return inference_data

    def _compile_tools(self, inference_data: dict, test_entry: dict) -> dict:
        """
        Compiles function definitions into tools format for OpenAI API.
        
        Args:
            inference_data (dict): The inference data
            test_entry (dict): The test case data
        
        Returns:
            dict: Inference data with compiled tools
        """
        functions: list = test_entry["function"]
        test_category: str = test_entry["id"].rsplit("_", 1)[0]

        functions = func_doc_language_specific_pre_processing(functions, test_category)
        tools = convert_to_tool(functions, GORILLA_TO_OPENAPI, self.model_style)

        inference_data["tools"] = tools

        return inference_data

    def _parse_query_response_FC(self, api_response: any) -> dict:
        """
        Parses the response from a function calling query.
        
        Args:
            api_response (any): The raw API response
        
        Returns:
            dict: Parsed response data
        """
        try:
            model_responses = [
                {func_call.function.name: func_call.function.arguments}
                for func_call in api_response.choices[0].message.tool_calls
            ]
            tool_call_ids = [
                func_call.id for func_call in api_response.choices[0].message.tool_calls
            ]
        except:
            model_responses = api_response.choices[0].message.content
            tool_call_ids = []

        model_responses_message_for_chat_history = api_response.choices[0].message

        return {
            "model_responses": model_responses,
            "model_responses_message_for_chat_history": model_responses_message_for_chat_history,
            "tool_call_ids": tool_call_ids,
            "input_token": api_response.usage.prompt_tokens,
            "output_token": api_response.usage.completion_tokens,
        }

    def add_first_turn_message_FC(
        self, inference_data: dict, first_turn_message: list[dict]
    ) -> dict:
        """
        Adds the first turn message for function calling mode.
        
        Args:
            inference_data (dict): The inference data
            first_turn_message (list[dict]): The initial message
        
        Returns:
            dict: Updated inference data
        """
        inference_data["message"].extend(first_turn_message)
        return inference_data

    def _add_next_turn_user_message_FC(
        self, inference_data: dict, user_message: list[dict]
    ) -> dict:
        """
        Adds user message for next turn in function calling mode.
        
        Args:
            inference_data (dict): The inference data
            user_message (list[dict]): The user message
        
        Returns:
            dict: Updated inference data
        """
        inference_data["message"].extend(user_message)
        return inference_data

    def _add_assistant_message_FC(
        self, inference_data: dict, model_response_data: dict
    ) -> dict:
        """
        Adds assistant message in function calling mode.
        
        Args:
            inference_data (dict): The inference data
            model_response_data (dict): The model's response data
        
        Returns:
            dict: Updated inference data
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
        Adds execution results in function calling mode.
        
        Args:
            inference_data (dict): The inference data
            execution_results (list[str]): Results of function execution
            model_response_data (dict): The model's response data
        
        Returns:
            dict: Updated inference data
        """
        # Add the execution results to the current round result, one at a time
        for execution_result, tool_call_id in zip(
            execution_results, model_response_data["tool_call_ids"]
        ):
            tool_message = {
                "role": "tool",
                "content": execution_result,
                "tool_call_id": tool_call_id,
            }
            inference_data["message"].append(tool_message)

        return inference_data

    def _add_reasoning_content_if_available_FC(
        self, api_response: any, response_data: dict
    ) -> None:
        """
        OpenAI models don't show reasoning content in the api response,
        but many other models that use the OpenAI interface do, such as DeepSeek and Grok.
        This method is included here to avoid code duplication.

        These models often don't take reasoning content in the chat history for next turn.
        Thus, this method saves reasoning content to response_data (for local result file) if present in the response,
        but does not include it in the chat history.
        """
        # Original assistant message object (contains `reasoning_content` on DeepSeek).
        message = api_response.choices[0].message

        # Preserve tool_call information but strip the unsupported `reasoning_content` field before inserting into chat history.
        if getattr(message, "tool_calls", None):
            assistant_message = {
                "role": "assistant",
                "content": message.content,
                "tool_calls": [
                    {
                        "id": tool_call.id,
                        "type": tool_call.type,
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments,
                        },
                    }
                    for tool_call in message.tool_calls
                ],
            }
            response_data["model_responses_message_for_chat_history"] = assistant_message

        # If no tool_calls, we still need to strip reasoning_content.
        elif hasattr(message, "reasoning_content"):
            response_data["model_responses_message_for_chat_history"] = {
                "role": "assistant",
                "content": message.content,
            }

        # Capture the reasoning trace so it can be logged to the local result file.
        if hasattr(message, "reasoning_content"):
            response_data["reasoning_content"] = message.reasoning_content

    #### Prompting methods ####

    def _query_prompting(self, inference_data: dict) -> tuple[Any, float]:
        """
        Handles the query for prompting mode.
        
        Args:
            inference_data (dict): Data needed for the inference
        
        Returns:
            tuple[Any, float]: The API response and the time taken
        """
        inference_data["inference_input_log"] = {"message": repr(inference_data["message"])}

        # OpenAI reasoning models don't support temperature parameter
        # Beta limitation: https://platform.openai.com/docs/guides/reasoning/beta-limitations
        if "o1" in self.model_name or "o3-mini" in self.model_name:
            return self.generate_with_backoff(
                messages=inference_data["message"],
                model=self.model_name,
            )
        else:
            return self.generate_with_backoff(
                messages=inference_data["message"],
                model=self.model_name,
                temperature=self.temperature,
            )

    def _pre_query_processing_prompting(self, test_entry: dict) -> dict:
        """
        Pre-processes data before prompting query.
        
        Args:
            test_entry (dict): The test case data
        
        Returns:
            dict: Processed inference data
        """
        functions: list = test_entry["function"]
        test_category: str = test_entry["id"].rsplit("_", 1)[0]

        functions = func_doc_language_specific_pre_processing(functions, test_category)

        test_entry["question"][0] = system_prompt_pre_processing_chat_model(
            test_entry["question"][0], functions, test_category
        )

        return {"message": []}

    def _parse_query_response_prompting(self, api_response: any) -> dict:
        """
        Parses the response from a prompting query.
        
        Args:
            api_response (any): The raw API response
        
        Returns:
            dict: Parsed response data
        """
        return {
            "model_responses": api_response.choices[0].message.content,
            "model_responses_message_for_chat_history": api_response.choices[0].message,
            "input_token": api_response.usage.prompt_tokens,
            "output_token": api_response.usage.completion_tokens,
        }

    def add_first_turn_message_prompting(
        self, inference_data: dict, first_turn_message: list[dict]
    ) -> dict:
        """
        Adds the first turn message for prompting mode.
        
        Args:
            inference_data (dict): The inference data
            first_turn_message (list[dict]): The initial message
        
        Returns:
            dict: Updated inference data
        """
        inference_data["message"].extend(first_turn_message)
        return inference_data

    def _add_next_turn_user_message_prompting(
        self, inference_data: dict, user_message: list[dict]
    ) -> dict:
        """
        Adds user message for next turn in prompting mode.
        
        Args:
            inference_data (dict): The inference data
            user_message (list[dict]): The user message
        
        Returns:
            dict: Updated inference data
        """
        inference_data["message"].extend(user_message)
        return inference_data

    def _add_assistant_message_prompting(
        self, inference_data: dict, model_response_data: dict
    ) -> dict:
        """
        Adds assistant message in prompting mode.
        
        Args:
            inference_data (dict): The inference data
            model_response_data (dict): The model's response data
        
        Returns:
            dict: Updated inference data
        """
        inference_data["message"].append(
            model_response_data["model_responses_message_for_chat_history"]
        )
        return inference_data

    def _add_execution_results_prompting(
        self, inference_data: dict, execution_results: list[str], model_response_data: dict
    ) -> dict:
        """
        Adds execution results in prompting mode.
        
        Args:
            inference_data (dict): The inference data
            execution_results (list[str]): Results of execution
            model_response_data (dict): The model's response data
        
        Returns:
            dict: Updated inference data
        """
        formatted_results_message = format_execution_results_prompting(
            inference_data, execution_results, model_response_data
        )
        inference_data["message"].append(
            {"role": "user", "content": formatted_results_message}
        )

        return inference_data

    def _add_reasoning_content_if_available_prompting(
        self, api_response: any, response_data: dict
    ) -> None:
        """
        OpenAI models don't show reasoning content in the api response,
        but many other models that use the OpenAI interface do, such as DeepSeek and Grok.
        This method is included here to avoid code duplication.

        These models often don't take reasoning content in the chat history for next turn.
        Thus, this method saves reasoning content to response_data (for local result file) if present in the response,
        but does not include it in the chat history.
        """
        message = api_response.choices[0].message
        if hasattr(message, "reasoning_content"):
            response_data["reasoning_content"] = message.reasoning_content
            # Reasoning content should not be included in the chat history
            response_data["model_responses_message_for_chat_history"] = {
                "role": "assistant",
                "content": str(response_data["model_responses"]),
            }
