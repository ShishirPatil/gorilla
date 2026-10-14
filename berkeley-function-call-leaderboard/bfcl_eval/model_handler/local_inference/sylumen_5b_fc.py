#!/usr/bin/env python3
"""BFCL model handler for ``TimJ3ly/Sylumen-5B`` (native function-calling mode).

Sylumen-5B is a tool-use fine-tune of ``IFM/K2-Horizon-3.7B`` (developed by Ghostcloud), so it
uses that base model's chat template and tool-calling grammar.  When the template is called with
``tools=...`` it renders the available tools and instructs the model to
answer with a single ``<ifm|tool_calls>`` block; each call is written as::

    <ifm|tool_calls>
    <ifm|tool_call>$FUNCTION_NAME
    <ifm|arg_key>$PARAMETER_NAME</ifm|arg_key>
    <ifm|arg_value>$PARAMETER_VALUE</ifm|arg_value>
    ...
    </ifm|tool_call>
    </ifm|tool_calls>

The model therefore behaves like the other self-hosted native-function-calling models in the
leaderboard (see ``local_inference/falcon_fc.py`` and ``local_inference/qwen_fc.py``): it is
registered with ``is_fc_model=True`` and this handler renders the tool block client-side with the
checkpoint's own template and decodes the model's own grammar.

Locally hosted models only implement the *prompting* half of the handler interface
(``OSSHandler.inference`` routes every local model through the prompting loop), so this module
implements ``_format_prompt`` and the prompting methods rather than the ``_FC`` ones.  Everything
that is model-specific lives here:

* ``_format_prompt`` uses ``apply_chat_template(messages, tools=function, tool_call_format="xml",
  reasoning_effort="high", add_generation_prompt=True)``;
* ``_query_prompting`` calls the official ``client.completions.create`` endpoint and applies the
  65 536-token context guard (the checkpoint advertises 524 288 positions, but the BFCL default
  server command does not pass ``--max-model-len``, so a single GPU cannot hold that KV cache;
  the guard and the served ``--max-model-len`` must agree);
* ``_parse_query_response_prompting`` splits the reasoning trace from the tool-call block and
  turns the block into BFCL's structured assistant history (``tool_calls`` with dict arguments)
  plus the raw decoded tool calls used by ``decode_ast`` / ``decode_execute``;
* ``_add_execution_results_prompting`` writes tool results back as ``role="tool"`` messages,
  which is the shape the checkpoint template expects.

The parsing helpers at the top of this module use the standard library only and can be unit-tested directly.
``docs`` / release notes: https://huggingface.co/TimJ3ly/Sylumen-5B
"""

from __future__ import annotations

import json
import os
import re
import time

from bfcl_eval.model_handler.local_inference.base_oss_handler import OSSHandler
from overrides import override

__all__ = [
    "Sylumen5BFCHandler",
    "MARKERS",
    "resolve_max_context",
    "coerce_arg_value",
    "strip_trailing_specials",
    "parse_output",
    "parse_to_ast",
    "parse_to_execute",
]

# --------------------------------------------------------------------------------------
# K2-Horizon control tokens (the model's released tokenizer markers)
# --------------------------------------------------------------------------------------
MARKERS = {
    "im_start": "<|ifm|im_start|>",
    "im_end": "<|ifm|im_end|>",
    "eot": "<|ifm|endoftext|>",
    "think": "<ifm|think>",
    "think_fast": "<ifm|think_fast>",
    "think_faster": "<ifm|think_faster>",
    "think_close": "</ifm|think>",
    "think_fast_close": "</ifm|think_fast>",
    "think_faster_close": "</ifm|think_faster>",
    "tool_calls": "<ifm|tool_calls>",
    "tool_calls_close": "</ifm|tool_calls>",
    "tool_call": "<ifm|tool_call>",
    "tool_call_close": "</ifm|tool_call>",
    "arg_key": "<ifm|arg_key>",
    "arg_key_close": "</ifm|arg_key>",
    "arg_value": "<ifm|arg_value>",
    "arg_value_close": "</ifm|arg_value>",
}

DEFAULT_MAX_CONTEXT = 65536
DEFAULT_MAX_NEW_TOKENS = 4096
_THINK_VARIANTS = (
    (MARKERS["think"], MARKERS["think_close"]),
    (MARKERS["think_fast"], MARKERS["think_fast_close"]),
    (MARKERS["think_faster"], MARKERS["think_faster_close"]),
)


def resolve_max_context(env=None) -> int:
    """Resolve the context guard; ``K2_MAX_CONTEXT`` overrides the 65 536-token default.

    The checkpoint's ``max_position_embeddings`` is 524 288, but BFCL's default local-server
    command does not pass ``--max-model-len``, so vLLM would try to reserve ~72 GiB of KV cache
    for that window on a single card.  The served context and this guard are therefore pinned
    to 65 536, which covers the multi-turn ``long_context`` category, and both can be raised
    together for deployments with more memory.
    """
    source = os.environ if env is None else env
    return int(source.get("K2_MAX_CONTEXT", DEFAULT_MAX_CONTEXT))


def coerce_arg_value(raw: str):
    """Invert the template's argument rendering.

    The template writes strings verbatim and everything else with ``tojson`` (see
    ``render_tool_calls_block``), so JSON is accepted only when it decodes to a non-string value;
    otherwise the literal text *is* the value.  No value is repaired or invented.
    """
    stripped = raw.strip()
    if stripped[:1] in "{[" or stripped in ("true", "false", "null"):
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            return raw
    try:
        value = json.loads(stripped)
    except json.JSONDecodeError:
        return raw
    return raw if isinstance(value, str) else value


def strip_trailing_specials(text: str) -> str:
    text = text.strip()
    for marker in (MARKERS["im_end"], MARKERS["eot"], MARKERS["im_start"]):
        if text.endswith(marker):
            text = text[: -len(marker)].rstrip()
    return text


def parse_output(raw: str) -> dict:
    """Parse one assistant completion into ``{reasoning_content, content, tool_calls}``.

    The generation prompt ends with ``<|ifm|im_start|>assistant\\n<ifm|think>\\n``, so the
    continuation normally starts with the reasoning text and closes it with ``</ifm|think>``.
    Both shapes are handled: reopened (``<ifm|think>text</ifm|think>``) and prompt-opened
    (``reasoning</ifm|think>``).  The function never invents arguments or repairs malformed
    calls; unparseable tool-call blocks simply yield an empty ``tool_calls`` list.
    """
    result = {"reasoning_content": "", "content": "", "tool_calls": []}
    text = raw
    reopened = next(((o, c) for o, c in _THINK_VARIANTS if o in text), None)
    if reopened:
        open_tag, close_tag = reopened
        body = text.split(open_tag, 1)[1]
    else:
        body = text
        close_tag = next((c for _, c in _THINK_VARIANTS if c in text), None)
    if close_tag is not None and close_tag in body:
        result["reasoning_content"] = body.split(close_tag, 1)[0].strip("\n")
        text = body.split(close_tag, 1)[1]
    else:
        # No closing think marker: everything generated is still inside the think block.
        result["reasoning_content"] = body.strip("\n")
        text = ""

    if MARKERS["tool_calls"] in text:
        head, tail = text.split(MARKERS["tool_calls"], 1)
        result["content"] = strip_trailing_specials(head)
        block = tail.split(MARKERS["tool_calls_close"], 1)[0]
        result["tool_calls"] = _parse_tool_call_block(block)
    else:
        result["content"] = strip_trailing_specials(text)
    return result


def _parse_tool_call_block(block: str) -> list:
    calls = []
    for chunk in block.split(MARKERS["tool_call"])[1:]:
        body = chunk.split(MARKERS["tool_call_close"], 1)[0].strip("\n")
        if not body:
            continue
        first_line, _, rest = body.partition("\n")
        name = first_line.strip()
        if not name or MARKERS["arg_key"] in name:
            continue
        args: dict = {}
        for key, value in re.findall(
            re.escape(MARKERS["arg_key"]) + r"(.*?)" + re.escape(MARKERS["arg_key_close"])
            + r"\s*" + re.escape(MARKERS["arg_value"]) + r"(.*?)" + re.escape(MARKERS["arg_value_close"]),
            rest,
            flags=re.S,
        ):
            args[key] = coerce_arg_value(value)
        calls.append({"name": name, "arguments": args})
    return calls


def parse_to_ast(result) -> list:
    """BFCL ``decode_ast`` format: ``[{"func": {arg: value, ...}}, ...]``."""
    if isinstance(result, list):
        return result
    return [
        {call["name"]: call["arguments"]} for call in parse_output(result)["tool_calls"]
    ]


def parse_to_execute(result) -> list:
    """BFCL ``decode_execute`` format: ``["func(k=repr(v), ...)", ...]``."""
    parsed = result if isinstance(result, dict) else parse_output(result)
    out = []
    for call in parsed["tool_calls"]:
        args = ",".join(f"{k}={v!r}" for k, v in call["arguments"].items())
        out.append(f"{call['name']}({args})")
    return out


# --------------------------------------------------------------------------------------
# BFCL handler
# --------------------------------------------------------------------------------------

class Sylumen5BFCHandler(OSSHandler):
    """Official-pattern local handler for Sylumen-5B's native tool calling."""

    def __init__(
        self,
        model_name,
        temperature,
        registry_name,
        is_fc_model,
        dtype="bfloat16",
        **kwargs,
    ) -> None:
        super().__init__(
            model_name, temperature, registry_name, is_fc_model, dtype=dtype, **kwargs
        )
        self.model_name_huggingface = model_name
        # ``K2_SERVED_MODEL`` lets a deployment point at a request-time LoRA adapter served
        # under its own vLLM module name; it defaults to the model id itself.
        self.served_model_name = os.environ.get("K2_SERVED_MODEL") or model_name
        self.reasoning_effort = os.environ.get("K2_REASONING_EFFORT", "high")
        self.tool_call_format = os.environ.get("K2_TOOL_CALL_FORMAT", "xml")
        self.max_context = resolve_max_context()
        self.max_new_tokens = int(
            os.environ.get("K2_MAX_NEW_TOKENS", DEFAULT_MAX_NEW_TOKENS)
        )

    @override
    def _format_prompt(self, messages, function):
        """Render the checkpoint template with the tool block included."""
        return self.tokenizer.apply_chat_template(
            messages,
            tools=function or None,
            tokenize=False,
            add_generation_prompt=True,
            reasoning_effort=self.reasoning_effort,
            tool_call_format=self.tool_call_format,
        )

    @override
    def _pre_query_processing_prompting(self, test_entry: dict) -> dict:
        # The checkpoint template carries its own system prompt + tool block, so BFCL's
        # default system prompt must not be injected.
        return {"message": [], "function": test_entry["function"]}

    @override
    def _query_prompting(self, inference_data: dict):
        function = inference_data["function"]
        message = inference_data["message"]
        formatted_prompt = self._format_prompt(message, function)
        inference_data["inference_input_log"] = {"formatted_prompt": formatted_prompt}

        input_token_count = len(self.tokenizer.tokenize(formatted_prompt))
        if input_token_count + self.max_new_tokens > self.max_context:
            raise RuntimeError(
                f"context_length_exceeded: {input_token_count} + {self.max_new_tokens} "
                f"> {self.max_context}"
            )

        start_time = time.time()
        api_response = self.client.completions.create(
            model=self.served_model_name,
            temperature=self.temperature,
            prompt=formatted_prompt,
            max_tokens=self.max_new_tokens,
            timeout=72000,
        )
        return api_response, time.time() - start_time

    @override
    def _parse_query_response_prompting(self, api_response) -> dict:
        raw = api_response.choices[0].text
        parsed = parse_output(raw)

        tool_calls = []
        for idx, call in enumerate(parsed["tool_calls"]):
            tool_calls.append(
                {
                    "id": f"call_{idx}",
                    "type": "function",
                    "function": {"name": call["name"], "arguments": call["arguments"]},
                }
            )

        chat_history_message = {
            "role": "assistant",
            "content": parsed["content"],
            "reasoning_content": parsed["reasoning_content"],
        }
        if tool_calls:
            chat_history_message["tool_calls"] = tool_calls

        return {
            "model_responses": raw,
            "model_responses_message_for_chat_history": chat_history_message,
            "tool_call_ids": [call["id"] for call in tool_calls],
            "reasoning_content": parsed["reasoning_content"],
            "input_token": api_response.usage.prompt_tokens,
            "output_token": api_response.usage.completion_tokens,
        }

    @override
    def _add_assistant_message_prompting(self, inference_data, model_response_data) -> dict:
        inference_data["message"].append(
            model_response_data["model_responses_message_for_chat_history"]
        )
        return inference_data

    @override
    def _add_execution_results_prompting(
        self, inference_data, execution_results, model_response_data
    ) -> dict:
        tool_call_ids = model_response_data.get("tool_call_ids", [])
        for idx, execution_result in enumerate(execution_results):
            message = {"role": "tool", "content": execution_result}
            if idx < len(tool_call_ids):
                message["tool_call_id"] = tool_call_ids[idx]
            inference_data["message"].append(message)
        return inference_data

    @override
    def decode_ast(self, result, language, has_tool_call_tag):
        return parse_to_ast(result)

    @override
    def decode_execute(self, result, has_tool_call_tag):
        return parse_to_execute(result)
