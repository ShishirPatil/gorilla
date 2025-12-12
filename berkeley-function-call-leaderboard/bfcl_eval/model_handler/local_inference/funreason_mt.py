from bfcl_eval.model_handler.local_inference.base_oss_handler import OSSHandler
from overrides import override
import time
from typing import Any
import json



class FunReasonMTHandler(OSSHandler):
    def __init__(self, model_name, temperature) -> None:
        super().__init__(model_name, temperature)
        self.is_fc_model = False
        self.top_p = 0.7
        self.max_output_len = 20000
        self.max_context_length = 247000

    @override
    def _query_prompting(self, inference_data: dict):
        print("overide _query_prompting")
        # We use the OpenAI Completions API
        function: list[dict] = inference_data["function"]
        message: list[dict] = inference_data["message"]

        formatted_prompt: str = self._format_prompt(message, function)
        inference_data["inference_input_log"] = {"formatted_prompt": formatted_prompt}

        # Tokenize the formatted prompt to get token count
        input_token_count = len(self.tokenizer.tokenize(formatted_prompt))

        # Determine the number of tokens to request. Cap it at 4096 if the model has a larger limit.
        if self.max_context_length < input_token_count + 2:
            # If the prompt is already at the max length, just request 1000 token, we will get an error anyway
            leftover_tokens_count = 1000
        else:
            leftover_tokens_count = min(
                self.max_output_len,
                self.max_context_length - input_token_count - 2,
            )

        extra_body = {}
        if hasattr(self, "stop_token_ids"):
            extra_body["stop_token_ids"] = self.stop_token_ids
        if hasattr(self, "skip_special_tokens"):
            extra_body["skip_special_tokens"] = self.skip_special_tokens

        start_time = time.time()
        if len(extra_body) > 0:
            api_response = self.client.completions.create(
                model=self.model_path_or_id,
                temperature=self.temperature,
                top_p=self.top_p,
                prompt=formatted_prompt,
                max_tokens=leftover_tokens_count,
                extra_body=extra_body,
                timeout=72000,  # Avoid timeout errors
            )
        else:
            api_response = self.client.completions.create(
                model=self.model_path_or_id,
                temperature=self.temperature,
                top_p=self.top_p,
                prompt=formatted_prompt,
                max_tokens=leftover_tokens_count,
                timeout=72000,  # Avoid timeout errors
            )
        end_time = time.time()

        return api_response, end_time - start_time
    
    def _process_tool_response(self, tool_response_lst):
        processed_tool_response = []
        for tool_response in tool_response_lst:
            processed_tool_response.append(tool_response)
        return processed_tool_response

    @override
    def _format_prompt(self, messages, function):
        new_messages = []
        tool_content = []
        for idx, message in enumerate(messages):
            role = message["role"]
            content = message["content"]
            if role != "tool":
                if len(tool_content) != 0:
                    tool_message = {
                        "role": "tool",
                        "content": str(tool_content),
                    }
                    new_messages.append(tool_message)
                    tool_content = []
                new_messages.append(message)
            else:
                tool_content.append(content)
        if len(tool_content) != 0:
            tool_message = {
                "role": "tool",
                "content": str(tool_content),
            }
            new_messages.append(tool_message)
            tool_content = []
        print("new_messages", new_messages)
        formatted_prompt = self.tokenizer.apply_chat_template(
            new_messages, tokenize=False, add_generation_prompt=True
        )
        formatted_prompt += "<think>"
        print("formated_prompt", formatted_prompt)
        return formatted_prompt

    @override
    def _parse_query_response_prompting(self, api_response: Any) -> dict:
        reasoning_content = ""
        model_response = api_response.choices[0].text
        cleaned_response = ""
        reasoning_content = ""
        cleaned_response = model_response
        if "</think>" in model_response:
            parts = model_response.split("</think>")
            reasoning_content = parts[0].rstrip("\n").split("<think>")[-1].lstrip("\n")
            cleaned_response = parts[-1].lstrip("\n")
        else:
            cleaned_response = "response outputs too long or no slash think in response."
        print("cleaned_response: ", cleaned_response)
        response_data = {
            "model_responses": cleaned_response,
            "model_responses_message_for_chat_history": {
                "role": "assistant",
                "content": cleaned_response,
            },
            "reasoning_content": reasoning_content,
            "input_token": api_response.usage.prompt_tokens,
            "output_token": api_response.usage.completion_tokens,
        }

        # Attach reasoning content to the assistant message for the next turn if present
        if reasoning_content:
            response_data["model_responses_message_for_chat_history"][
                "reasoning_content"
            ] = reasoning_content

        if not reasoning_content:
            del response_data["reasoning_content"]

        return response_data
