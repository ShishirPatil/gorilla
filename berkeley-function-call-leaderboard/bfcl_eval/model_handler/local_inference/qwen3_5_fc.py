"""BFCL handler for Qwen3.5-family models in native function-calling mode.

Qwen3.5 (and Qwen3-Coder) changed the tool-call wire format from the Qwen3
JSON-in-<tool_call> style to an XML-ish style rendered by the model's own chat
template:

    <tool_call>
    <function=get_weather>
    <parameter=city>
    Berlin
    </parameter>
    <parameter=days>
    3
    </parameter>
    </function>
    </tool_call>

Parameter values are untyped text in that format, so this handler:

1. Renders prompts with the model's own ``chat_template`` (via the tokenizer
   loaded by ``OSSHandler``) so the prompt is byte-identical to what the model
   was trained on.
2. Parses the XML tool calls and coerces every parameter value back to the type
   declared in the BFCL function spec for that test entry (int/float/bool/list/
   dict), leaving strings untouched.
3. Stores the *typed* JSON form (the Qwen3 ``<tool_call>{json}</tool_call>``
   style) as ``model_responses`` so the existing ``QwenFCHandler`` decoders and
   the AST checker work unchanged.

Thinking is left at the template default (disabled): the generation prompt ends
with an empty ``<think>\\n\\n</think>\\n\\n`` block, matching how the small
Qwen3.5 checkpoints are meant to be served for tool use.
"""

import json
import re
import threading
from typing import Any

from bfcl_eval.constants.enums import ModelStyle
from bfcl_eval.constants.type_mappings import GORILLA_TO_OPENAPI
from bfcl_eval.model_handler.local_inference.qwen_fc import QwenFCHandler
from bfcl_eval.model_handler.utils import convert_to_tool
from overrides import override

_TOOL_CALL_RE = re.compile(
    r"<tool_call>\s*<function=(?P<name>[^>\n]+)>(?P<body>.*?)</function>\s*</tool_call>",
    re.DOTALL,
)
_PARAM_RE = re.compile(
    r"<parameter=(?P<key>[^>\n]+)>\n?(?P<value>.*?)\n?</parameter>",
    re.DOTALL,
)

# BFCL/Gorilla type names (Python, Java and JavaScript categories) -> coercion.
_INT_TYPES = {"integer", "int", "long", "short", "byte"}
_FLOAT_TYPES = {"float", "number", "double"}
_BOOL_TYPES = {"boolean", "bool"}
_LIST_TYPES = {"array", "tuple", "list", "arraylist", "array"}
_DICT_TYPES = {"dict", "object", "hashmap", "map"}


def _coerce(value: str, type_name: str | None):
    """Coerce an XML parameter string to the declared BFCL type. Never raises."""
    raw = value.strip()
    t = (type_name or "").lower()

    def _json():
        return json.loads(raw)

    try:
        if t in _BOOL_TYPES:
            low = raw.lower()
            if low in ("true", "false"):
                return low == "true"
            return _json()
        if t in _INT_TYPES:
            try:
                return int(raw)
            except ValueError:
                f = float(raw)
                return int(f) if f.is_integer() else f
        if t in _FLOAT_TYPES:
            return float(raw)
        if t in _LIST_TYPES or t in _DICT_TYPES:
            return _json()
        if t in ("string", "str", "any", "") or t == "any":
            return raw
        # Unknown language-specific type (e.g. Java "String[]", JS "Object"):
        # take a JSON literal if it parses, else the raw text.
        try:
            return _json()
        except Exception:
            return raw
    except Exception:
        return raw


class Qwen35FCHandler(QwenFCHandler):
    def __init__(
        self,
        model_name,
        temperature,
        registry_name,
        is_fc_model,
        dtype="bfloat16",
        **kwargs,
    ) -> None:
        super().__init__(model_name, temperature, registry_name, is_fc_model, dtype, **kwargs)
        self.model_name_huggingface = model_name
        # Per-thread stash of the current test entry's function specs, used to
        # type-coerce XML parameter values. The handler instance is shared by
        # the generation thread pool, so this must be thread-local.
        self._tls = threading.local()

    # ------------------------------------------------------------------ prompt
    @override
    def _format_prompt(self, messages, function):
        tools = convert_to_tool(function, GORILLA_TO_OPENAPI, ModelStyle.OSSMODEL)
        tools = [{"type": "function", "function": t} for t in tools]
        return self.tokenizer.apply_chat_template(
            messages,
            tools=tools if len(tools) > 0 else None,
            tokenize=False,
            add_generation_prompt=True,
        )

    @override
    def _query_prompting(self, inference_data: dict):
        self._tls.param_types = self._param_type_index(inference_data.get("function", []))
        return super()._query_prompting(inference_data)

    @staticmethod
    def _param_type_index(functions: list[dict]) -> dict[str, dict[str, str]]:
        index: dict[str, dict[str, str]] = {}
        for fn in functions:
            props = (fn.get("parameters") or {}).get("properties") or {}
            types = {p: (spec or {}).get("type") for p, spec in props.items()}
            index[fn["name"]] = types
            # convert_to_tool rewrites '.' to '_' for OSS models; accept both.
            index[fn["name"].replace(".", "_")] = types
        return index

    # ------------------------------------------------------------------- parse
    def _parse_xml_tool_calls(self, text: str) -> list[dict]:
        param_types = getattr(self._tls, "param_types", {}) or {}
        calls = []
        for m in _TOOL_CALL_RE.finditer(text):
            name = m.group("name").strip()
            types = param_types.get(name, {})
            args = {}
            for pm in _PARAM_RE.finditer(m.group("body")):
                key = pm.group("key").strip()
                args[key] = _coerce(pm.group("value"), types.get(key))
            calls.append({"name": name, "arguments": args})
        return calls

    @override
    def _parse_query_response_prompting(self, api_response: Any) -> dict:
        model_response = api_response.choices[0].text

        reasoning_content = ""
        cleaned = model_response
        if "</think>" in model_response:
            parts = model_response.split("</think>")
            reasoning_content = parts[0].rstrip("\n").split("<think>")[-1].lstrip("\n")
            cleaned = parts[-1].lstrip("\n")

        tool_calls = self._parse_xml_tool_calls(cleaned)
        # Any natural-language preamble before the first call.
        text_content = _TOOL_CALL_RE.sub("", cleaned).strip()

        if len(tool_calls) > 0:
            # Store the typed JSON form so QwenFCHandler.decode_ast/decode_execute
            # and the checker see exactly what a Qwen3 FC model would emit.
            typed_form = "\n".join(
                "<tool_call>\n" + json.dumps(c, ensure_ascii=False) + "\n</tool_call>"
                for c in tool_calls
            )
            model_responses = typed_form
            history_message = {
                "role": "assistant",
                "content": text_content,
                "tool_calls": tool_calls,
            }
        else:
            model_responses = cleaned
            history_message = {"role": "assistant", "content": cleaned}

        history_message["reasoning_content"] = reasoning_content

        return {
            "model_responses": model_responses,
            "reasoning_content": reasoning_content,
            "model_responses_message_for_chat_history": history_message,
            "input_token": api_response.usage.prompt_tokens,
            "output_token": api_response.usage.completion_tokens,
        }
