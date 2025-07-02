import os

from bfcl_eval.model_handler.api_inference.openai_completion import OpenAICompletionsHandler
from openai import OpenAI
from overrides import override
from typing import Any


class GrokHandler(OpenAICompletionsHandler):
    def __init__(self, model_name, temperature) -> None:
        super().__init__(model_name, temperature)
        self.client = OpenAI(
            base_url="https://api.x.ai/v1",
            api_key=os.getenv("GROK_API_KEY"),
        )
        self.is_fc_model = "FC" in self.model_name

    @override
    def _parse_query_response_prompting(self, api_response: Any) -> dict:
        response_data = super()._parse_query_response_prompting(api_response)
        self._add_reasoning_content_if_available_prompting(api_response, response_data)
        return response_data

    @override
    def _parse_query_response_FC(self, api_response: Any) -> dict:
        response_data = super()._parse_query_response_FC(api_response)
        self._add_reasoning_content_if_available_prompting(api_response, response_data)
        return response_data
