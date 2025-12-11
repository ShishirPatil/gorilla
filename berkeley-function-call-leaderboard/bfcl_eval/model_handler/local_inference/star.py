import json
import re
from typing import Any

from bfcl_eval.model_handler.local_inference.base_oss_handler import OSSHandler
from bfcl_eval.model_handler.utils import (
    convert_to_function_call,
)
from overrides import override

SYSTEM_PROMPT="""
You are a helpful assistant. The assistant first thinks about the reasoning process in the mind and then provides the user with the answer. The reasoning process are enclosed within <think>{explain why the user's question can be answered without calling a function or why you should ask the user for more information or why you should call one or more functions and your plan to solve the user's question.}</think>, and then give the answer. You can call the tool by <tool_call> </tool_call> tag. 

If the user's question can be answered without calling any function, please answer the user's question directly. In this situation, you should return your thought and answer the user's question directly.

If the user cannot be answered without calling any function, and the user does not provide enough information to call functions, please ask the user for more information. In this situation, you should return your thought and ask the user for more information.

If the user's question cannot be answered without calling any function, and the user has provided enough information to call functions to solve it, you should call the functions. In this situation, the assistant should return your thought and call the functions.
""".strip()


class STARHandler(OSSHandler):
    def __init__(self, model_name, temperature) -> None:
        super().__init__(model_name, temperature)
        self.is_fc_model = True

    @override
    def decode_ast(self, result, language, has_tool_call_tag):
        # Model response is of the form:
        # "<tool_call>\n{\"name\": \"spotify.play\", \"arguments\": {\"artist\": \"Taylor Swift\", \"duration\": 20}}\n</tool_call>\n<tool_call>\n{\"name\": \"spotify.play\", \"arguments\": {\"artist\": \"Maroon 5\", \"duration\": 15}}\n</tool_call>"?
        tool_calls = self._extract_tool_calls(result)
        if type(tool_calls) != list or any(type(item) != dict for item in tool_calls):
            raise ValueError(f"Model did not return a list of function calls: {result}")
        return [
            {call["name"]: {k: v for k, v in call["arguments"].items()}}
            for call in tool_calls
        ]

    @override
    def decode_execute(self, result, has_tool_call_tag):
        tool_calls = self._extract_tool_calls(result)
        if type(tool_calls) != list or any(type(item) != dict for item in tool_calls):
            raise ValueError(f"Model did not return a list of function calls: {result}")
        decoded_result = []
        for item in tool_calls:
            if type(item) == str:
                item = eval(item)
            decoded_result.append({item["name"]: item["arguments"]})
        return convert_to_function_call(decoded_result)

    @override
    def _format_prompt(self, messages, function):
        """
        "chat_template":
        {%- if tools %}
            {{- '<|im_start|>system\n' }}
            {%- if messages[0]['role'] == 'system' %}
                {{- messages[0]['content'] }}
            {%- else %}
                {{- 'You are Qwen, created by Alibaba Cloud. You are a helpful assistant.' }}
            {%- endif %}
            {{- "\n\n# Tools\n\nYou may call one or more functions to assist with the user query.\n\nYou are provided with function signatures within <tools></tools> XML tags:\n<tools>" }}
            {%- for tool in tools %}
                {{- "\n" }}
                {{- tool | tojson }}
            {%- endfor %}
            {{- "\n</tools>\n\nFor each function call, return a json object with function name and arguments within <tool_call></tool_call> XML tags:\n<tool_call>\n{\"name\": <function-name>, \"arguments\": <args-json-object>}\n</tool_call><|im_end|>\n" }}
        {%- else %}
            {%- if messages[0]['role'] == 'system' %}
                {{- '<|im_start|>system\n' + messages[0]['content'] + '<|im_end|>\n' }}
            {%- else %}
                {{- '<|im_start|>system\nYou are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>\n' }}
            {%- endif %}
        {%- endif %}
        {%- for message in messages %}
            {%- if (message.role == "user") or (message.role == "system" and not loop.first) or (message.role == "assistant" and not message.tool_calls) %}
                {{- '<|im_start|>' + message.role + '\n' + message.content + '<|im_end|>' + '\n' }}
            {%- elif message.role == "assistant" %}
                {{- '<|im_start|>' + message.role }}
                {%- if message.content %}
                    {{- '\n' + message.content }}
                {%- endif %}
                {%- for tool_call in message.tool_calls %}
                    {%- if tool_call.function is defined %}
                        {%- set tool_call = tool_call.function %}
                    {%- endif %}
                    {{- '\n<tool_call>\n{"name": "' }}
                    {{- tool_call.name }}
                    {{- '", "arguments": ' }}
                    {{- tool_call.arguments | tojson }}
                    {{- '}\n</tool_call>' }}
                {%- endfor %}
                {{- '<|im_end|>\n' }}
            {%- elif message.role == "tool" %}
                {%- if (loop.index0 == 0) or (messages[loop.index0 - 1].role != "tool") %}
                    {{- '<|im_start|>user' }}
                {%- endif %}
                {{- '\n<tool_response>\n' }}
                {{- message.content }}
                {{- '\n</tool_response>' }}
                {%- if loop.last or (messages[loop.index0 + 1].role != "tool") %}
                    {{- '<|im_end|>\n' }}
                {%- endif %}
            {%- endif %}
        {%- endfor %}
        {%- if add_generation_prompt %}
            {{- '<|im_start|>assistant\n' }}
        {%- endif %}
        """
        formatted_prompt = ""

        if messages[0]["role"] == "system":
            system_prompt = messages[0]["content"]
        else:
            system_prompt = (
                SYSTEM_PROMPT
            )

        if len(function) > 0:
            formatted_prompt += "<|im_start|>system\n"
            formatted_prompt += system_prompt
            formatted_prompt += "\n\n# Tools\n\nYou may call one or more functions to assist with the user query.\n\nYou are provided with function signatures within <tools></tools> XML tags:\n<tools>"
            for tool in function:
                formatted_prompt += f"\n{json.dumps(tool)}\n"
            formatted_prompt += '\n</tools>\n\nFor each function call, return a json object with function name and arguments within <tool_call></tool_call> XML tags:\n<tool_call>\n{"name": <function-name>, "arguments": <args-json-object>}\n</tool_call><|im_end|>\n'
        else:
            formatted_prompt += f"<|im_start|>system\n{system_prompt}<|im_end|>\n"

        for idx, message in enumerate(messages):
            role = message["role"]
            content = message["content"]
            tool_calls = message.get(
                "tool_calls", []
            )  # tool calls is only present for assistant messages

            if (
                role == "user"
                or (role == "system" and idx != 0)
                or (role == "assistant" and not tool_calls)
            ):
                formatted_prompt += f"<|im_start|>{role}\n{content}<|im_end|>\n"
            elif role == "assistant":
                formatted_prompt += f"<|im_start|>{role}"
                if content:
                    formatted_prompt += f"\n{content}"
                for tool_call in tool_calls:
                    if "function" in tool_call:
                        tool_call = tool_call["function"]
                    tool_name = tool_call.get("name", "")
                    arguments = tool_call.get("arguments", {})
                    formatted_prompt += f'\n<tool_call>\n{{"name": "{tool_name}", "arguments": {json.dumps(arguments)}}}\n</tool_call>'
                formatted_prompt += "<|im_end|>\n"
            elif role == "tool":
                if idx == 0 or messages[idx - 1]["role"] != "tool":
                    formatted_prompt += "<|im_start|>user"
                formatted_prompt += f"\n<tool_response>\n{content}\n</tool_response>"
                if idx == len(messages) - 1 or messages[idx + 1]["role"] != "tool":
                    formatted_prompt += "<|im_end|>\n"

        formatted_prompt += "<|im_start|>assistant\n<think>"
        return formatted_prompt

    @override
    def _pre_query_processing_prompting(self, test_entry: dict) -> dict:
        functions: list = test_entry["function"]

        return {"message": [], "function": functions}

    @override
    def _parse_query_response_prompting(self, api_response: Any) -> dict:
        model_response = api_response.choices[0].text
        extracted_tool_calls = self._extract_tool_calls(model_response)
        reasoning_content = ""
        cleaned_response = model_response
        if "</think>" in model_response:
            parts = model_response.split("</think>")
            reasoning_content = parts[0].rstrip("\n").split("<think>")[-1].lstrip("\n")
            cleaned_response = parts[-1].lstrip("\n")

        if len(extracted_tool_calls) > 0:
            model_responses_message_for_chat_history = {
                "role": "assistant",
                "content": "",
                "tool_calls": extracted_tool_calls,
            }

        else:
            model_responses_message_for_chat_history = {
                "role": "assistant",
                "content": cleaned_response,
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
            model_response_data["model_responses_message_for_chat_history"],
        )
        return inference_data

    @staticmethod
    def _extract_tool_calls(input_string):
        pattern = r"<tool_call>(.*?)</tool_call>"
        matches = re.findall(pattern, input_string, re.DOTALL)

        # Process matches into a list of dictionaries
        result = []
        for match in matches:
            try:
                match = json.loads(match)
            except Exception as e:
                print(f"Error parsing tool call: {e}")
                pass
            result.append(match)
        return result
