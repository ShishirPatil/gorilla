from typing import Any
import os
import time

from bfcl.model_handler.model_style import ModelStyle
from bfcl.model_handler.api_inference.openai import OpenAIHandler
from openai import OpenAI


class FireworksHandler(OpenAIHandler):
    """
    A handler class for interacting with Fireworks AI's API, extending OpenAIHandler for compatibility with OpenAI-style API calls. This class provides methods for sending queries, processing responses, and managing conversation history with Fireworks AI models.
    """
    def __init__(self, model_name: str, temperature: float) -> None:
        super().__init__(model_name, temperature)
        self.model_style = ModelStyle.FIREWORK_AI

        self.client = OpenAI(
            base_url="https://api.fireworks.ai/inference/v1",
            api_key=os.getenv("FIREWORKS_API_KEY"),
        )

    #### FC methods ####

    def _query_FC(self, inference_data: dict) -> tuple[Any, float]:
        """
        Sends a query to the Fireworks AI API and returns the response along with execution time.
        
        Args:
            inference_data (`dict`): Dictionary containing the message and tools for the API call.
        
        Returns:
            `tuple[Any, float]`: A tuple containing the API response and the execution time in seconds.
        """
        message: list[dict] = inference_data["message"]
        tools = inference_data["tools"]
        inference_data["inference_input_log"] = {"message": message, "tools": tools}

        start_time = time.time()
        if len(tools) > 0:
            api_response = self.client.chat.completions.create(
                messages=message,
                model=f"accounts/fireworks/models/{self.model_name.replace('-FC', '')}",
                temperature=self.temperature,
                tools=tools,
            )
        else:
            api_response = self.client.chat.completions.create(
                messages=message,
                model=f"accounts/fireworks/models/{self.model_name.replace('-FC', '')}",
                temperature=self.temperature,
            )
        end_time = time.time()

        return api_response, end_time - start_time

    def _pre_query_processing_FC(self, inference_data: dict, test_entry: dict) -> dict:
        """
        Pre-processes the inference data before sending to the API. Inherits behavior from OpenAIHandler.
        
        Args:
            inference_data (`dict`): Dictionary containing inference parameters.
            test_entry (`dict`): Test data entry for processing.
        
        Returns:
            `dict`: Processed inference data.
        """
        return super()._pre_query_processing_FC(inference_data, test_entry)

    def _compile_tools(self, inference_data: dict, test_entry: dict) -> dict:
        """
        Compiles tools for function calling. Inherits behavior from OpenAIHandler.
        
        Args:
            inference_data (`dict`): Dictionary containing inference parameters.
            test_entry (`dict`): Test data entry for processing.
        
        Returns:
            `dict`: Inference data with compiled tools.
        """
        return super()._compile_tools(inference_data, test_entry)

    def _parse_query_response_FC(self, api_response: any) -> dict:
        """
        Parses the response from Fireworks AI API into a standardized format.
        
        Args:
            api_response (`Any`): The raw API response from Fireworks AI.
        
        Returns:
            `dict`: Parsed response containing model responses, token usage, and chat history data.
        """
        try:
            model_responses = [
                {func_call.function.name: func_call.function.arguments}
                for func_call in api_response.choices[0].message.tool_calls
            ]
            tool_calls = [
                tool_call.model_dump()
                for tool_call in api_response.choices[0].message.tool_calls
            ]
        except:
            model_responses = api_response.choices[0].message.content
            tool_calls = []

        return {
            "model_responses": model_responses,
            "model_responses_message_for_chat_history": tool_calls,
            "input_token": api_response.usage.prompt_tokens,
            "output_token": api_response.usage.completion_tokens,
        }

    def add_first_turn_message_FC(
        self, inference_data: dict, first_turn_message: list[dict]
    ) -> dict:
        """
        Adds the initial message to start a conversation. Inherits behavior from OpenAIHandler.
        
        Args:
            inference_data (`dict`): Dictionary containing inference parameters.
            first_turn_message (`list[dict]`): Initial message to start the conversation.
        
        Returns:
            `dict`: Updated inference data with initial message.
        """
        return super().add_first_turn_message_FC(inference_data, first_turn_message)

    def _add_next_turn_user_message_FC(
        self, inference_data: dict, user_message: list[dict]
    ) -> dict:
        """
        Adds a user message to continue the conversation. Inherits behavior from OpenAIHandler.
        
        Args:
            inference_data (`dict`): Dictionary containing inference parameters.
            user_message (`list[dict]`): User message to add to the conversation.
        
        Returns:
            `dict`: Updated inference data with user message.
        """
        return super()._add_next_turn_user_message_FC(inference_data, user_message)

    def _add_assistant_message_FC(
        self, inference_data: dict, model_response_data: dict
    ) -> dict:
        """
        Adds an assistant message to the conversation history.
        
        Args:
            inference_data (`dict`): Dictionary containing inference parameters.
            model_response_data (`dict`): Contains the assistant's response data.
        
        Returns:
            `dict`: Updated inference data with assistant message.
        """
        inference_data["message"].append(
            {
                "role": "assistant",
                "content": "",
                "tool_calls": model_response_data[
                    "model_responses_message_for_chat_history"
                ],
            }
        )
        return inference_data

    def _add_execution_results_FC(
        self, inference_data: dict, execution_results: list[str], model_response_data: dict
    ) -> dict:
        """
        Adds tool execution results to the conversation history.
        
        Args:
            inference_data (`dict`): Dictionary containing inference parameters.
            execution_results (`list[str]`): Results from tool executions.
            model_response_data (`dict`): Contains model response data.
        
        Returns:
            `dict`: Updated inference data with execution results.
        """
        # Fireworks don’t support parallel and nested function calling, but we still support the code logic here for future use
        for execution_result in execution_results:
            tool_message = {
                "role": "tool",
                "content": execution_result,
            }
            inference_data["message"].append(tool_message)

        return inference_data
