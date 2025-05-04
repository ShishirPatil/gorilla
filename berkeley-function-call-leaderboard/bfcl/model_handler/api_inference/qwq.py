import os
import time

from bfcl.model_handler.api_inference.openai import OpenAIHandler
from bfcl.model_handler.model_style import ModelStyle
from bfcl.model_handler.utils import (
    combine_consecutive_user_prompts,
    func_doc_language_specific_pre_processing,
    retry_with_backoff,
    system_prompt_pre_processing_chat_model,
)
from openai import OpenAI, RateLimitError
from overrides import override





class QwenAPIHandler(OpenAIHandler):
    def __init__(self, model_name, temperature) -> None:
        super().__init__(model_name, temperature)
        self.model_style = ModelStyle.OpenAI
        self.chat_history = []
        self.client = OpenAI(
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1", api_key=os.getenv("QWEN_API_KEY")
    )



    @override
    def _query_prompting(self, inference_data: dict):
        message: list[dict] = inference_data["message"]
        inference_data["inference_input_log"] = {"message": repr(message)}

        # OpenAI reasoning models don't support temperature parameter
        # Beta limitation: https://platform.openai.com/docs/guides/reasoning/beta-limitations
        #print(inference_data)
        return self.generate_with_backoff(
            messages=inference_data["message"],
            model='qwq-32b',
            stream=True,
        )
    # @override
    # def _pre_query_processing_prompting(self, test_entry: dict) -> dict:
    #     functions: list = test_entry["function"]
    #     test_category: str = test_entry["id"].rsplit("_", 1)[0]

    #     functions = func_doc_language_specific_pre_processing(functions, test_category)

    #     test_entry["question"][0] = system_prompt_pre_processing_chat_model(
    #         test_entry["question"][0], functions, test_category
    #     )

    #     # 'deepseek-reasoner does not support successive user messages, so we need to combine them
    #     for round_idx in range(len(test_entry["question"])):
    #         test_entry["question"][round_idx] = combine_consecutive_user_prompts(
    #             test_entry["question"][round_idx]
    #         )

    #     return {"message": []}


    def stream_parse_query_response_prompting(self, api_response: any):
        #print(api_response)
        # print(type(api_response))
        return {
            "model_responses": api_response,
            "model_responses_message_for_chat_history": {
                "role": "assistant",
                "content": api_response,
            },
            "input_token": 0,
            "output_token": 0,
        }

    def _add_reasoning_content_if_available(
        self, api_response: any, response_data: dict
    ) -> None:
        #message = api_response.choices[0].message
        #if hasattr(message, "reasoning_content"):
        response_data["reasoning_content"] = api_response
        # Reasoning content should not be included in the chat history
        response_data["model_responses_message_for_chat_history"] = {
            "role": "assistant",
            "content": response_data["model_responses"],
        }
    @override
    def _parse_query_response_prompting(self, api_response: any) -> dict:
        #print(api_response)
        reasoning_content = ""  # 完整思考过程
        answer_content = ""  # 完整回复
        is_answering = False  # 是否进入回复阶段
        for chunk in api_response:
            if not chunk.choices:
                # print("\nUsage:")
                # print(chunk.usage)
                continue

            delta = chunk.choices[0].delta

            # 只收集思考内容
            if hasattr(delta, "reasoning_content") and delta.reasoning_content is not None:
                #if not is_answering:
                    #print(delta.reasoning_content, end="", flush=True)
                reasoning_content += delta.reasoning_content

            # 收到content，开始进行回复
            if hasattr(delta, "content") and delta.content:
                if not is_answering:
                    #print("\n" + "=" * 20 + "完整回复" + "=" * 20 + "\n")
                    is_answering = True
                #print(delta.content, end="", flush=True)
                answer_content += delta.content
        response_data = self.stream_parse_query_response_prompting(answer_content)

        self._add_reasoning_content_if_available(reasoning_content, response_data)
        return response_data
