import json
import os
from time import time
from typing import Optional

from ibm_watsonx_ai import APIClient
from ibm_watsonx_ai.foundation_models.model import ModelInference

from bfcl.constants.type_mappings import GORILLA_TO_OPENAPI
from bfcl.model_handler.base_handler import BaseHandler
from bfcl.model_handler.model_style import ModelStyle
from bfcl.model_handler.utils import (
    convert_to_tool,
    default_decode_ast_prompting,
    default_decode_execute_prompting,
    format_execution_results_prompting,
    func_doc_language_specific_pre_processing,
    system_prompt_pre_processing_chat_model,
)


# List of models which support function calling:
fc_models = [
    "ibm/granite-3-3-8b-instruct",
    "ibm/granite-3-2-8b-instruct",
    "ibm/granite-3-8b-instruct",
    "meta-llama/llama-4-maverick-17b-128e-instruct-fp8",
    "meta-llama/llama-3-3-70b-instruct",
    "mistralai/mistral-large",
    "mistralai/mistral-medium-2505",
    "mistralai/mistral-small-3-1-24b-instruct-2503",
]


class WatsonxAIHandler(BaseHandler):
    def __init__(self, model_name: str, temperature: float) -> None:
        super().__init__(model_name, temperature)

        self.model_style = ModelStyle.WATSONX_AI

        credentials = self.read_wx_credentials()
        self.client = APIClient(
            project_id=credentials.pop("project_id"),
            space_id=credentials.pop("space_id"),
            credentials=credentials,
        )

        model_id = model_name.replace("ibm-", "")

        self.model = ModelInference(
            api_client=self.client,
            model_id=model_id,
        )

        self.is_fc_model = model_id in fc_models

    @staticmethod
    def read_wx_credentials() -> dict[str, str]:
        url = os.getenv("WX_AI_URL")
        apikey = os.getenv("WX_AI_API_KEY")
        project_id = os.getenv("WX_AI_PROJECT_ID")
        space_id = os.getenv("WX_AI_SPACE_ID")

        if not (url and apikey and (project_id or space_id)):
            raise ValueError(
                "If you want to use watsonx.ai, you must set `WX_AI_URL`, "
                "`WX_AI_API_KEY` and either `WX_AI_PROJECT_ID` or "
                "`WX_AI_SPACE_ID` environment variables."
            )

        if project_id and space_id:
            raise ValueError(
                "You must specify either `WX_AI_PROJECT_ID` or `WX_AI_SPACE_ID`, "
                "however, both were given."
            )

        return {
            "url": url,
            "apikey": apikey,
            "project_id": project_id if project_id else None,
            "space_id": space_id if space_id else None,
        }

    def _query_FC(self, inference_data: dict) -> tuple[dict, float]:
        message: list[dict] = inference_data["message"]
        tools: Optional[list[dict]] = inference_data["tools"]

        t0 = time()
        response = self.model.chat(
            messages=message,
            tools=tools,
            params={
                "temperature": self.temperature
            },
        )
        t1 = time()

        return response, t1 - t0

    def _pre_query_processing_FC(self, inference_data: dict, test_entry: dict) -> dict:
        inference_data["message"] = []
        return inference_data

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
        return inference_data

    def _add_execution_results_FC(
        self, inference_data: dict,
        execution_results: list[str],
        model_response_data: dict,
    ) -> dict:
        for execution_result, tool_call_id in zip(
            execution_results, model_response_data["tool_call_ids"]
        ):
            tool_message = {
                "role": "tool",
                "content": execution_result,
                "tool_call_id": tool_call_id,
            }
            inference_data["message"].append(tool_message)

        return inference_data

    def _parse_query_response_FC(self, api_response: dict) -> dict:
        output = api_response["choices"][0]["message"]
        is_tool_call = (
            "tool_calls" in output
            or api_response["choices"][0]["finish_reason"] == "tool_calls"
        )

        prediction: list[dict] | str = (
            [
                {
                    key: value for key, value in tool_call.items()
                    if key not in ("id", "type")
                }
                for tool_call in output.get("tool_calls", [])
            ]
            if is_tool_call
            else output.get("content", "")
        )
        tool_call_ids: Optional[list[str]] = (
            [tool_call["id"] for tool_call in output.get("tool_calls", [])]
            if is_tool_call
            else None
        )

        return {
            "model_responses": prediction,
            "input_token": api_response["usage"]["prompt_tokens"],
            "output_token": api_response["usage"]["completion_tokens"],
            "tool_call_ids": tool_call_ids,
        }

    def _query_prompting(self, inference_data: dict) -> tuple[dict, float]:
        message: list[dict] = inference_data["message"]

        t0 = time()
        response = self.model.chat(
            messages=message,
            params={
                "temperature": self.temperature
            },
        )
        t1 = time()

        return response, t1 - t0

    def _pre_query_processing_prompting(self, test_entry: dict) -> dict:
        functions: list = test_entry["function"]
        test_category: str = test_entry["id"].rsplit("_", 1)[0]

        functions = func_doc_language_specific_pre_processing(functions, test_category)

        test_entry["question"][0] = system_prompt_pre_processing_chat_model(
            test_entry["question"][0], functions, test_category
        )

        return {"message": []}

    def _parse_query_response_prompting(self, api_response: any) -> dict:
        return {
            "model_responses": api_response["choices"][0]["message"]["content"],
            "input_token": api_response["usage"]["prompt_tokens"],
            "output_token": api_response["usage"]["completion_tokens"],
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
            model_response_data["model_responses_message_for_chat_history"]
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

    def _compile_tools(self, inference_data: dict, test_entry: dict) -> dict:
        functions: list = test_entry["function"]
        test_category: str = test_entry["id"].rsplit("_", 1)[0]

        functions = func_doc_language_specific_pre_processing(functions, test_category)
        tools = convert_to_tool(functions, GORILLA_TO_OPENAPI, self.model_style)

        inference_data["tools"] = tools

        return inference_data

    def decode_ast(self, result, language="Python"):
        if self.is_fc_model:
            return [
                {
                    tool_call["function"]["name"]: json.loads(
                        tool_call["function"]["arguments"]
                    )
                }
                for tool_call in result
            ]

        default_decode_ast_prompting(result, language)

    def decode_execute(self, result):
        if self.is_fc_model:
            decoded_result = []

            for tool_call in result:
                func = tool_call.get("function")
                if not func:
                    decoded_result.append(tool_call)
                    continue

                func_name, func_args = func.values()
                arg_str = ",".join(
                    f"{arg_name}={repr(arg_val)}"
                    for arg_name, arg_val in json.loads(func_args).items()
                )
                decoded_result.append(f"{func_name}({arg_str})")

            return decoded_result

        default_decode_execute_prompting(result)
