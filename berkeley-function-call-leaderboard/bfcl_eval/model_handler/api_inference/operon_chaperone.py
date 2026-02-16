"""
Operon Chaperone Handler
========================

Wraps an OpenAI model in prompting mode with Operon's Chaperone cascade
for robust JSON repair in the decode step. The Chaperone cascade
(STRICT → EXTRACTION → REPAIR) recovers valid function calls from
malformed or wrapped LLM output.

See: https://github.com/coredipper/operon
"""
import json
import os
import re
import time
from typing import Any

from bfcl_eval.model_handler.base_handler import BaseHandler
from bfcl_eval.constants.enums import ModelStyle
from bfcl_eval.model_handler.utils import (
    convert_to_function_call,
    default_decode_ast_prompting,
    default_decode_execute_prompting,
    format_execution_results_prompting,
    retry_with_backoff,
    system_prompt_pre_processing_chat_model,
)
from openai import OpenAI, RateLimitError


# ---------------------------------------------------------------------------
# Chaperone-lite: self-contained JSON repair cascade
# Mirrors operon_ai/organelles/chaperone.py without requiring the package.
# ---------------------------------------------------------------------------

_JSON_REPAIRS = [
    (r',\s*}', '}'),
    (r',\s*]', ']'),
    (r"'([^']*)'(?=\s*:)", r'"\1"'),
    (r":\s*'([^']*)'", r': "\1"'),
    (r'(\{|,)\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":'),
    (r'\bNone\b', 'null'),
    (r'\bTrue\b', 'true'),
    (r'\bFalse\b', 'false'),
    (r':\s*undefined\b', ': null'),
    (r':\s*NaN\b', ': null'),
]

_EXTRACTION_PATTERNS = [
    r'```json\s*([\s\S]*?)\s*```',
    r'```\s*([\s\S]*?)\s*```',
    r'<json>([\s\S]*?)</json>',
]


def _cascade_parse(raw: str) -> Any | None:
    """Parse JSON with Chaperone cascade: strict → extract → repair."""
    raw = raw.strip()

    # STRICT
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # EXTRACTION
    for pattern in _EXTRACTION_PATTERNS:
        m = re.search(pattern, raw, re.MULTILINE | re.DOTALL)
        if m:
            try:
                return json.loads(m.group(1).strip())
            except json.JSONDecodeError:
                pass

    # REPAIR
    repaired = raw
    for pattern, replacement in _JSON_REPAIRS:
        repaired = re.sub(pattern, replacement, repaired)
    try:
        return json.loads(repaired)
    except json.JSONDecodeError:
        pass

    # REPAIR on extracted text
    for pattern in _EXTRACTION_PATTERNS:
        m = re.search(pattern, raw, re.MULTILINE | re.DOTALL)
        if m:
            extracted = m.group(1).strip()
            repaired = extracted
            for pat, repl in _JSON_REPAIRS:
                repaired = re.sub(pat, repl, repaired)
            try:
                return json.loads(repaired)
            except json.JSONDecodeError:
                pass

    return None


# ---------------------------------------------------------------------------
# Handler
# ---------------------------------------------------------------------------

class OpeornChaperoneHandler(BaseHandler):
    """
    Wraps an OpenAI-compatible model in prompting mode with Operon's
    Chaperone cascade for robust JSON repair in the decode step.

    The model generates function calls as plain text (prompting mode).
    The Chaperone cascade recovers valid JSON even when the model wraps
    output in markdown, uses single quotes, or has trailing commas.
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
        self.model_style = ModelStyle.OPENAI_COMPLETIONS
        self.client = OpenAI(**self._build_client_kwargs())

    def _build_client_kwargs(self):
        kwargs = {}
        if api_key := os.getenv("OPENAI_API_KEY"):
            kwargs["api_key"] = api_key
        if base_url := os.getenv("OPENAI_BASE_URL"):
            kwargs["base_url"] = base_url
        return kwargs

    # ----- decode with Chaperone cascade -----

    def decode_ast(self, result, language, has_tool_call_tag):
        """Decode model output using Chaperone cascade parsing.

        Falls back to default_decode_ast_prompting if cascade fails.
        """
        # result is a string from _parse_query_response_prompting
        if not isinstance(result, str):
            return default_decode_ast_prompting(str(result), language, has_tool_call_tag)

        parsed = _cascade_parse(result)
        if parsed is not None:
            # parsed is either a list or a single dict
            if isinstance(parsed, list):
                # Validate structure: list of dicts with func_name: {args}
                decoded = []
                for item in parsed:
                    if isinstance(item, dict):
                        decoded.append(item)
                if decoded:
                    return decoded

            elif isinstance(parsed, dict):
                return [parsed]

        # Fallback to default prompting decoder
        return default_decode_ast_prompting(result, language, has_tool_call_tag)

    def decode_execute(self, result, has_tool_call_tag):
        """Decode model output to executable function call strings."""
        if not isinstance(result, str):
            return default_decode_execute_prompting(str(result))

        parsed = _cascade_parse(result)
        if parsed is not None:
            if isinstance(parsed, list):
                decoded = []
                for item in parsed:
                    if isinstance(item, dict):
                        decoded.append(item)
                if decoded:
                    return convert_to_function_call(decoded)

            elif isinstance(parsed, dict):
                return convert_to_function_call([parsed])

        return default_decode_execute_prompting(result)

    # ----- API methods (prompting mode only) -----

    @retry_with_backoff(error_type=RateLimitError)
    def generate_with_backoff(self, **kwargs):
        start_time = time.time()
        api_response = self.client.chat.completions.create(**kwargs)
        end_time = time.time()
        return api_response, end_time - start_time

    #### Prompting methods ####

    def _query_prompting(self, inference_data: dict):
        inference_data["inference_input_log"] = {"message": repr(inference_data["message"])}
        return self.generate_with_backoff(
            messages=inference_data["message"],
            model=self.model_name,
            temperature=self.temperature,
            store=False,
        )

    def _pre_query_processing_prompting(self, test_entry: dict) -> dict:
        functions: list = test_entry["function"]
        test_entry_id: str = test_entry["id"]

        test_entry["question"][0] = system_prompt_pre_processing_chat_model(
            test_entry["question"][0], functions, test_entry_id
        )
        return {"message": []}

    def _parse_query_response_prompting(self, api_response: Any) -> dict:
        return {
            "model_responses": api_response.choices[0].message.content,
            "model_responses_message_for_chat_history": api_response.choices[0].message,
            "input_token": api_response.usage.prompt_tokens,
            "output_token": api_response.usage.completion_tokens,
        }

    def add_first_turn_message_prompting(
        self, inference_data: dict, first_turn_message: list[dict]
    ) -> dict:
        inference_data["message"].extend(first_turn_message)
        return inference_data

    def _add_next_turn_user_message_prompting(
        self, inference_data: dict, user_message: list[dict]
    ) -> dict:
        inference_data["message"].extend(user_message)
        return inference_data

    def _add_assistant_message_prompting(
        self, inference_data: dict, model_response_data: dict
    ) -> dict:
        inference_data["message"].append(
            model_response_data["model_responses_message_for_chat_history"]
        )
        return inference_data

    def _add_execution_results_prompting(
        self, inference_data: dict, execution_results: list[str], model_response_data: dict
    ) -> dict:
        formatted_results_message = format_execution_results_prompting(
            inference_data, execution_results, model_response_data
        )
        inference_data["message"].append(
            {"role": "user", "content": formatted_results_message}
        )
        return inference_data
