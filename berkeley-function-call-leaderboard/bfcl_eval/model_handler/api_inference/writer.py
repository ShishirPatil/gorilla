from typing import Any
import os
import time

from bfcl_eval.model_handler.model_style import ModelStyle
from bfcl_eval.model_handler.api_inference.openai import OpenAIHandler
from writerai import Writer


class WriterHandler(OpenAIHandler):
    """
    A handler class for interacting with Writer AI models. Inherits from OpenAIHandler and implements specific functionality for Writer's API.
    
    Args:
        model_name (`str`):
            The name of the Writer model to use.
        temperature (`float`):
            The temperature parameter for model generation (controls randomness).
    """
    def __init__(self, model_name: str, temperature: float) -> None:
        super().__init__(model_name, temperature)
        self.model_style = ModelStyle.WRITER
        self.client = Writer(api_key=os.getenv("WRITER_API_KEY"))
        self.is_fc_model = True

    #### FC methods ####

    def _query_FC(self, inference_data: dict) -> tuple[Any, float]:
        """
        Makes a function calling query to the Writer API.
        
        Args:
            inference_data (`dict`):
                Dictionary containing inference parameters including:
                - message: List of message dictionaries for the chat
                - tools: List of tools/functions available to the model
                - inference_input_log: Log of input data (auto-populated)
        
        Returns:
            `tuple[Any, float]`:
                A tuple containing:
                - The API response from Writer
                - The execution time in seconds
        """
        message: list[dict] = inference_data["message"]
        tools = inference_data["tools"]
        inference_data["inference_input_log"] = {"message": repr(message), "tools": tools}

        start_time = time.time()
        if len(tools) > 0:
            api_response = self.client.chat.chat(
                messages=message,
                model=self.model_name,
                temperature=self.temperature,
                tools=tools,
                tool_choice="auto",
            )
        else:
            api_response = self.client.chat.chat(
                messages=message,
                model=self.model_name,
                temperature=self.temperature,
            )
        end_time = time.time()

        return api_response, end_time - start_time
