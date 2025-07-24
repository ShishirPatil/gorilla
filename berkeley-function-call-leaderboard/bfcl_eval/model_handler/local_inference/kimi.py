from bfcl_eval.model_handler.local_inference.base_oss_handler import OSSHandler
from bfcl_eval.model_handler.utils import (
    combine_consecutive_user_prompts,
    func_doc_language_specific_pre_processing,
    system_prompt_pre_processing_chat_model,
)
from overrides import override


class KimiHandler(OSSHandler):
    """Local inference for Kimi models."""
    def __init__(self, model_name: str, temperature: float) -> None:
        super().__init__(model_name, temperature)

        self.max_context_length = 128000 # 128k context length from HF
        # recommended temperature from HF
        if self.temperature is None or self.temperature == 0.001:
            self.temperature = 0.6

