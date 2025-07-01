import os

from bfcl_eval.model_handler.api_inference.openai import OpenAIHandler
from openai import OpenAI
from overrides import override


class GrokHandler(OpenAIHandler):
    """
    A handler for interacting with Grok API, extending OpenAIHandler with Grok-specific functionality.
    
    Args:
        model_name (`str`):
            Name of the Grok model to use
        temperature (`float`):
            Temperature parameter for model generation
    """
    def __init__(self, model_name: str, temperature: float) -> None:
        super().__init__(model_name, temperature)
        self.client = OpenAI(
            base_url="https://api.x.ai/v1",
            api_key=os.getenv("GROK_API_KEY"),
        )
        self.is_fc_model = "FC" in self.model_name

    @override
    def _parse_query_response_prompting(self, api_response: any) -> dict:
        """
        Parses the response from Grok API for prompting mode.
        
        Args:
            api_response (`any`):
                Raw response from Grok API
        
        Returns:
            `dict`: Parsed response data with added reasoning content if available
        """
        response_data = super()._parse_query_response_prompting(api_response)
        self._add_reasoning_content_if_available_prompting(api_response, response_data)
        return response_data

    @override
    def _parse_query_response_FC(self, api_response: any) -> dict:
        """
        Parses the response from Grok API for FC (function calling) mode.
        
        Args:
            api_response (`any`):
                Raw response from Grok API
        
        Returns:
            `dict`: Parsed response data with added reasoning content if available
        """
        response_data = super()._parse_query_response_FC(api_response)
        self._add_reasoning_content_if_available_prompting(api_response, response_data)
        return response_data
