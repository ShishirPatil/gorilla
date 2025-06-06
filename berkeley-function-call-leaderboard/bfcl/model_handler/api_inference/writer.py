from typing import Any
import os
import time

from bfcl.model_handler.model_style import ModelStyle
from bfcl.model_handler.api_inference.openai import OpenAIHandler
from writerai import Writer


class WriterHandler(OpenAIHandler):
    """
    A handler class for interacting with Writer AI models, extending OpenAIHandler functionality. This class provides specific implementations for Writer API calls and handles function calling capabilities.
    
    Args:
        model_name (`str`):
            The name of the Writer model to use for inference.
        temperature (`float`):
            The temperature parameter for controlling randomness in generation (0.0 to 1.0).
    """
    def __init__(self, model_name: str, temperature: float) -> None:
        super().__init__(model_name, temperature)
        self.model_style = ModelStyle.WRITER
        self.client = Writer(api_key=os.getenv("WRITER_API_KEY"))
        self.is_fc_model = True

    #### FC methods ####

    def _query_FC(self, inference_data: dict) -> tuple[Any, float]:
        """
        Executes a function calling query against the Writer API.
        
        Args:
            inference_data (`dict`):
                Dictionary containing inference parameters including:
                - message: List of message dictionaries for the chat context
                - tools: List of tool definitions for function calling
                - inference_input_log: Logging information
        
        Returns:
            `tuple[Any, float]`:
                A tuple containing:
                - The API response object
                - The execution time in seconds
        
        Note:
            This method automatically handles both regular chat queries and function calling queries based on the presence of tools.
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
