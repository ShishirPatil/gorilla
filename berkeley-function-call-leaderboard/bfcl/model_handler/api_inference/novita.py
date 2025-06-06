from typing import Any
import os

from bfcl.model_handler.api_inference.openai import OpenAIHandler
from bfcl.model_handler.model_style import ModelStyle
from openai import OpenAI


class NovitaHandler(OpenAIHandler):
    """
    A handler for interacting with Novita AI's API, extending the OpenAIHandler class. This class provides specific implementations for querying Novita AI models with both function calling and standard prompting approaches.
    """
    def __init__(self, model_name: str, temperature: float) -> None:
        super().__init__(model_name, temperature)
        self.model_style = ModelStyle.NOVITA_AI
        self.client = OpenAI(
            base_url="https://api.novita.ai/v3/openai",
            api_key=os.getenv("NOVITA_API_KEY"),
        )

    #### FC methods ####

    def _query_FC(self, inference_data: dict):
        """
        Handles function calling queries to the Novita AI API.
        
        Args:
            inference_data (`dict`):
                Dictionary containing the message and tools for the function call. Expected keys:
                - 'message': List of message dictionaries
                - 'tools': List of tool definitions for function calling
        
        Returns:
            The API response from Novita AI for the function calling request
        """
        message: list[dict] = inference_data["message"]
        tools = inference_data["tools"]
        inference_data["inference_input_log"] = {
            "message": repr(message),
            "tools": tools,
        }

        if len(tools) > 0:
            return self.generate_with_backoff(
                messages=message,
                model=self.model_name.replace("-FC", "").replace("-novita", ""),
                temperature=self.temperature,
                tools=tools,
            )
        else:

            return self.generate_with_backoff(
                messages=message,
                model=self.model_name.replace("-FC", "").replace("-novita", ""),
                temperature=self.temperature,
            )

    #### Prompting methods ####

    def _query_prompting(self, inference_data: dict):
        """
        Handles standard prompting queries to the Novita AI API.
        
        Args:
            inference_data (`dict`):
                Dictionary containing the message for the prompt. Expected key:
                - 'message': List of message dictionaries
        
        Returns:
            The API response from Novita AI for the standard prompt request
        """
        inference_data["inference_input_log"] = {"message": repr(inference_data["message"])}

        return self.generate_with_backoff(
            messages=inference_data["message"],
            model=self.model_name.replace("-novita", ""),
            temperature=self.temperature,
        )
