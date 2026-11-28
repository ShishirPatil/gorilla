import json
import re
from typing import Any

from bfcl_eval.model_handler.local_inference.base_oss_handler import OSSHandler
from bfcl_eval.model_handler.utils import convert_to_function_call
from overrides import override


class Lfm3FCHandler(OSSHandler):
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
        # Preserve <tool_call>, <function=...>, <parameter=...>, and <think> special tokens
        self.skip_special_tokens = False

    @override
    def decode_ast(self, result, language, has_tool_call_tag):
        tool_calls = self._extract_tool_calls(result)
        if not isinstance(tool_calls, list) or any(
            not isinstance(item, dict) for item in tool_calls
        ):
            raise ValueError(f"Model did not return a list of function calls: {result}")
        return [
            {call["name"]: {k: v for k, v in call["arguments"].items()}}
            for call in tool_calls
        ]

    @override
    def decode_execute(self, result, has_tool_call_tag):
        tool_calls = self._extract_tool_calls(result)
        if not isinstance(tool_calls, list) or any(
            not isinstance(item, dict) for item in tool_calls
        ):
            raise ValueError(f"Model did not return a list of function calls: {result}")
        decoded_result = [{item["name"]: item["arguments"]} for item in tool_calls]
        return convert_to_function_call(decoded_result)

    @staticmethod
    def _render_value(value: Any) -> str:
        if isinstance(value, str):
            return value
        if isinstance(value, bool):
            return "true" if value else "false"
        if value is None:
            return "null"
        if isinstance(value, (dict, list)):
            return json.dumps(value)
        return str(value)

    @classmethod
    def _render_tool_calls(cls, tool_calls: list) -> str:
        blocks = []
        for tool_call in tool_calls:
            func = tool_call["function"] if "function" in tool_call else tool_call
            func_args = func.get("arguments", {})
            if isinstance(func_args, str):
                stripped = func_args.strip()
                func_args = json.loads(stripped) if stripped not in ("", "{}", "null") else {}
            block = f"<tool_call>\n<function={func['name']}>\n"
            if isinstance(func_args, dict):
                for arg_name, arg_value in func_args.items():
                    block += (
                        f"<parameter={arg_name}>\n"
                        f"{cls._render_value(arg_value)}\n"
                        f"</parameter>\n"
                    )
            block += "</function>\n</tool_call>"
            blocks.append(block)
        return "\n\n".join(blocks)

    @override
    def _format_prompt(self, messages, function):
        """Format conversation matching Sayansantra/LFM3-2.0B-WSP-V5 chat_template.jinja."""
        formatted_prompt = ""
        system_prompt = ""
        remaining_messages = list(messages)

        if remaining_messages and remaining_messages[0]["role"] == "system":
            system_prompt = remaining_messages[0].get("content") or ""
            remaining_messages = remaining_messages[1:]

        if function:
            tool_lines = [json.dumps(tool) for tool in function]
            tools_block = "<tools>\n" + "\n".join(tool_lines) + "\n</tools>"
            system_prompt = (
                f"{system_prompt}\n\n{tools_block}" if system_prompt else tools_block
            )

        if system_prompt:
            formatted_prompt += f"<|im_start|>system\n{system_prompt}<|im_end|>\n"

        last_user_index = -1
        for idx, message in enumerate(remaining_messages):
            if message["role"] == "user":
                last_user_index = idx

        for idx, message in enumerate(remaining_messages):
            role = message["role"]
            content = message.get("content") or ""

            if role == "assistant":
                reasoning = message.get("reasoning_content") or ""
                keep_thinking = idx > last_user_index
                if not reasoning and "</think>" in content:
                    parts = content.split("</think>", 1)
                    reasoning = parts[0].split("<think>")[-1]
                    content = parts[1].strip()
                elif not keep_thinking and "</think>" in content:
                    content = content.split("</think>")[-1].strip()

                formatted_prompt += "<|im_start|>assistant\n"
                if keep_thinking:
                    formatted_prompt += f"<think>{reasoning}</think>"
                else:
                    formatted_prompt += "<think></think>"

                formatted_prompt += content
                if message.get("tool_calls"):
                    formatted_prompt += self._render_tool_calls(message["tool_calls"])
                formatted_prompt += "<|im_end|>\n"

            elif role == "tool":
                if isinstance(content, str) and "<tool_response>" in content:
                    tool_body = content
                else:
                    tool_str = (
                        content if isinstance(content, str) else json.dumps(content)
                    )
                    tool_body = f"<tool_response>\n{tool_str}\n</tool_response>"
                formatted_prompt += f"<|im_start|>tool\n{tool_body}<|im_end|>\n"

            else:
                formatted_prompt += f"<|im_start|>{role}\n{content}<|im_end|>\n"

        formatted_prompt += "<|im_start|>assistant\n<think>"
        return formatted_prompt

    @override
    def _pre_query_processing_prompting(self, test_entry: dict) -> dict:
        functions: list = test_entry["function"]
        return {"message": [], "function": functions}

    @override
    def _parse_query_response_prompting(self, api_response: Any) -> dict:
        model_response = api_response.choices[0].text
        reasoning_content = ""
        cleaned_response = model_response

        if "</think>" in model_response:
            parts = model_response.split("</think>", 1)
            reasoning_content = parts[0].split("<think>")[-1].strip()
            cleaned_response = parts[1].strip()

        extracted_tool_calls = self._extract_tool_calls(cleaned_response)

        if len(extracted_tool_calls) > 0:
            model_responses_message_for_chat_history = {
                "role": "assistant",
                "content": "",
                "tool_calls": extracted_tool_calls,
                "reasoning_content": reasoning_content,
            }
        else:
            model_responses_message_for_chat_history = {
                "role": "assistant",
                "content": cleaned_response,
                "reasoning_content": reasoning_content,
            }

        return {
            "model_responses": cleaned_response,
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
            model_response_data["model_responses_message_for_chat_history"]
        )
        return inference_data

    @staticmethod
    def _parse_param_value(raw_val: str) -> Any:
        val = raw_val.strip()
        if not val:
            return ""
        try:
            return json.loads(val)
        except Exception:
            return val

    @classmethod
    def _extract_tool_calls(cls, input_string: str) -> list[dict[str, Any]]:
        if not input_string:
            return []
        text = input_string
        if "</think>" in text:
            text = text.split("</think>", 1)[1]

        call_pattern = re.compile(
            r"<tool_call>\s*<function=([^>\n]+)>\s*(.*?)\s*</function>\s*</tool_call>",
            re.DOTALL,
        )
        param_pattern = re.compile(
            r"<parameter=([^>\n]+)>\s*(.*?)\s*</parameter>",
            re.DOTALL,
        )

        result = []
        for func_name, body in call_pattern.findall(text):
            arguments: dict[str, Any] = {}
            for param_name, raw_val in param_pattern.findall(body):
                arguments[param_name.strip()] = cls._parse_param_value(raw_val)
            result.append({"name": func_name.strip(), "arguments": arguments})
        return result
