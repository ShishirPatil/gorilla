import os

from bfcl_eval.model_handler.api_inference.openai_completion import OpenAICompletionsHandler
from openai import OpenAI


class VivoAPIHandler(OpenAICompletionsHandler):
    """
    Handler for vivo BlueLM models accessed via the vivo public API.
    The API is OpenAI-compatible and supports function calling.
    """

    def __init__(
        self,
        model_name,
        temperature,
        registry_name,
        is_fc_model,
        **kwargs,
    ) -> None:
        super().__init__(model_name, temperature, registry_name, is_fc_model, **kwargs)
        self.client = OpenAI(
            api_key=os.getenv("VIVO_API_KEY", ""),
            base_url="https://api-ai.vivo.com.cn/v1",
        )
