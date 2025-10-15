import os
from typing import Any

from openai import OpenAI
from overrides import override
from torch import dtype

from bfcl_eval.constants.enums import ModelStyle
from bfcl_eval.constants.eval_config import LOCAL_SERVER_PORT
from bfcl_eval.model_handler.api_inference.openai_completion import (
    OpenAICompletionsHandler,
)
from bfcl_eval.model_handler.local_inference.base_oss_handler import OSSHandler


class LlamaHandler(OSSHandler):
    """
    This the handler for the Llama models in function calling mode.
    According to the Llama model card, function calling should be handled differently
    than what is suggested by the standard Hugging Face chat template.
    For more details, see:
    https://www.llama.com/docs/model-cards-and-prompt-formats/llama4_omni/#-zero-shot-function-calling---system-message-
    This applies to all Llama 3 and Llama 4 series models, except for Llama 3.1.

    In addition, because Llama uses the same system prompt as the default BFCL system
    prompt that's normally provided to the model in "prompt mode", the constructed
    formatted prompt string remains same in both modes.
    As a result, we will not have separate "prompt mode" for Llama models to avoid confusion.
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
        self.model_name_huggingface = model_name.replace("-FC", "")

    @override
    def _format_prompt(self, messages, function):
        # For Llama 4 series, they use a different set of tokens than Llama 3
        if "Llama-4" in self.model_name:
            formatted_prompt = "<|begin_of_text|>"

            for message in messages:
                formatted_prompt += f"<|header_start|>{message['role']}<|header_end|>\n\n{message['content'].strip()}<|eot|>"

            formatted_prompt += "<|header_start|>assistant<|header_end|>\n\n"
        # For Llama 3 series
        else:
            formatted_prompt = "<|begin_of_text|>"

            for message in messages:
                formatted_prompt += f"<|start_header_id|>{message['role']}<|end_header_id|>\n\n{message['content'].strip()}<|eot_id|>"

            formatted_prompt += "<|start_header_id|>assistant<|end_header_id|>\n\n"

        return formatted_prompt

    @override
    def _add_execution_results_prompting(
        self,
        inference_data: dict,
        execution_results: list[str],
        model_response_data: dict,
    ) -> dict:
        for execution_result in execution_results:
            # Llama uses the `ipython` role for execution results
            inference_data["message"].append(
                {
                    "role": "ipython",
                    "content": execution_result,
                }
            )

        return inference_data


class LlamaChatCompletionsHandler(OpenAICompletionsHandler):
    """
    This the handler for the Llama models in chat/completions mode for function calling and
    uses the same system prompt used when using the Llama model with completions request.
    The chat template can be used directly or by removing the default Huggingface system prompt.
    According to the Llama model card, function calling should be handled differently
    than what is suggested by the standard Hugging Face chat template.
    For more details, see:
    https://www.llama.com/docs/model-cards-and-prompt-formats/llama4_omni/#-zero-shot-function-calling---system-message-
    This applies to all Llama 3 and Llama 4 series models, except for Llama 3.1.

    In addition, because Llama uses the same system prompt as the default BFCL system
    prompt that's normally provided to the model in "prompt mode", the constructed
    formatted prompt string remains same in both modes.
    As a result, we will not have separate "prompt mode" for Llama models to avoid confusion.
    """
    def __init__(
        self, model_name, temperature, registry_name, is_fc_model, **kwargs
    ) -> None:
        self.model_name = model_name = model_name.replace("-chat-completions", "")
        super().__init__(model_name, temperature, registry_name, is_fc_model, **kwargs)
        self.model_name_huggingface = model_name
        self.model_style = ModelStyle.OPENAI_COMPLETIONS
        self.dtype = dtype

        # Will be overridden in batch_inference method
        # Used to indicate where the tokenizer and config should be loaded from
        self.model_path_or_id = None

        # Read from env vars with fallbacks
        self.local_server_endpoint = os.getenv("LOCAL_SERVER_ENDPOINT", "localhost")
        self.local_server_port = os.getenv("LOCAL_SERVER_PORT", LOCAL_SERVER_PORT)

        self.base_url = (
            f"http://{self.local_server_endpoint}:{self.local_server_port}/v1"
        )
        self.client = OpenAI(base_url=self.base_url, api_key="EMPTY")

    @override
    def _add_execution_results_prompting(
        self,
        inference_data: dict,
        execution_results: list[str],
        model_response_data: dict,
    ) -> dict:
        for execution_result in execution_results:
            # Llama uses the `ipython` role for execution results
            inference_data["message"].append(
                {
                    "role": "ipython",
                    "content": execution_result,
                }
            )

        return inference_data

    @override
    def _parse_query_response_prompting(self, api_response: Any) -> dict:
        return {
            "model_responses": api_response.choices[
                0
            ].message.content,
            "input_token": api_response.usage.prompt_tokens,
            "output_token": api_response.usage.completion_tokens,
        }

    @override
    def _add_assistant_message_prompting(
        self, inference_data: dict, model_response_data: dict
    ) -> dict:
        inference_data["message"].append(
            {"role": "assistant", "content": model_response_data["model_responses"]}
        )
        return inference_data
