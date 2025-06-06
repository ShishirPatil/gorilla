from typing import Any
import os

from bfcl.model_handler.api_inference.openai import OpenAIHandler
from bfcl.model_handler.model_style import ModelStyle
from openai import OpenAI
from overrides import override


class QwenAPIHandler(OpenAIHandler):
    """
    A handler for interacting with the Qwen API, which is compatible with OpenAI's API format. This class extends OpenAIHandler to provide specific functionality for Qwen models.
    
    Args:
        model_name (str): The name of the Qwen model to use.
        temperature (float): The temperature parameter for controlling randomness in generation.
    """
    def __init__(self, model_name: str, temperature: float) -> None:
        super().__init__(model_name, temperature)
        self.model_style = ModelStyle.OpenAI
        self.chat_history = []
        self.client = OpenAI(
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            api_key=os.getenv("QWEN_API_KEY"),
        )

    @override
    def _query_prompting(self, inference_data: dict):
        """
        Sends a prompt to the Qwen API and returns the streaming response.
        
        Args:
            inference_data (dict): A dictionary containing the message to send to the API.
            
        Returns:
            The streaming response from the Qwen API.
        """
        message: list[dict] = inference_data["message"]
        inference_data["inference_input_log"] = {"message": repr(message)}

        return self.generate_with_backoff(
            messages=inference_data["message"],
            model="qwq-32b",
            stream=True,
            stream_options={
                "include_usage": True
            },  # retrieving token usage for stream response
        )

    @override
    def _parse_query_response_prompting(self, api_response: any) -> dict:
        """
        Parses the streaming response from the Qwen API into a structured format.
        
        Args:
            api_response (any): The streaming response from the Qwen API.
            
        Returns:
            dict: A dictionary containing the model's response, reasoning content, and token usage information.
        """

        reasoning_content = ""
        answer_content = ""
        for chunk in api_response:
            if not chunk.choices:
                continue

            delta = chunk.choices[0].delta

            if hasattr(delta, "reasoning_content") and delta.reasoning_content is not None:
                reasoning_content += delta.reasoning_content

            if hasattr(delta, "content") and delta.content:
                answer_content += delta.content

        response_data = {
            "model_responses": answer_content,
            "model_responses_message_for_chat_history": {
                "role": "assistant",
                "content": answer_content,
            },
            "reasoning_content": reasoning_content,
            # chunk is the last chunk of the stream response
            "input_token": chunk.usage.prompt_tokens,
            "output_token": chunk.usage.completion_tokens,
        }

        return response_data
