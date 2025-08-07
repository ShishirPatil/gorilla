"""
Gemma Model Handler for Google AI Studio API

This handler is specifically designed for Gemma models which don't support system instructions
and thinking features in Google AI Studio. It converts system prompts to user prompts and
removes thinking configuration.
"""

from google.genai.types import GenerateContentConfig

from bfcl_eval.model_handler.api_inference.gemini import GeminiHandler
from bfcl_eval.model_handler.utils import (
    convert_system_prompt_into_user_prompt,
    func_doc_language_specific_pre_processing,
    system_prompt_pre_processing_chat_model,
)
from overrides import override


class GemmaHandler(GeminiHandler):
    """
    Handler for Gemma models via Google AI Studio API.
    
    Gemma models are prompting-only models that don't support:
    - System instructions (converted to user prompts)
    - Thinking features (removed from API calls)
    """

    def __init__(self, model_name, temperature):
        super().__init__(model_name, temperature)

    @override
    def _query_prompting(self, inference_data: dict):
        """Override to remove thinking_config for Gemma models"""
        
        inference_data["inference_input_log"] = {
            "message": repr(inference_data["message"]),
            "system_prompt": inference_data.get("system_prompt", None),
        }

        # Create config without thinking_config (Gemma doesn't support it)
        config = GenerateContentConfig(
            temperature=self.temperature,
            # Note: No thinking_config for Gemma models
        )


        api_response = self.generate_with_backoff(
            model=self.model_name.replace("-FC", ""),
            contents=inference_data["message"],
            config=config,
        )

        return api_response

    @override
    def _pre_query_processing_prompting(self, test_entry: dict) -> dict:
        functions: list = test_entry["function"]
        test_category: str = test_entry["id"].rsplit("_", 1)[0]

        functions = func_doc_language_specific_pre_processing(functions, test_category)

        for round_idx in range(len(test_entry["question"])):
            test_entry["question"][round_idx] = self._substitute_prompt_role(
                test_entry["question"][round_idx]
            )

        test_entry["question"][0] = system_prompt_pre_processing_chat_model(
            test_entry["question"][0], functions, test_category
        )
        
        # Gemma models don't support system instructions, convert to user prompt
        for round_idx in range(len(test_entry["question"])):
            test_entry["question"][round_idx] = convert_system_prompt_into_user_prompt(
                test_entry["question"][round_idx]
            )
        
        return {"message": []} 