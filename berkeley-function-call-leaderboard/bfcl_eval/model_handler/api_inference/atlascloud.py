import os

from bfcl_eval.model_handler.api_inference.openai_completion import (
    OpenAICompletionsHandler,
)
from openai import OpenAI


class AtlasCloudHandler(OpenAICompletionsHandler):
    """Handler for open-weight models served through the Atlas Cloud gateway.

    Atlas Cloud exposes an OpenAI-compatible `/chat/completions` endpoint and
    the models registered below advertise native `tools` support, so both the
    FC and the prompting paths are inherited unchanged from
    `OpenAICompletionsHandler`; only the client needs to be re-pointed.
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
            base_url="https://api.atlascloud.ai/v1",
            api_key=os.getenv("ATLASCLOUD_API_KEY"),
        )
