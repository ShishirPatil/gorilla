import json
import os
import time

from anthropic import Anthropic, RateLimitError
from anthropic.types import TextBlock, ToolUseBlock
from bfcl.model_handler.base_handler import BaseHandler
from bfcl.constants.type_mappings import GORILLA_TO_OPENAPI
from bfcl.model_handler.model_style import ModelStyle
from bfcl.model_handler.utils import (
    ast_parse,
    combine_consecutive_user_prompts,
    convert_system_prompt_into_user_prompt,
    convert_to_function_call,
    convert_to_tool,
    extract_system_prompt,
    format_execution_results_prompting,
    func_doc_language_specific_pre_processing,
    retry_with_backoff,
    system_prompt_pre_processing_chat_model,
)
from bfcl.utils import is_multi_turn


class ClaudeHandler(BaseHandler):
    def __init__(self, model_name, temperature) -> None:
        super().__init__(model_name, temperature)
        self.model_style = ModelStyle.Anthropic
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    def decode_ast(self, result, language="Python"):
        if "FC" not in self.model_name:
            func = result
            if " " == func[0]:
                func = func[1:]
            if not func.startswith("["):
                func = "[" + func
            if not func.endswith("]"):
                func = func + "]"
            decode_output = ast_parse(func, language)
            return decode_output

        else:
            decoded_output = []
            for invoked_function in result:
                name = list(invoked_function.keys())[0]
                params = json.loads(invoked_function[name])
                decoded_output.append({name: params})
            return decoded_output

    def decode_execute(self, result):
        if "FC" not in self.model_name:
            func = result
            if " " == func[0]:
                func = func[1:]
            if not func.startswith("["):
                func = "[" + func
            if not func.endswith("]"):
                func = func + "]"
            decode_output = ast_parse(func)
            execution_list = []
            for function_call in decode_output:
                for key, value in function_call.items():
                    execution_list.append(
                        f"{key}({','.join([f'{k}={repr(v)}' for k, v in value.items()])})"
                    )
            return execution_list

        else:
            function_call = convert_to_function_call(result)
            return function_call

    @retry_with_backoff(error_type=RateLimitError)
    def generate_with_backoff(self, **kwargs):
        start_time = time.time()
        api_response = self.client.messages.create(**kwargs)
        end_time = time.time()

        return api_response, end_time - start_time

    #### FC methods ####

    def _query_FC(self, inference_data: dict):
        inference_data["inference_input_log"] = {
            "message": repr(inference_data["message"]),
            "tools": inference_data["tools"],
        }
        messages = inference_data["message"]

        if inference_data["caching_enabled"]:
            # Only add cache control to the last two user messages
            # Remove previously set cache control flags from all user messages except the last two
            count = 0
            for message in reversed(messages):
                if message["role"] == "user":
                    if count < 2:
                        message["content"][0]["cache_control"] = {"type": "ephemeral"}
                    else:
                        if "cache_control" in message["content"][0]:
                            del message["content"][0]["cache_control"]
                    count += 1

        return self.generate_with_backoff(
            model=self.model_name.strip("-FC"),
            max_tokens=(
                4096 if "claude-3-opus-20240229" in self.model_name else 8192
            ),  # 3.5 Sonnet has a higher max token limit
            tools=inference_data["tools"],
            messages=messages,
        )

    def _pre_query_processing_FC(self, inference_data: dict, test_entry: dict) -> dict:
        for round_idx in range(len(test_entry["question"])):
            test_entry["question"][round_idx] = convert_system_prompt_into_user_prompt(
                test_entry["question"][round_idx]
            )
            test_entry["question"][round_idx] = combine_consecutive_user_prompts(
                test_entry["question"][round_idx]
            )
        inference_data["message"] = []

        test_entry_id: str = test_entry["id"]
        test_category: str = test_entry_id.rsplit("_", 1)[0]
        # caching enabled only for multi_turn category
        inference_data["caching_enabled"] = is_multi_turn(test_category)

        return inference_data

    def _compile_tools(self, inference_data: dict, test_entry: dict) -> dict:
        functions: list = test_entry["function"]
        test_category: str = test_entry["id"].rsplit("_", 1)[0]

        functions = func_doc_language_specific_pre_processing(functions, test_category)
        tools = convert_to_tool(functions, GORILLA_TO_OPENAPI, self.model_style)

        if inference_data["caching_enabled"]:
            # First time compiling tools, so adding cache control flag to the last tool
            if "tools" not in inference_data:
                tools[-1]["cache_control"] = {"type": "ephemeral"}
            # This is the situation where the tools are already compiled and we are adding more tools to the existing tools (in miss_func category)
            # We add the cache control flag to the last tool in the previous existing tools and the last tool in the new tools to maximize cache hit
            else:
                existing_tool_len = len(inference_data["tools"])
                tools[existing_tool_len - 1]["cache_control"] = {"type": "ephemeral"}
                tools[-1]["cache_control"] = {"type": "ephemeral"}

        inference_data["tools"] = tools

        return inference_data

    def _parse_query_response_FC(self, api_response: any) -> dict:
        text_outputs = []
        tool_call_outputs = []
        tool_call_ids = []

        for content in api_response.content:
            if isinstance(content, TextBlock):
                text_outputs.append(content.text)
            elif isinstance(content, ToolUseBlock):
                tool_call_outputs.append({content.name: json.dumps(content.input)})
                tool_call_ids.append(content.id)

        model_responses = tool_call_outputs if tool_call_outputs else text_outputs

        model_responses_message_for_chat_history = api_response.content

        return {
            "model_responses": model_responses,
            "model_responses_message_for_chat_history": model_responses_message_for_chat_history,
            "tool_call_ids": tool_call_ids,
            "input_token": api_response.usage.input_tokens,
            "output_token": api_response.usage.output_tokens,
        }

    def add_first_turn_message_FC(
        self, inference_data: dict, first_turn_message: list[dict]
    ) -> dict:
        for message in first_turn_message:
            message["content"] = [{"type": "text", "text": message["content"]}]
        inference_data["message"].extend(first_turn_message)
        return inference_data

    def _add_next_turn_user_message_FC(
        self, inference_data: dict, user_message: list[dict]
    ) -> dict:
        for message in user_message:
            message["content"] = [{"type": "text", "text": message["content"]}]
        inference_data["message"].extend(user_message)
        return inference_data

    def _add_assistant_message_FC(
        self, inference_data: dict, model_response_data: dict
    ) -> dict:
        inference_data["message"].append(
            {
                "role": "assistant",
                "content": model_response_data["model_responses_message_for_chat_history"],
            }
        )
        return inference_data

    def _add_execution_results_FC(
        self,
        inference_data: dict,
        execution_results: list[str],
        model_response_data: dict,
    ) -> dict:
        # Claude don't use the tool role; it uses the user role to send the tool output
        tool_message = {
            "role": "user",
            "content": [],
        }
        for execution_result, tool_call_id in zip(
            execution_results, model_response_data["tool_call_ids"]
        ):
            tool_message["content"].append(
                {
                    "type": "tool_result",
                    "content": execution_result,
                    "tool_use_id": tool_call_id,
                }
            )

        inference_data["message"].append(tool_message)

        return inference_data

    #### Prompting methods ####

    def _query_prompting(self, inference_data: dict):
        inference_data["inference_input_log"] = {
            "message": repr(inference_data["message"]),
            "system_prompt": inference_data["system_prompt"],
        }

        if inference_data["caching_enabled"]:
            # Cache the system prompt
            inference_data["system_prompt"][0]["cache_control"] = {"type": "ephemeral"}
            # Add cache control to the last two user messages as well
            count = 0
            for message in reversed(inference_data["message"]):
                if message["role"] == "user":
                    if count < 2:
                        message["content"][0]["cache_control"] = {"type": "ephemeral"}
                    else:
                        if "cache_control" in message["content"][0]:
                            del message["content"][0]["cache_control"]
                    count += 1

        return self.generate_with_backoff(
            model=self.model_name,
            max_tokens=(4096 if "claude-3-opus-20240229" in self.model_name else 8192),
            temperature=self.temperature,
            system=inference_data["system_prompt"],
            messages=inference_data["message"],
        )

    def _pre_query_processing_prompting(self, test_entry: dict) -> dict:
        functions: list = test_entry["function"]
        test_entry_id: str = test_entry["id"]
        test_category: str = test_entry_id.rsplit("_", 1)[0]

        functions = func_doc_language_specific_pre_processing(functions, test_category)

        test_entry["question"][0] = system_prompt_pre_processing_chat_model(
            test_entry["question"][0], functions, test_category
        )
        # Claude takes in system prompt in a specific field, not in the message field, so we don't need to add it to the message
        system_prompt = extract_system_prompt(test_entry["question"][0])

        system_prompt = [{"type": "text", "text": system_prompt}]

        # Claude doesn't allow consecutive user prompts, so we need to combine them
        for round_idx in range(len(test_entry["question"])):
            test_entry["question"][round_idx] = combine_consecutive_user_prompts(
                test_entry["question"][round_idx]
            )

        test_entry_id: str = test_entry["id"]
        test_category: str = test_entry_id.rsplit("_", 1)[0]
        # caching enabled only for multi_turn category
        caching_enabled: bool = is_multi_turn(test_category)

        return {
            "message": [],
            "system_prompt": system_prompt,
            "caching_enabled": caching_enabled,
        }

    def _parse_query_response_prompting(self, api_response: any) -> dict:
        return {
            "model_responses": api_response.content[0].text,
            "input_token": api_response.usage.input_tokens,
            "output_token": api_response.usage.output_tokens,
        }

    def add_first_turn_message_prompting(
        self, inference_data: dict, first_turn_message: list[dict]
    ) -> dict:
        for message in first_turn_message:
            message["content"] = [{"type": "text", "text": message["content"]}]
        inference_data["message"].extend(first_turn_message)
        return inference_data

    def _add_next_turn_user_message_prompting(
        self, inference_data: dict, user_message: list[dict]
    ) -> dict:
        for message in user_message:
            message["content"] = [{"type": "text", "text": message["content"]}]
        inference_data["message"].extend(user_message)
        return inference_data

    def _add_assistant_message_prompting(
        self, inference_data: dict, model_response_data: dict
    ) -> dict:
        inference_data["message"].append(
            {
                "role": "assistant",
                "content": model_response_data["model_responses"],
            }
        )
        return inference_data

    def _add_execution_results_prompting(
        self, inference_data: dict, execution_results: list[str], model_response_data: dict
    ) -> dict:
        formatted_results_message = format_execution_results_prompting(
            inference_data, execution_results, model_response_data
        )
        inference_data["message"].append(
            {
                "role": "user",
                "content": [{"type": "text", "text": formatted_results_message}],
            }
        )

        return inference_data
