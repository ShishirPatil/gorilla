import ast
import json
import re
from typing import Any

from bfcl_eval.constants.type_mappings import GORILLA_TO_OPENAPI
from bfcl_eval.model_handler.local_inference.base_oss_handler import OSSHandler
from bfcl_eval.model_handler.utils import convert_to_function_call, convert_to_tool
from overrides import override


class GLM5FCHandler(OSSHandler):
    """
    Handler for GLM-5.3 (`zai-org/GLM-5.3`, architecture `GlmMoeDsaForCausalLM`) in FC mode,
    and for models fine-tuned from it that keep its chat template, such as `praex/Lucia-III`.

    The prompt is built by hand to match the model's default `chat_template.jinja`
    (thinking on, default reasoning effort), and tool calls are parsed from the GLM format:

        <tool_call>{function-name}<arg_key>{key}</arg_key><arg_value>{value}</arg_value>...</tool_call>

    In that format string arguments are written as raw text and all other arguments as JSON,
    so the parser uses the tool schema to type the arguments, like vLLM's `glm45` tool parser.
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
        self.model_name_huggingface = model_name
        # <|endoftext|>, <|user|>, <|observation|> (the `eos_token_id` list in generation_config.json)
        self.stop_token_ids = [154820, 154827, 154829]

    @override
    def _format_prompt(self, messages, function):
        """
        Reproduces the parts of GLM-5.3's `chat_template.jinja` that BFCL uses
        (https://huggingface.co/zai-org/GLM-5.3/blob/main/chat_template.jinja):

        [gMASK]<sop><|system|>Reasoning Effort: Max<|system|>
        # Tools

        You may call one or more functions to assist with the user query.

        You are provided with function signatures within <tools></tools> XML tags:
        <tools>
        {tool_1 as JSON}
        {tool_2 as JSON}
        </tools>

        For each function call, output the function name and arguments within the following XML format:
        <tool_call>{function-name}<arg_key>{arg-key-1}</arg_key><arg_value>{arg-value-1}</arg_value><arg_key>{arg-key-2}</arg_key><arg_value>{arg-value-2}</arg_value>...</tool_call><|system|>{system}<|user|>{user}<|assistant|><think>{reasoning}</think>{content}<tool_call>...</tool_call><|observation|><tool_response>{result_1}</tool_response><tool_response>{result_2}</tool_response><|assistant|><think>

        The template keeps the reasoning of earlier assistant turns by default (`clear_thinking` is false).
        Tool results carry no tool call ids in BFCL, so the template renders them in their original order.
        """
        tools = convert_to_tool(function, GORILLA_TO_OPENAPI, self.model_style)

        # The default reasoning effort is "max" when the `reasoning_effort` template variable is not set.
        formatted_prompt = "[gMASK]<sop><|system|>Reasoning Effort: Max"

        if len(tools) > 0:
            formatted_prompt += (
                "<|system|>\n# Tools\n\nYou may call one or more functions to assist with the user query.\n\n"
                "You are provided with function signatures within <tools></tools> XML tags:\n<tools>\n"
            )
            for tool in tools:
                formatted_prompt += self._tool_to_json(tool) + "\n"
            formatted_prompt += (
                "</tools>\n\nFor each function call, output the function name and arguments within the following XML format:\n"
                "<tool_call>{function-name}<arg_key>{arg-key-1}</arg_key><arg_value>{arg-value-1}</arg_value>"
                "<arg_key>{arg-key-2}</arg_key><arg_value>{arg-value-2}</arg_value>...</tool_call>"
            )

        for idx, message in enumerate(messages):
            role = message["role"]
            content = message.get("content") or ""

            if role == "user":
                formatted_prompt += f"<|user|>{content}"

            elif role == "system":
                formatted_prompt += f"<|system|>{content}"

            elif role == "assistant":
                reasoning_content = message.get("reasoning_content")
                if not isinstance(reasoning_content, str):
                    reasoning_content = None
                    if "</think>" in content:
                        reasoning_content = content.split("</think>")[0].split("<think>")[-1]
                        content = content.split("</think>")[-1]

                formatted_prompt += "<|assistant|>"
                if reasoning_content is not None:
                    formatted_prompt += f"<think>{reasoning_content}</think>"
                else:
                    formatted_prompt += "<think></think>"

                if content.strip():
                    formatted_prompt += content.strip()

                for tool_call in message.get("tool_calls") or []:
                    if "function" in tool_call:
                        tool_call = tool_call["function"]
                    arguments = tool_call["arguments"]
                    if isinstance(arguments, str):
                        arguments = json.loads(arguments)
                    formatted_prompt += f"<tool_call>{tool_call['name']}"
                    for key, value in arguments.items():
                        if not isinstance(value, str):
                            value = json.dumps(value, ensure_ascii=False)
                        formatted_prompt += (
                            f"<arg_key>{key}</arg_key><arg_value>{value}</arg_value>"
                        )
                    formatted_prompt += "</tool_call>"

            elif role == "tool":
                if idx == 0 or messages[idx - 1]["role"] != "tool":
                    formatted_prompt += "<|observation|>"
                formatted_prompt += f"<tool_response>{content}</tool_response>"

        formatted_prompt += "<|assistant|><think>"

        return formatted_prompt

    @override
    def _pre_query_processing_prompting(self, test_entry: dict) -> dict:
        functions: list = test_entry["function"]

        # FC models use their own system prompt, so no need to add any message.
        # In the multi_turn_miss_func category, the held-out functions are shown to the model
        # later in a user message; keep their schema so their arguments can be typed too.
        functions_for_parsing = list(functions)
        for missed_functions in test_entry.get("missed_function", {}).values():
            functions_for_parsing.extend(missed_functions)

        return {
            "message": [],
            "function": functions,
            "functions_for_parsing": functions_for_parsing,
        }

    @override
    def _query_prompting(self, inference_data: dict):
        api_response, query_latency = super()._query_prompting(inference_data)

        # `_parse_query_response_prompting` only receives the API response, but the
        # arguments of a GLM tool call can only be typed with the tool schema.
        # Pass the parameter types along with the response.
        param_types = self._get_param_types(
            inference_data.get("functions_for_parsing", inference_data["function"])
        )
        return {"api_response": api_response, "param_types": param_types}, query_latency

    @override
    def _parse_query_response_prompting(self, api_response: Any) -> dict:
        param_types = api_response["param_types"]
        api_response = api_response["api_response"]
        model_response = api_response.choices[0].text

        # The prompt ends with "<think>", so the output is "{reasoning}</think>{content}".
        # Output without "</think>" is unfinished reasoning (e.g. cut off by the token limit).
        if "</think>" in model_response:
            reasoning_content, _, content = model_response.partition("</think>")
        else:
            reasoning_content, content = model_response, ""

        tool_calls = self._extract_tool_calls(content, param_types)

        if len(tool_calls) > 0:
            model_responses = [{call["name"]: call["arguments"]} for call in tool_calls]
            model_responses_message_for_chat_history = {
                "role": "assistant",
                "content": content[: content.find("<tool_call>")],
                "reasoning_content": reasoning_content,
                "tool_calls": tool_calls,
            }
        else:
            model_responses = content
            model_responses_message_for_chat_history = {
                "role": "assistant",
                "content": content,
                "reasoning_content": reasoning_content,
            }

        return {
            "model_responses": model_responses,
            "reasoning_content": reasoning_content,
            "model_responses_message_for_chat_history": model_responses_message_for_chat_history,
            "input_token": api_response.usage.prompt_tokens,
            "output_token": api_response.usage.completion_tokens,
        }

    @override
    def _add_assistant_message_prompting(
        self, inference_data: dict, model_response_data: dict
    ) -> dict:
        inference_data["message"].append(
            model_response_data["model_responses_message_for_chat_history"],
        )
        return inference_data

    @override
    def decode_ast(self, result, language, has_tool_call_tag):
        # `result` is a list of {function_name: arguments} when the model called tools,
        # and the text of the answer otherwise.
        if isinstance(result, str):
            return []
        return [{name: dict(arguments)} for call in result for name, arguments in call.items()]

    @override
    def decode_execute(self, result, has_tool_call_tag):
        if isinstance(result, str):
            return []
        return convert_to_function_call(result)

    def _get_param_types(self, functions: list[dict]) -> dict[str, dict[str, Any]]:
        """Map each tool name (as shown to the model) to {parameter name: JSON schema type}."""
        tools = convert_to_tool(functions, GORILLA_TO_OPENAPI, self.model_style)
        return {
            tool["name"]: {
                param: spec.get("type")
                for param, spec in tool.get("parameters", {}).get("properties", {}).items()
            }
            for tool in tools
        }

    @staticmethod
    def _tool_to_json(tool: dict) -> str:
        # Same as the template's `tool_to_json` macro: `tojson(ensure_ascii=False)` per field,
        # skipping `defer_loading` and `strict`.
        return (
            "{"
            + ", ".join(
                f'"{key}": {json.dumps(value, ensure_ascii=False)}'
                for key, value in tool.items()
                if key not in ("defer_loading", "strict")
            )
            + "}"
        )

    @staticmethod
    def _deserialize(value: str) -> Any:
        try:
            return json.loads(value)
        except Exception:
            pass
        try:
            return ast.literal_eval(value)
        except Exception:
            pass
        return value

    @classmethod
    def _extract_tool_calls(cls, content: str, param_types: dict) -> list[dict]:
        tool_calls = []
        for block in re.findall(r"<tool_call>(.*?)</tool_call>", content, re.DOTALL):
            name = block.split("<arg_key>", 1)[0].strip()
            if not name:
                continue
            arguments = {}
            for key, value in re.findall(
                r"<arg_key>(.*?)</arg_key>\s*<arg_value>(.*?)</arg_value>", block, re.DOTALL
            ):
                key = key.strip()
                value = value.strip()
                # String arguments are written as raw text; everything else is JSON.
                if param_types.get(name, {}).get(key) != "string":
                    value = cls._deserialize(value)
                arguments[key] = value
            tool_calls.append({"name": name, "arguments": arguments})
        return tool_calls
