import os

from bfcl_eval.model_handler.api_inference.openai_completion import OpenAICompletionsHandler
from openai import OpenAI
from overrides import override
from typing import Any
import httpx


class GLMAPIHandler(OpenAICompletionsHandler):
    def __init__(self, model_name, temperature) -> None:
        super().__init__(model_name, temperature)
        self.client = OpenAI(
            api_key=os.getenv("GLM_API_KEY"),
            base_url="https://open.bigmodel.cn/api/paas/v4/",
            timeout=httpx.Timeout(timeout=300.0, connect=8.0)
        )
        self.is_fc_model = True
