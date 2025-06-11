import os

from bfcl_eval.model_handler.api_inference.openai import OpenAIHandler
from bfcl_eval.model_handler.model_style import ModelStyle
from openai import OpenAI
from overrides import override


class QwenAPIHandler(OpenAIHandler):
    """
    This is the OpenAI-compatible API handler with streaming enabled.

    For Qwen's hosted service, the QwQ series, and Qwen3 series with reasoning enabled only support streaming response for both prompting and FC mode.
    So to make things simple, we will just use streaming response for all Qwen model variants.

    """

    def __init__(self, model_name, temperature) -> None:
        super().__init__(model_name, temperature)
        self.model_style = ModelStyle.OpenAI
        self.client = OpenAI(
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            api_key=os.getenv("QWEN_API_KEY"),
        )

    #### FC methods ####

    @override
    def _query_FC(self, inference_data: dict):
        message: list[dict] = inference_data["message"]
        tools = inference_data["tools"]
        inference_data["inference_input_log"] = {"message": repr(message), "tools": tools}

        return self.generate_with_backoff(
            messages=inference_data["message"],
            model=self.model_name.replace("-FC", ""),
            tools=tools,
            parallel_tool_calls=True,
            extra_body={
                "enable_thinking": True
            },
            stream=True,
            stream_options={
                "include_usage": True
            },  # retrieving token usage for stream response
        )

    @override
    def _parse_query_response_FC(self, api_response: any) -> dict:

        reasoning_content = ""
        answer_content = ""
        tool_info = []
        for chunk in api_response:
            if not chunk.choices:
                continue

            delta = chunk.choices[0].delta

            if hasattr(delta, "reasoning_content") and delta.reasoning_content is not None:
                reasoning_content += delta.reasoning_content

            if hasattr(delta, "content") and delta.content:
                answer_content += delta.content

            if hasattr(delta, "tool_calls") and delta.tool_calls:
                for tool_call in delta.tool_calls:
                    # Index for parallel tool calls
                    index = tool_call.index

                    # Dynamically extend the tool info storage list
                    while len(tool_info) <= index:
                        tool_info.append({})

                    # Aggregate the streaming chunks of each field
                    if tool_call.id:
                        tool_info[index]["id"] = (
                            tool_info[index].get("id", "") + tool_call.id
                        )
                    if tool_call.function and tool_call.function.name:
                        tool_info[index]["name"] = (
                            tool_info[index].get("name", "") + tool_call.function.name
                        )
                    if tool_call.function and tool_call.function.arguments:
                        tool_info[index]["arguments"] = (
                            tool_info[index].get("arguments", "")
                            + tool_call.function.arguments
                        )

        tool_call_ids = []
        for item in tool_info:
            tool_call_ids.append(item["id"])

        if len(tool_info) > 0:
            # Build tool_calls structure required by OpenAI-compatible API
            tool_calls_for_history = []
            for item in tool_info:
                tool_calls_for_history.append(
                    {
                        "id": item["id"],
                        "type": "function",
                        "function": {
                            "name": item["name"],
                            "arguments": item["arguments"],
                        },
                    }
                )

            model_response = [{item["name"]: item["arguments"]} for item in tool_info]
            model_response_message_for_chat_history = {
                "role": "assistant",
                "content": None,
                "tool_calls": tool_calls_for_history,
            }
            # Attach reasoning content so that it can be passed to the next turn
            if reasoning_content:
                model_response_message_for_chat_history["reasoning_content"] = reasoning_content
        else:
            model_response = answer_content
            model_response_message_for_chat_history = {
                "role": "assistant",
                "content": answer_content,
            }
            # Attach reasoning content so that it can be passed to the next turn
            if reasoning_content:
                model_response_message_for_chat_history["reasoning_content"] = reasoning_content

        response_data = {
            "model_responses": model_response,
            "model_responses_message_for_chat_history": model_response_message_for_chat_history,
            "reasoning_content": reasoning_content,
            "tool_call_ids": tool_call_ids,
            # chunk is the last chunk of the stream response
            "input_token": chunk.usage.prompt_tokens,
            "output_token": chunk.usage.completion_tokens,
        }

        if not reasoning_content:
            del response_data["reasoning_content"]

        return response_data

    #### Prompting methods ####

    @override
    def _query_prompting(self, inference_data: dict):
        message: list[dict] = inference_data["message"]
        inference_data["inference_input_log"] = {"message": repr(message)}

        return self.generate_with_backoff(
            messages=inference_data["message"],
            model=self.model_name,
            extra_body={
                "enable_thinking": True
            },
            stream=True,
            stream_options={
                "include_usage": True
            },  # retrieving token usage for stream response
        )

    @override
    def _parse_query_response_prompting(self, api_response: any) -> dict:

        reasoning_content = ""
        answer_content = ""
        for chunk in api_response:
            if not chunk.choices:
                continue

            delta = chunk.choices[0].delta

            if hasattr(delta, "reasoning_content") and delta.reasoning_content is not None:
                reasoning_content += delta.reasoning_content

            if hasattr(delta, "content") and delta.content:
                answer_content += delta.content

        response_data = {
            "model_responses": answer_content,
            "model_responses_message_for_chat_history": {
                "role": "assistant",
                "content": answer_content,
            },
            "reasoning_content": reasoning_content,
            # chunk is the last chunk of the stream response
            "input_token": chunk.usage.prompt_tokens,
            "output_token": chunk.usage.completion_tokens,
        }

        # Attach reasoning content to the assistant message for the next turn if present
        if reasoning_content:
            response_data["model_responses_message_for_chat_history"][
                "reasoning_content"
            ] = reasoning_content

        if not reasoning_content:
            del response_data["reasoning_content"]

        return response_data
