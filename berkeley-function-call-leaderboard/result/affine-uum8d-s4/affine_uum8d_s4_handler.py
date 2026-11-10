# Affine.Earth Sovereign S4xC4 Handler for Berkeley Function Calling Leaderboard (BFCL V4)
# Model ID: affine-uum8d-s4 · Seal: dfa59d960871
import os
from bfcl_eval.model_handler.api_inference.openai_completion import OpenAICompletionsHandler
from bfcl_eval.constants.enums import ModelStyle
from openai import OpenAI


class AffineUUM8DS4Handler(OpenAICompletionsHandler):
    def __init__(
        self,
        model_name,
        temperature,
        registry_name,
        is_fc_model,
        dtype="bfloat16",
        **kwargs,
    ) -> None:
        super().__init__(model_name, temperature, registry_name, is_fc_model, **kwargs)
        self.model_style = ModelStyle.OPENAI_COMPLETIONS
        self.client = OpenAI(
            base_url=os.getenv("AFFINE_BASE_URL", "https://affine.earth/v1"),
            api_key=os.getenv("AFFINE_API_KEY", "affine-public-eval-2026"),
        )
