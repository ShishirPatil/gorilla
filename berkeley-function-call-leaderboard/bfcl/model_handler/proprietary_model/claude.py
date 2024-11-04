import json
import os
import logging
from anthropic import Anthropic
from transformers import GPT2TokenizerFast

from anthropic.types import TextBlock, ToolUseBlock
from bfcl.model_handler.base_handler import BaseHandler
from bfcl.model_handler.constant import GORILLA_TO_OPENAPI
from bfcl.model_handler.model_style import ModelStyle
from bfcl.model_handler.utils import (
    ast_parse,
    combine_consecutive_user_prompts,
    convert_system_prompt_into_user_prompt,
    convert_to_function_call,
    convert_to_tool,
    format_execution_results_prompting,
    extract_system_prompt,
    func_doc_language_specific_pre_processing,
    system_prompt_pre_processing_chat_model,
)

os.environ["TOKENIZERS_PARALLELISM"] = "false"

class ClaudeHandler(BaseHandler):
    def __init__(self, model_name, temperature) -> None:
        super().__init__(model_name, temperature)
        self.model_style = ModelStyle.Anthropic
        self.client = Anthropic(os.getenv("ANTHROPIC_API_KEY"))
        #print(os.getenv("ANTHROPIC_API_KEY"))

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

    #### FC methods ####

    def _query_FC(self, inference_data: dict):
        inference_data["inference_input_log"] = {
            "message": repr(inference_data["message"]),
            "tools": inference_data["tools"],
        }

        tools = inference_data["tools"]

        if tools:
            # Use a tokenizer to calculate token counts
            tokenizer = GPT2TokenizerFast.from_pretrained("gpt2")

            cumulative_token_count = 0
            cacheable_tools = []
            cache_control_applied = False

            for idx, tool in enumerate(tools):
                tool_text = json.dumps(tool)
                token_count = len(tokenizer.encode(tool_text))
                cumulative_token_count += token_count
                cacheable_tools.append(tool)

                # Apply cache_control when cumulative tokens exceed 1024
                if not cache_control_applied and cumulative_token_count >= 1024:
                    cacheable_tools[idx]['cache_control'] = {'type': 'ephemeral'}
                    cache_control_applied = True
                    print(f"Caching tools up to index {idx} with cumulative tokens {cumulative_token_count}")
                    break  # Only one cache breakpoint needed here

            if not cache_control_applied:
                # If cumulative tokens never reached 1024, no caching will occur
                print("Cumulative token count did not reach 1024. No caching applied.")
        else:
            cacheable_tools = tools

        response = self.client.beta.prompt_caching.messages.create(
            model=self.model_name.strip("-FC"),
            max_tokens=(
                8192 if "claude-3-5-sonnet-20240620" in self.model_name else 4096
            ),
            tools=cacheable_tools,
            messages=inference_data["message"]
        )

        # Corrected way to access usage attributes
        usage = response.usage
        if usage:
            print(f"Cache Creation Tokens: {getattr(usage, 'cache_creation_input_tokens', 0)}")
            print(f"Cache Read Tokens: {getattr(usage, 'cache_read_input_tokens', 0)}")
            print(f"Regular Input Tokens: {getattr(usage, 'input_tokens', 0)}")
            print(f"Output Tokens: {getattr(usage, 'output_tokens', 0)}")

        return response



    def _pre_query_processing_FC(self, inference_data: dict, test_entry: dict) -> dict:
        for round_idx in range(len(test_entry["question"])):
            test_entry["question"][round_idx] = convert_system_prompt_into_user_prompt(
                test_entry["question"][round_idx]
            )
            test_entry["question"][round_idx] = combine_consecutive_user_prompts(
                test_entry["question"][round_idx]
            )

        inference_data["message"] = []
        return inference_data

    def _compile_tools(self, inference_data: dict, test_entry: dict) -> dict:
        functions: list = test_entry["function"]
        test_category: str = test_entry["id"].rsplit("_", 1)[0]

        functions = func_doc_language_specific_pre_processing(functions, test_category)
        tools = convert_to_tool(functions, GORILLA_TO_OPENAPI, self.model_style)

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
        inference_data["message"].extend(first_turn_message)
        return inference_data

    def _add_next_turn_user_message_FC(
        self, inference_data: dict, user_message: list[dict]
    ) -> dict:
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

         # Use the GPT2 tokenizer to calculate token counts
        tokenizer = GPT2TokenizerFast.from_pretrained("gpt2")

        system_prompt_text = inference_data["system_prompt"]
        token_count = len(tokenizer.encode(system_prompt_text))

        system_prompt = [
            {
                "type": "text",
                "text": system_prompt_text
            }
        ]

        # Decide whether to apply caching based on token count
        if token_count >= 1024:
            # Add 'cache_control' to the system prompt
            system_prompt[0]['cache_control'] = {"type": "ephemeral"}
            print(f"Caching system prompt with token count: {token_count}")
        else:
            print(f"System prompt token count ({token_count}) is less than 1024. No caching applied.")


        # Use the beta prompt caching endpoint
        api_response = self.client.beta.prompt_caching.messages.create(
            model=self.model_name,
            max_tokens=(
                8192 if "claude-3-5-sonnet-20240620" in self.model_name else 4096
            ),
            temperature=self.temperature,
            system=system_prompt,
            messages=inference_data["message"]
        )

        # Log caching metrics
        usage = api_response.usage
        if usage:
            print(f"Cache Creation Tokens: {getattr(usage, 'cache_creation_input_tokens', 0)}")
            print(f"Cache Read Tokens: {getattr(usage, 'cache_read_input_tokens', 0)}")
            print(f"Regular Input Tokens: {getattr(usage, 'input_tokens', 0)}")
            print(f"Output Tokens: {getattr(usage, 'output_tokens', 0)}")

        return api_response
        

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

        # Claude doesn't allow consecutive user prompts, so we need to combine them
        for round_idx in range(len(test_entry["question"])):
            test_entry["question"][round_idx] = combine_consecutive_user_prompts(
                test_entry["question"][round_idx]
            )

        return {"message": [], "system_prompt": system_prompt}

    def _parse_query_response_prompting(self, api_response: any) -> dict:
        return {
            "model_responses": api_response.content[0].text,
            "input_token": api_response.usage.input_tokens,
            "output_token": api_response.usage.output_tokens,
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
            {"role": "user", "content": formatted_results_message}
        )

        return inference_data

