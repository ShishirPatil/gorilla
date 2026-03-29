"""
AIREV-Agent-0.8B Handler for BFCL Official Evaluation.

KEY LEARNINGS:
- DO NOT override BFCL's system prompt. _pre_query_processing_prompting already
  calls system_prompt_pre_processing_chat_model which adds the correct prompt.
- DO activate <think> mode by appending <think>\n to the prompt.
- DO use default_decode_ast_prompting (BFCL's own decoder).
- The model outputs func_name(param=value) which BFCL's decoder handles.
"""
import json
import re
from typing import Any
from bfcl_eval.model_handler.local_inference.base_oss_handler import OSSHandler
from bfcl_eval.model_handler.utils import (
    default_decode_ast_prompting,
    default_decode_execute_prompting,
)
from overrides import override


class AIREVAgentHandler(OSSHandler):
    def __init__(self, model_name, temperature, registry_name, is_fc_model, dtype="bfloat16", **kwargs):
        super().__init__(model_name, temperature, registry_name, is_fc_model, **kwargs)

    @override
    def _format_prompt(self, messages, function):
        """
        Build prompt from the ALREADY-PREPROCESSED messages.
        DO NOT add our own system prompt — BFCL already added theirs
        via system_prompt_pre_processing_chat_model in _pre_query_processing_prompting.
        Just format as chat template and activate <think>.
        """
        prompt = ""
        for m in messages:
            role = m.get("role", "user")
            content = m.get("content", "")
            prompt += "<|im_start|>" + role + "\n" + content + "<|im_end|>\n"
        # Activate thinking mode
        prompt += "<|im_start|>assistant\n<think>\n"
        return prompt

    @override
    def _parse_query_response_prompting(self, api_response: Any) -> dict:
        """Strip <think> tags from the response before passing to decoder."""
        text = api_response.choices[0].text
        # Strip thinking — evaluator only wants the function call
        if "</think>" in text:
            text = text.split("</think>")[-1].strip()
        return {
            "model_responses": text,
            "input_token": api_response.usage.prompt_tokens,
            "output_token": api_response.usage.completion_tokens,
        }

    @override
    def decode_ast(self, result, language, has_tool_call_tag):
        """Use BFCL's own default decoder."""
        # Strip thinking if still present
        if isinstance(result, str) and "</think>" in result:
            result = result.split("</think>")[-1].strip()
        return default_decode_ast_prompting(result, language, has_tool_call_tag)

    @override
    def decode_execute(self, result, has_tool_call_tag):
        """Use BFCL's own default decoder."""
        if isinstance(result, str) and "</think>" in result:
            result = result.split("</think>")[-1].strip()
        return default_decode_execute_prompting(result, has_tool_call_tag)
