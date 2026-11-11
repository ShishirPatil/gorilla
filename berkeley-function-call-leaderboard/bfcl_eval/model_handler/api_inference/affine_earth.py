import json
import os

from bfcl_eval.constants.enums import ModelStyle
from bfcl_eval.model_handler.api_inference.openai_completion import (
    OpenAICompletionsHandler,
)


class AffineEarthHandler(OpenAICompletionsHandler):
    def __init__(
        self,
        model_name,
        temperature,
        registry_name,
        is_fc_model,
        **kwargs,
    ) -> None:
        super().__init__(model_name, temperature, registry_name, is_fc_model, **kwargs)
        self.model_style = ModelStyle.OPENAI_COMPLETIONS

    def _build_client_kwargs(self):
        kwargs = {
            "base_url": os.getenv("AFFINE_BASE_URL")
            or os.getenv("OPENAI_BASE_URL")
            or "https://affine.earth/v1"
        }

        if api_key := (os.getenv("AFFINE_API_KEY") or os.getenv("OPENAI_API_KEY")):
            kwargs["api_key"] = api_key

        if headers_env := os.getenv("OPENAI_DEFAULT_HEADERS"):
            kwargs["default_headers"] = json.loads(headers_env)

        return kwargs
