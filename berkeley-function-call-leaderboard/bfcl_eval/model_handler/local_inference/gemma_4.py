import os
import re
from typing import Any

from bfcl_eval.model_handler.local_inference.base_oss_handler import OSSHandler
from bfcl_eval.model_handler.utils import (
    combine_consecutive_user_prompts,
    system_prompt_pre_processing_chat_model,
)
from overrides import override


class Gemma4Handler(OSSHandler):
    """
    Local inference handler for Google's Gemma 4 family.

    Gemma 4 does NOT share Gemma 3's chat format, so `GemmaHandler` cannot be
    reused: Gemma 3 uses `<start_of_turn>role ... <end_of_turn>`, while Gemma 4
    uses `<|turn>role ... <turn|>` plus a separate thought channel and native
    tool-call/tool-response blocks.

    Two properties of the published Gemma 4 template drive this implementation,
    both verified by rendering `chat_template.jinja` from `google/gemma-4-12B-it`
    directly (2026-08-13):

    1. A bare ``{"role": "tool", ...}`` message renders to NOTHING. The template
       reaches its tool-response branch only from an assistant message carrying
       structured tool data, so BFCL's flat message list would silently lose
       every execution result and each multi-turn episode would run blind. That
       failure is invisible in the output -- it shows up only as a depressed
       multi-turn score, which is the exact column this benchmark run exists to
       measure. The tool-response block is therefore emitted explicitly here.

    2. Folding the tool messages onto the assistant message as `tool_responses`
       (the template's own "Gemma native" path) restores the content but emits it
       BEFORE the assistant's text, because in that path the call is expected to
       live in `tool_calls` rather than in the content. In BFCL prompt mode the
       call *is* the content, so the order inverts and the model sees the result
       before the call. Rendering the turn here keeps call-then-result order.

    The thought channel follows the template's convention, which reads inverted
    at a glance: an EMPTY thought channel is the instruction NOT to think, while
    omitting it lets the model open one itself.
    """

    # <|turn> markers are the turn boundary; the tokenizer's EOS also applies.
    # Left to the server's generation_config rather than pinned here, since the
    # Gemma 4 sizes ship consistent EOS ids.
    enable_thinking = True

    # Keep special tokens in the completion text. The thought channel is
    # delimited by `<|channel>` / `<channel|>`, which ARE special tokens: with
    # the default skip_special_tokens the server strips them and the reply
    # arrives as "thought\n<reasoning>[actual_call(...)]" with no boundary left
    # to split on. The reasoning then reaches decode_ast as if it were the
    # answer. Verified on the smoke run before this was set.
    skip_special_tokens = False

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

    # Gemma 4's native call block: <|tool_call>call:name(arg=val, ...)<tool_call|>
    # The body is already Python-call syntax, so normalising to the prompt-mode
    # [name(arg=val, ...)] form is a pure re-wrap, not a re-parse.
    _NATIVE_TOOL_CALL_RE = re.compile(
        r"<\|tool_call>\s*call:\s*(.*?)\s*<tool_call\|>", re.DOTALL
    )

    @classmethod
    def _normalize_native_tool_calls(cls, text: str) -> str:
        """Rewrite native `<|tool_call>` blocks into BFCL's prompt-mode list form.

        Gemma 4 has native function calling, and in multi-turn it falls back to
        that syntax even when the system prompt asks for the bracket form. BFCL's
        `default_decode_ast_prompting` only understands the bracket form, so left
        alone every such reply scores zero -- the model called the right function
        with the right arguments and got no credit for it. Observed as a clean
        0.00% across all four multi-turn categories before this existed.

        Returns the text unchanged when there is no native block, so single-turn
        replies that already use the bracket form are untouched.
        """
        calls = cls._NATIVE_TOOL_CALL_RE.findall(text)
        if not calls:
            return text
        return "[" + ", ".join(call.strip() for call in calls if call.strip()) + "]"

    @staticmethod
    def _format_tool_response(name: str, response: str) -> str:
        """Mirrors the template's `format_tool_response_block` for string bodies."""
        return f'<|tool_response>response:{name}{{value:<|"|>{response}<|"|>}}<tool_response|>'

    @override
    def _format_prompt(self, messages, function):
        """
        Renders the prompt-mode subset of the Gemma 4 template:

            <|turn>system\\n[<|think|>\\n]{system}<turn|>\\n
            <|turn>user\\n{content}<turn|>\\n
            <|turn>model\\n{content}[{tool_response blocks}]<turn|>\\n
            <|turn>model\\n                              <- generation, thinking
            <|turn>model\\n<|channel>thought\\n<channel|> <- generation, no-think

        Multimodal parts and structured `tool_calls` are deliberately not handled:
        BFCL prompt mode produces neither.
        """
        formatted_prompt = ""

        if messages and messages[0]["role"] == "system":
            system_message = messages[0]["content"]
            messages = messages[1:]
        else:
            system_message = ""

        # The template emits the header when there is a system message or when
        # thinking is on, and places the think directive inside it.
        if system_message or self.enable_thinking:
            formatted_prompt += "<|turn>system\n"
            if self.enable_thinking:
                formatted_prompt += "<|think|>\n"
            formatted_prompt += f"{system_message.strip()}<turn|>\n"

        index = 0
        prev_was_tool_response = False
        while index < len(messages):
            message = messages[index]
            role = message["role"]
            content = message["content"] if isinstance(message["content"], str) else ""

            if role == "user":
                formatted_prompt += f"<|turn>user\n{content.strip()}<turn|>\n"
                prev_was_tool_response = False
                index += 1

            elif role == "assistant":
                # Open the model turn with the assistant text (in prompt mode this
                # text is the tool call itself), then append any execution results
                # that follow, keeping them inside the same model turn.
                formatted_prompt += f"<|turn>model\n{content.strip()}"
                index += 1
                emitted_tool_response = False
                while index < len(messages) and messages[index]["role"] == "tool":
                    tool_message = messages[index]
                    formatted_prompt += self._format_tool_response(
                        tool_message.get("name", "unknown"),
                        tool_message["content"],
                    )
                    emitted_tool_response = True
                    index += 1
                formatted_prompt += "<turn|>\n"
                prev_was_tool_response = emitted_tool_response

            elif role == "tool":
                # A tool result with no assistant message before it; give it a
                # model turn of its own so the content is not dropped.
                formatted_prompt += "<|turn>model\n"
                formatted_prompt += self._format_tool_response(
                    message.get("name", "unknown"), message["content"]
                )
                formatted_prompt += "<turn|>\n"
                prev_was_tool_response = True
                index += 1

            elif role == "system":
                formatted_prompt += f"<|turn>system\n{content.strip()}<turn|>\n"
                prev_was_tool_response = False
                index += 1

            else:
                index += 1

        # Generation prompt. An empty thought channel instructs the model not to
        # think; omitting the channel leaves it free to open one.
        formatted_prompt += "<|turn>model\n"
        if not self.enable_thinking:
            formatted_prompt += "<|channel>thought\n<channel|>"

        return formatted_prompt

    @override
    def _pre_query_processing_prompting(self, test_entry: dict) -> dict:
        functions: list = test_entry["function"]
        test_entry_id: str = test_entry["id"]

        # Gemma 4 has native function calling, but this handler runs the model in
        # prompt mode, so the function list goes into the system prompt.
        test_entry["question"][0] = system_prompt_pre_processing_chat_model(
            test_entry["question"][0], functions, test_entry_id
        )

        for round_idx in range(len(test_entry["question"])):
            test_entry["question"][round_idx] = combine_consecutive_user_prompts(
                test_entry["question"][round_idx]
            )

        return {"message": [], "function": functions}

    @override
    def _parse_query_response_prompting(self, api_response: Any) -> dict:
        raw_response = api_response.choices[0].text

        # In thinking mode the model opens its own thought channel; strip it so
        # the AST and executable checkers see only the answer.
        reasoning_content = ""
        model_response = raw_response
        if "<channel|>" in raw_response:
            reasoning_content, model_response = raw_response.rsplit("<channel|>", 1)
            reasoning_content = reasoning_content.replace("<|channel>thought", "", 1)

        model_response = self._normalize_native_tool_calls(model_response)

        # Gemma 4 sometimes emits a stray native tool-call marker (e.g. a bare
        # `<tool_call|>` closer) after a bracket-format call in multi-turn
        # contexts. The marker is not a serve-time stop id, so it reaches the
        # decoder and makes an otherwise-correct reply undecodable. Strip any
        # UNPAIRED markers left after full-block normalization above; paired
        # native blocks were already converted. This applies to every Gemma-4
        # prompt-mode model (measured: raises stock Gemma-4-E4B-it by +4.6
        # Overall on BFCL V4 — details in the PR).
        if True:
            model_response = (
                model_response.replace("<|tool_call>", "")
                .replace("<tool_call|>", "")
                .strip()
            )

        return {
            "model_responses": model_response,
            "reasoning_content": reasoning_content,
            "model_responses_message_for_chat_history": model_response,
            "input_token": api_response.usage.prompt_tokens,
            "output_token": api_response.usage.completion_tokens,
        }


class Gemma4NoThinkHandler(Gemma4Handler):
    """Gemma 4 with the thought channel closed empty, i.e. thinking suppressed."""

    enable_thinking = False
