import os
import time

import boto3
from bfcl_eval.model_handler.base_handler import BaseHandler
from bfcl_eval.constants.type_mappings import GORILLA_TO_OPENAPI
from bfcl_eval.model_handler.model_style import ModelStyle
from bfcl_eval.model_handler.utils import (
    combine_consecutive_user_prompts,
    convert_to_function_call,
    convert_to_tool,
    extract_system_prompt,
    func_doc_language_specific_pre_processing,
    retry_with_backoff,
)


class NovaHandler(BaseHandler):
    def __init__(self, model_name, temperature) -> None:
        super().__init__(model_name, temperature)
        self.model_style = ModelStyle.AMAZON
        self.is_fc_model = True
        self.client = boto3.client(
            service_name="bedrock-runtime",
            region_name="us-east-1",  # Currently only available in us-east-1
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        )

    def decode_ast(self, result, language="Python"):
        if type(result) != list:
            return []
        return result

    def decode_execute(self, result):
        if type(result) != list:
            return []
        return convert_to_function_call(result)

    @retry_with_backoff(error_message_pattern=r".*\(ThrottlingException\).*")
    def generate_with_backoff(self, **kwargs):
        start_time = time.time()
        api_response = self.client.converse(**kwargs)
        end_time = time.time()

        return api_response, end_time - start_time

    #### FC methods ####

    def _query_FC(self, inference_data: dict):
        message: list[dict] = inference_data["message"]
        tools = inference_data["tools"]

        if "system_prompt" in inference_data:
            system_prompt = inference_data["system_prompt"]
        else:
            system_prompt = []

        inference_data["inference_input_log"] = {
            "message": repr(message),
            "tools": tools,
            "system_prompt": system_prompt,
        }

        if len(tools) > 0:
            # toolConfig requires minimum number of 1 item.
            return self.generate_with_backoff(
                modelId=f"us.amazon.{self.model_name.replace('.', ':')}",
                messages=message,
                system=system_prompt,
                inferenceConfig={"temperature": self.temperature},
                toolConfig={"tools": tools},
            )
        else:
            return self.generate_with_backoff(
                modelId=f"us.amazon.{self.model_name.replace('.', ':')}",
                messages=message,
                system=system_prompt,
                inferenceConfig={"temperature": self.temperature},
            )

    def _pre_query_processing_FC(self, inference_data: dict, test_entry: dict) -> dict:
        for round_idx in range(len(test_entry["question"])):
            test_entry["question"][round_idx] = combine_consecutive_user_prompts(
                test_entry["question"][round_idx]
            )

        inference_data["message"] = []

        system_prompt = extract_system_prompt(test_entry["question"][0])
        if system_prompt:
            inference_data["system_prompt"] = [{"text": system_prompt}]

        return inference_data

    def _compile_tools(self, inference_data: dict, test_entry: dict) -> dict:
        functions: list = test_entry["function"]
        test_category: str = test_entry["id"].rsplit("_", 1)[0]

        functions = func_doc_language_specific_pre_processing(functions, test_category)
        tools = convert_to_tool(functions, GORILLA_TO_OPENAPI, self.model_style)

        inference_data["tools"] = tools

        return inference_data

    def _parse_query_response_FC(self, api_response: any) -> dict:
        model_responses_message_for_chat_history = api_response["output"]["message"]

        if api_response["stopReason"] == "tool_use":
            model_responses = []
            tool_call_ids = []
            """
            Note: Not every response will have a toolUse, so we skip any content that does not have a toolUse
            Example API response:
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [
                        {"text": "`"},
                        {
                            "toolUse": {
                                "toolUseId": "tooluse_kF0BECcNSd6WITS9W4afbQ",
                                "name": "calculate_triangle_area",
                                "input": {"base": 10, "height": 5},
                            }
                        },
                        {"text": "`"},
                    ],
                }
            },
            """
            for func_call in api_response["output"]["message"]["content"]:
                if "toolUse" not in func_call:
                    continue

                func_call = func_call["toolUse"]
                func_name = func_call["name"]
                func_args = func_call["input"]
                model_responses.append({func_name: func_args})
                tool_call_ids.append(func_call["toolUseId"])

        else:
            model_responses = api_response["output"]["message"]["content"][0]["text"]
            tool_call_ids = []

        return {
            "model_responses": model_responses,
            "model_responses_message_for_chat_history": model_responses_message_for_chat_history,
            "tool_call_ids": tool_call_ids,
            "input_token": api_response["usage"]["inputTokens"],
            "output_token": api_response["usage"]["outputTokens"],
        }

    def add_first_turn_message_FC(
        self, inference_data: dict, first_turn_message: list[dict]
    ) -> dict:
        for message in first_turn_message:
            message["content"] = [{"text": message["content"]}]
        inference_data["message"].extend(first_turn_message)
        return inference_data

    def _add_next_turn_user_message_FC(
        self, inference_data: dict, user_message: list[dict]
    ) -> dict:
        for message in user_message:
            message["content"] = [{"text": message["content"]}]
        inference_data["message"].extend(user_message)
        return inference_data

    def _add_assistant_message_FC(
        self, inference_data: dict, model_response_data: dict
    ) -> dict:
        inference_data["message"].append(
            model_response_data["model_responses_message_for_chat_history"]
        )
        return inference_data

    def _add_execution_results_FC(
        self,
        inference_data: dict,
        execution_results: list[str],
        model_response_data: dict,
    ) -> dict:
        # Nova use the `user` role for the tool result message
        tool_message = {
            "role": "user",
            "content": [],
        }
        for execution_result, tool_call_id in zip(
            execution_results, model_response_data["tool_call_ids"]
        ):
            tool_message["content"].append(
                {
                    "toolResult": {
                        "toolUseId": tool_call_id,
                        # Nova models supports json or text content
                        # Our pipeline force execution results to be text for all models
                        # So we will just use text here to be consistent
                        "content": [{"text": execution_result}],
                    }
                }
            )

        inference_data["message"].append(tool_message)

        return inference_data
