import os
import time

from bfcl.model_handler.api_inference.openai import OpenAIHandler
from bfcl.model_handler.model_style import ModelStyle
from bfcl.model_handler.utils import retry_with_backoff
from openai import OpenAI, RateLimitError
from overrides import override


class DeepSeekAPIHandler(OpenAIHandler):
    def __init__(self, model_name, temperature) -> None:
        super().__init__(model_name, temperature)
        self.model_style = ModelStyle.OpenAI
        self.client = OpenAI(
            base_url="https://api.deepseek.com", api_key=os.getenv("DEEPSEEK_API_KEY")
        )

    @retry_with_backoff(error_type=RateLimitError)
    def generate_with_backoff(self, **kwargs):
        """
        Per the DeepSeek API documentation:
        https://api-docs.deepseek.com/quick_start/rate_limit

        DeepSeek API does NOT constrain user's rate limit. We will try out best to serve every request.
        But please note that when our servers are under high traffic pressure, you may receive 429 (Rate Limit Reached) or 503 (Server Overloaded). When this happens, please wait for a while and retry.

        Thus, backoff is still useful for handling 429 and 503 errors.
        """
        start_time = time.time()
        api_response = self.client.chat.completions.create(**kwargs)
        end_time = time.time()

        return api_response, end_time - start_time

    @override
    def _query_FC(self, inference_data: dict):
        message: list[dict] = inference_data["message"]
        tools = inference_data["tools"]
        inference_data["inference_input_log"] = {"message": repr(message), "tools": tools}

        # Source https://api-docs.deepseek.com/quick_start/pricing
        # This will need to be updated if newer models are released.
        if "DeepSeek-V3" in self.model_name:
            api_model_name = "deepseek-chat"
        elif "DeepSeek-R1" in self.model_name:
            api_model_name = "deepseek-reasoner"
        else:
            raise ValueError(f"Model name {self.model_name} not supported by DeepSeek API")

        if len(tools) > 0:
            return self.generate_with_backoff(
                model=api_model_name,
                messages=message,
                tools=tools,
            )
        else:
            return self.generate_with_backoff(
                model=api_model_name,
                messages=message,
            )

    @override
    def _query_prompting(self, inference_data: dict):
        message: list[dict] = inference_data["message"]
        inference_data["inference_input_log"] = {"message": repr(message)}

        # Source https://api-docs.deepseek.com/quick_start/pricing
        # This will need to be updated if newer models are released.
        if "DeepSeek-V3" in self.model_name:
            api_model_name = "deepseek-chat"
        elif "DeepSeek-R1" in self.model_name:
            api_model_name = "deepseek-reasoner"
        else:
            raise ValueError(f"Model name {self.model_name} not supported by DeepSeek API")

        return self.generate_with_backoff(
            model=api_model_name,
            messages=message,
        )
