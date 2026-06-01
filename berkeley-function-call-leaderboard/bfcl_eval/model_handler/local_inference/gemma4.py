import re

from bfcl_eval.model_handler.local_inference.base_oss_handler import OSSHandler
from bfcl_eval.model_handler.utils import (
    combine_consecutive_user_prompts,
    default_decode_ast_prompting,
    default_decode_execute_prompting,
    system_prompt_pre_processing_chat_model,
)
from overrides import override


# Gemma 4 emits tool calls as: <|tool_call>call:func(args)<tool_call|>
# Asymmetric delimiters — opener has no trailing pipe, closer has no leading
# pipe. Multi-call responses concatenate back-to-back with no separator.
_GEMMA4_NATIVE_CALL_RE = re.compile(
    r"<\|tool_call>\s*(.*?)\s*<tool_call\|>",
    re.DOTALL,
)

# Top-level `key:` -> `key=` for the JSON-dict-args quirk. Only matches at
# string start or after a comma to avoid hitting colons inside string values.
_DICT_KEY_RE = re.compile(r"(^|,\s*)(\w+)\s*:")


def _normalize_call(inner: str) -> str | None:
    """Normalize one captured tool-call body to a Python call expression.

    Handles known model-emission quirks: fullwidth colon, `call[...]` wrapper,
    `name{}` empty-args, `name{key: val}` JSON-dict-args. Returns None if the
    body has an unknown shape — the caller drops it from the converted list.
    """
    s = inner.strip().replace("：", ":")  # fullwidth -> ASCII colon

    if s.startswith("call:"):
        s = s[len("call:"):].lstrip()
    elif s.startswith("call["):
        s = s[len("call["):].lstrip()
        if s.endswith("]"):
            s = s[:-1].rstrip()
    else:
        return None

    m = re.fullmatch(r"(\w+)\{\}", s)
    if m:
        return f"{m.group(1)}()"

    m = re.fullmatch(r"(\w+)\{(.+)\}", s, re.DOTALL)
    if m:
        name, body = m.group(1), m.group(2)
        args = _DICT_KEY_RE.sub(r"\1\2=", body)
        return f"{name}({args})"

    return s


def _gemma4_native_to_bfcl(result: str) -> str:
    """Rewrite Gemma 4 native tool-call syntax into BFCL's `[func(args), ...]`.

    Returns the input unchanged if no native markers are present, so
    responses already in BFCL format (turn-0 system-prompt-driven) and
    plain-prose refusals fall through to the default decoder unchanged.
    """
    matches = _GEMMA4_NATIVE_CALL_RE.findall(result)
    if not matches:
        return result
    normalized = [n for n in (_normalize_call(m) for m in matches) if n is not None]
    if not normalized:
        return result
    return "[" + ", ".join(normalized) + "]"


class Gemma4Handler(OSSHandler):
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
        self._ctx_fixed = False

    def _fix_context_length(self):
        if not self._ctx_fixed:
            # Gemma 4 is multimodal; the top-level HF config lacks
            # max_position_embeddings (it lives under text_config), so
            # spin_up_local_server falls back to the tokenizer sentinel (~10^18).
            # The real value is 262144, from config.text_config.
            self.max_context_length = 262144
            self._ctx_fixed = True

    @override
    def inference(self, test_entry, include_input_log, exclude_state_log):
        self._fix_context_length()
        return super().inference(test_entry, include_input_log, exclude_state_log)

    @override
    def _format_prompt(self, messages, function):
        return self.tokenizer.apply_chat_template(
            messages, add_generation_prompt=True, tokenize=False
        )

    @override
    def decode_ast(self, result, language, has_tool_call_tag):
        return default_decode_ast_prompting(
            _gemma4_native_to_bfcl(result), language, has_tool_call_tag
        )

    @override
    def decode_execute(self, result, has_tool_call_tag):
        return default_decode_execute_prompting(
            _gemma4_native_to_bfcl(result), has_tool_call_tag
        )

    @override
    def _add_execution_results_prompting(
        self, inference_data: dict, execution_results: list[str], model_response_data: dict
    ) -> dict:
        # Gemma 4's chat template silently drops messages with role="tool"
        # (the BFCL default). It renders role="tool_response" as a proper
        # turn, so the model sees tool feedback. Without this override the
        # model runs blind in multi-turn and loops on failed actions.
        for execution_result, decoded_model_response in zip(
            execution_results, model_response_data["model_responses_decoded"]
        ):
            inference_data["message"].append(
                {
                    "role": "tool_response",
                    "name": decoded_model_response,
                    "content": execution_result,
                }
            )
        return inference_data

    @override
    def _pre_query_processing_prompting(self, test_entry: dict) -> dict:
        functions: list = test_entry["function"]
        test_entry_id: str = test_entry["id"]

        test_entry["question"][0] = system_prompt_pre_processing_chat_model(
            test_entry["question"][0], functions, test_entry_id
        )

        for round_idx in range(len(test_entry["question"])):
            test_entry["question"][round_idx] = combine_consecutive_user_prompts(
                test_entry["question"][round_idx]
            )

        return {"message": [], "function": functions}
