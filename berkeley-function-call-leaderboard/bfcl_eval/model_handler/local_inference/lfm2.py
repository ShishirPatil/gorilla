import ast
import re
from typing import Any

from bfcl_eval.constants.enums import ModelStyle
from bfcl_eval.constants.type_mappings import GORILLA_TO_OPENAPI
from bfcl_eval.model_handler.local_inference.base_oss_handler import OSSHandler
from bfcl_eval.model_handler.utils import (
    convert_to_tool,
    default_decode_ast_prompting,
    default_decode_execute_prompting,
)
from bfcl_eval.utils import extract_test_category_from_id, is_agentic
from overrides import override

# Liquid LFM2.x emits tool calls in a Pythonic format wrapped in special tokens:
#   <|tool_call_start|>[func1(arg1="val", arg2=123), func2(...)]<|tool_call_end|>
# Reasoning, when present, is wrapped in <think>...</think>.
TOOL_CALL_START = "<|tool_call_start|>"
TOOL_CALL_END = "<|tool_call_end|>"
_TOOL_CALL_BLOCK_PATTERN = re.compile(
    r"<\|tool_call_start\|>\s*\[(.*?)\]\s*<\|tool_call_end\|>", re.DOTALL
)
_THINK_PATTERN = re.compile(r"<think>([\s\S]*?)</think>", re.DOTALL)
# Lone UTF-16 surrogates (e.g. half of an emoji) occasionally appear in raw model
# output and crash BFCL's result writer (json.dumps + utf-8 write). Strip them.
_SURROGATE_PATTERN = re.compile(r"[\ud800-\udfff]")


def _eval_node(node: ast.AST):
    """Convert a limited subset of AST nodes into Python objects."""
    if isinstance(node, ast.Constant):
        return node.value
    elif isinstance(node, ast.List):
        return [_eval_node(elt) for elt in node.elts]
    elif isinstance(node, ast.Tuple):
        return tuple(_eval_node(elt) for elt in node.elts)
    elif isinstance(node, ast.Dict):
        return {_eval_node(k): _eval_node(v) for k, v in zip(node.keys, node.values)}
    elif isinstance(node, ast.Name):
        # For bareword values such as order=ascending / descending
        return node.id
    elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        # Handle negative numbers
        return -_eval_node(node.operand)
    else:
        raise ValueError(f"Unsupported AST node: {ast.dump(node)}")


def _get_function_name(node: ast.expr) -> str:
    """Extract a (possibly dotted) function name from an AST node."""
    if isinstance(node, ast.Name):
        return node.id
    elif isinstance(node, ast.Attribute):
        return _get_function_name(node.value) + "." + node.attr
    else:
        raise ValueError(f"Invalid function name node: {node}")


def extract_tool_calls(text: str) -> list[dict]:
    """
    Extract all tool calls from a Liquid-format response.

    Format: <|tool_call_start|>[func_name(arg1="val", arg2=123), func2(...)]<|tool_call_end|>

    Returns a list of {"name": str, "arguments": dict}. Returns an empty list when no
    well-formed tool-call block is present, so callers can fall back to other parsing.
    """
    if not text:
        return []

    calls: list[dict] = []
    for match in _TOOL_CALL_BLOCK_PATTERN.findall(text):
        try:
            parsed = ast.parse(f"x = [{match}]").body[0].value.elts
        except Exception as e:
            print(f"Warning: Failed to parse tool call block: {e}")
            continue
        for call in parsed:
            try:
                if not isinstance(call, ast.Call):
                    continue
                function_name = _get_function_name(call.func)
                args = {kw.arg: _eval_node(kw.value) for kw in call.keywords}
                calls.append({"name": function_name, "arguments": args})
            except Exception as e:
                print(f"Warning: Failed to parse individual call: {e}")
                continue

    return calls


def strip_surrogates(text: str) -> str:
    """Remove lone UTF-16 surrogate codepoints that break JSON/utf-8 serialization."""
    return _SURROGATE_PATTERN.sub("", text) if text else text


# --- Robustify BFCL's result writer against lone UTF-16 surrogates --------------------
# BFCL's writer does json.dumps(ensure_ascii=False) then writes utf-8, which raises
# UnicodeEncodeError on a lone surrogate (half an emoji). These arrive not only from
# model output (sanitized in _parse_query_response_prompting) but also from tool-execution
# results / web_search web content that base_handler logs into the result file directly --
# a path no handler method can intercept. We patch the single serialization chokepoint,
# bfcl_eval.utils.make_json_serializable, so every string it emits is surrogate-free.
# write_list_of_dicts_to_file resolves make_json_serializable from module globals at call
# time, so reassigning it here takes effect without editing any core BFCL file.
import bfcl_eval.utils as _bfcl_utils  # noqa: E402

_orig_make_json_serializable = _bfcl_utils.make_json_serializable


def _make_json_serializable_strip_surrogates(value):
    if isinstance(value, str):
        return strip_surrogates(value)
    if isinstance(value, dict):
        return {
            k: _make_json_serializable_strip_surrogates(v) for k, v in value.items()
        }
    if isinstance(value, list):
        return [_make_json_serializable_strip_surrogates(item) for item in value]
    return _orig_make_json_serializable(value)


# Idempotent: only wrap once even if this module is imported/reloaded multiple times.
if getattr(_bfcl_utils.make_json_serializable, "__name__", "") != (
    "_make_json_serializable_strip_surrogates"
):
    _bfcl_utils.make_json_serializable = _make_json_serializable_strip_surrogates
# --------------------------------------------------------------------------------------


def extract_think_block(text: str) -> str:
    """Return the reasoning inside <think>...</think>, or "" if not present."""
    if not text:
        return ""
    match = _THINK_PATTERN.search(text)
    return match.group(1).strip() if match else ""


def strip_think_block(text: str) -> str:
    """Remove all <think>...</think> blocks from the text used for decode/eval."""
    if text and "<think>" in text and "</think>" in text:
        return _THINK_PATTERN.sub("", text).lstrip("\n")
    return text


def parse_liquid_response(response: str) -> str:
    """
    If the response contains the tool-call tokens, return the content of the first
    <|tool_call_start|>...<|tool_call_end|> block with the tokens stripped
    (e.g. `[func(arg=val)]`); otherwise return the response unchanged. This is what
    becomes `model_responses` (eval + decode input).
    """
    if response is None:
        return "No Response"
    if not isinstance(response, str):
        try:
            response = str(response)
        except Exception:
            return ""
    if TOOL_CALL_START in response and TOOL_CALL_END in response:
        match = re.search(r"<\|tool_call_start\|>(.*?)<\|tool_call_end\|>", response, re.DOTALL)
        answer = match.group(1) if match else response
        return re.sub(r"<\|tool_call_start\|>|<\|tool_call_end\|>", "", answer).strip()
    return response


# LFM2.x's native tool-use instruction, baked into the handler the same way
# QwenFCHandler bakes Qwen's "# Tools ... You may call one or more functions" block and
# MiniCPMFCHandler relies on its template's "# Function Call Rule" block. The function
# signatures themselves are rendered natively via the chat template's tools= argument
# (as `List of tools: [...]`); this instruction supplies the behavioral guidance the
# LFM2.x template does not include on its own.
LFM2_FC_SYSTEM_PROMPT = """You are an expert in composing functions. You are given a question and a set of possible functions. Based on the question, you will need to make one or more function/tool calls to achieve the purpose.
If none of the functions can be used, point it out. If the given question lacks the parameters required by the function, also point it out.
You should only return the function calls in your response.

If you decide to invoke any of the function(s), you MUST put it in the format of <|tool_call_start|>[func_name1(params_name1=params_value1, params_name2=params_value2...), func_name2(params)]<|tool_call_end|>
You SHOULD NOT include any other text in the response.

At each turn, you should try your best to complete the tasks requested by the user within the current turn. Continue to output functions to call until you have fulfilled the user's request to the best of your ability. Once you have no more functions to call, the system will consider the current turn complete and proceed to the next turn or task.
"""

# Non-restrictive tool-call FORMAT guidance for agentic categories (web_search, memory).
# Those categories carry BFCL's own conversational prompt (the {answer,context} format,
# and the memory agent role + core-memory dump) and must be free to respond in prose, so
# we must NOT impose "only return the function calls". But the model still needs to know
# *how* to format any calls it does make, since decode_execute parses this format -- so we
# append just the format instruction, without the behavioral restrictions.
LFM2_TOOL_CALL_FORMAT_INSTRUCTION = (
    "When you decide to invoke any of the available function(s), you MUST put the "
    "call(s) in the format of <|tool_call_start|>[func_name1(params_name1=params_value1, "
    "params_name2=params_value2...), func_name2(params)]<|tool_call_end|>."
)


class LFM2Handler(OSSHandler):
    """
    Function-calling handler for Liquid AI LFM2.x models (e.g. LFM2.5), following the
    same pattern as QwenFCHandler / MiniCPMFCHandler.

    LFM2.x uses a ChatML-like chat template (``<|startoftext|>``, ``<|im_start|>``,
    ``<|im_end|>``) with native ``system``/``user``/``assistant``/``tool`` roles. Function
    signatures are passed through the chat template's native ``tools=`` argument (which
    LFM2.x renders as ``List of tools: [...]``) -- the format the model was trained on --
    and LFM2.x's own tool-use instruction is injected as the system message (see
    LFM2_FC_SYSTEM_PROMPT), mirroring how QwenFCHandler bakes Qwen's ``# Tools`` block in.

    LFM2.x emits tool calls in a Pythonic format wrapped in
    ``<|tool_call_start|>[...]<|tool_call_end|>`` tokens, optionally preceded by a
    ``<think>...</think>`` reasoning block. We strip the reasoning block from the
    response used for decoding/evaluation, record it as ``reasoning_content``, and keep
    it on the assistant chat-history message as ``thinking`` for multi-turn fidelity. We
    decode the Pythonic tool calls directly, falling back to BFCL's default bare-list
    decoders when the special tokens are absent.

    Named per major version (LFM2) rather than per point release so LFM3 can get its own
    handler when it arrives.
    """

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

    @override
    def _pre_query_processing_prompting(self, test_entry: dict) -> dict:
        # FC-style handler (cf. QwenFCHandler / MiniCPMFCHandler): do NOT use BFCL's
        # generic system_prompt_pre_processing_chat_model. Instead inject LFM2.x's own
        # tool-use instruction as the system message, and render the function signatures
        # natively via the chat template's tools= argument (see _format_prompt).
        #
        # Convert the Gorilla function schema with convert_to_tool(..., OPENAI_COMPLETIONS)
        # so the model sees standard
        # `[{"type": "function", "function": {... OpenAPI types ...}}]` tool
        # rendering (object/number/array, names with "." -> "_", hence
        # underscore_to_dot=True in model_config) rather than raw Gorilla types.
        functions: list = convert_to_tool(
            test_entry["function"], GORILLA_TO_OPENAPI, ModelStyle.OPENAI_COMPLETIONS
        )

        # Agentic categories (web_search, memory) already carry BFCL's own system
        # prompt -- the agentic {answer,context} response format, and for memory the
        # agent role + live core-memory dump. Those require a conversational/structured
        # response, which conflicts with our "only return the function calls, no other
        # text" instruction. So:
        #   - non-agentic: inject the full LFM2_FC_SYSTEM_PROMPT (the only instruction
        #     present, since BFCL injects nothing for FC-style handlers);
        #   - agentic: keep BFCL's prompt and only APPEND the non-restrictive tool-call
        #     format instruction, so the model still emits the format decode_execute
        #     expects without being told to suppress its prose answer.
        prompts: list[dict] = test_entry["question"][0]
        if not is_agentic(extract_test_category_from_id(test_entry["id"])):
            if prompts and prompts[0]["role"] == "system":
                prompts[0]["content"] = (
                    LFM2_FC_SYSTEM_PROMPT + "\n\n" + prompts[0]["content"]
                )
            else:
                prompts.insert(0, {"role": "system", "content": LFM2_FC_SYSTEM_PROMPT})
        else:
            if prompts and prompts[0]["role"] == "system":
                prompts[0]["content"] = (
                    prompts[0]["content"] + "\n\n" + LFM2_TOOL_CALL_FORMAT_INSTRUCTION
                )
            else:
                prompts.insert(
                    0, {"role": "system", "content": LFM2_TOOL_CALL_FORMAT_INSTRUCTION}
                )

        return {"message": [], "function": functions}

    @override
    def _format_prompt(self, messages, function):
        # Render the function signatures through LFM2.x's native chat-template tools=
        # path (as `List of tools: [...]`), alongside the instruction system message
        # injected above. This is the format the model was trained on.
        formatted_prompt = self.tokenizer.apply_chat_template(
            messages,
            tools=function,
            add_generation_prompt=True,
            tokenize=False,
        )

        return formatted_prompt

    @override
    def _parse_query_response_prompting(self, api_response: Any) -> dict:
        # Parse the raw completion text: strip <think>, then `model_responses` is the
        # de-tagged first tool-call block (parse_liquid_response), the chat-history
        # message keeps the tagged content, and tool_calls_decoded holds the parsed
        # [{name, arguments}] calls for execution-result threading.
        content = strip_surrogates(api_response.choices[0].text)
        reasoning_content = extract_think_block(content)
        content_tobe_parsed = strip_think_block(content)

        model_responses = parse_liquid_response(content_tobe_parsed)
        decoded_calls = extract_tool_calls(content_tobe_parsed)

        message_for_chat_history = {"role": "assistant", "content": content_tobe_parsed}
        if reasoning_content:
            message_for_chat_history["thinking"] = reasoning_content

        return {
            "model_responses": model_responses,
            "model_responses_message_for_chat_history": message_for_chat_history,
            "model_responses_decoded": decoded_calls,
            "tool_calls_decoded": decoded_calls,
            "reasoning_content": reasoning_content,
            "input_token": api_response.usage.prompt_tokens,
            "output_token": api_response.usage.completion_tokens,
        }

    @override
    def _add_assistant_message_prompting(
        self, inference_data: dict, model_response_data: dict
    ) -> dict:
        inference_data["message"].append(
            model_response_data["model_responses_message_for_chat_history"]
        )
        return inference_data

    @override
    def _add_execution_results_prompting(
        self, inference_data: dict, execution_results: list[str], model_response_data: dict
    ) -> dict:
        # Tool results go back as one `tool` message whose content is
        # repr([{'name': <func name>, 'result': <execution result>}, ...]), pairing each
        # result with its function name from the parsed tool calls (tool_calls_decoded).
        response_message = []
        decoded = model_response_data["tool_calls_decoded"]
        for execution_result, tool_call in zip(execution_results, decoded):
            response_message.append(
                {"name": tool_call["name"], "result": execution_result}
            )

        inference_data["message"].append(
            {"role": "tool", "content": repr(response_message)}
        )
        return inference_data

    @override
    def decode_ast(self, result, language, has_tool_call_tag):
        # Decode the Pythonic tool calls; fall back to the default bare-list parser.
        extracted = extract_tool_calls(result)
        if extracted:
            return [{call["name"]: call["arguments"]} for call in extracted]
        try:
            return default_decode_ast_prompting(result, language, has_tool_call_tag)
        except Exception:
            return []

    @override
    def decode_execute(self, result, has_tool_call_tag):
        # Decode the Pythonic tool calls to executable strings; else default parser.
        extracted = extract_tool_calls(result)
        if extracted:
            calls = []
            for call in extracted:
                args_str = ", ".join(
                    f"{k}={repr(v)}" for k, v in call["arguments"].items()
                )
                calls.append(f"{call['name']}({args_str})")
            return calls
        try:
            return default_decode_execute_prompting(result)
        except Exception:
            return []
