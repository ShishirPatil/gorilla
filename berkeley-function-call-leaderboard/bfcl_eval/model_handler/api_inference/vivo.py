import json
import os

from bfcl_eval.model_handler.api_inference.openai_completion import OpenAICompletionsHandler
from openai import OpenAI
from overrides import override
from typing import Any
from bfcl_eval.model_handler.model_style import ModelStyle


class VivoAPIHandler(OpenAICompletionsHandler):
    """
    Handler for vivo BlueLM models accessed via the vivo public API.
    The API is OpenAI-compatible and supports function calling.
    """

    def __init__(self, model_name, temperature) -> None:
        super().__init__(model_name, temperature)
        self.model_style = ModelStyle.OpenAI
        self.client = OpenAI(
            api_key=os.getenv("VIVO_API_KEY", ""),
            base_url="https://api-ai.vivo.com.cn/v1"
        )
        self.is_fc_model = True

    @override
    def _parse_query_response_FC(self, api_response: Any) -> dict:
        try:
            model_responses = [
                {func_call.function.name: func_call.function.arguments}
                for func_call in api_response.choices[0].message.tool_calls
            ]
            tool_call_ids = [
                func_call.id for func_call in api_response.choices[0].message.tool_calls
            ]
            if len(model_responses) == 0:
                model_responses = api_response.choices[0].message.content
        except:
            model_responses = api_response.choices[0].message.content
            tool_call_ids = []

        model_responses_message_for_chat_history = api_response.choices[0].message.__dict__
        if model_responses_message_for_chat_history.get("tool_calls", None):
            model_responses_message_for_chat_history["tool_calls"] = [
                {
                    "id": tool_call.id,
                    "type": "function",
                    "function": tool_call.function.__dict__,
                }
                for tool_call in model_responses_message_for_chat_history["tool_calls"]
            ]

        return {
            "model_responses": model_responses,
            "model_responses_message_for_chat_history": model_responses_message_for_chat_history,
            "tool_call_ids": tool_call_ids,
            "input_token": api_response.usage.prompt_tokens,
            "output_token": api_response.usage.completion_tokens,
        }
