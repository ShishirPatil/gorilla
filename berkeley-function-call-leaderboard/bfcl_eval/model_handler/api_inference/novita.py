import os

from bfcl_eval.model_handler.api_inference.openai_completion import OpenAICompletionsHandler
from bfcl_eval.model_handler.model_style import ModelStyle
from openai import OpenAI


class NovitaHandler(OpenAICompletionsHandler):
    def __init__(self, model_name, temperature) -> None:
        super().__init__(model_name, temperature)
        self.model_style = ModelStyle.NOVITA_AI
        self.client = OpenAI(
            base_url="https://api.novita.ai/v3/openai",
            api_key=os.getenv("NOVITA_API_KEY"),
        )

    #### FC methods ####

    def _query_FC(self, inference_data: dict):
        message: list[dict] = inference_data["message"]
        tools = inference_data["tools"]
        inference_data["inference_input_log"] = {
            "message": repr(message),
            "tools": tools,
        }

        if len(tools) > 0:
            return self.generate_with_backoff(
                messages=message,
                model=self.model_name.replace("-FC", "").replace("-novita", ""),
                temperature=self.temperature,
                tools=tools,
            )
        else:

            return self.generate_with_backoff(
                messages=message,
                model=self.model_name.replace("-FC", "").replace("-novita", ""),
                temperature=self.temperature,
            )

    #### Prompting methods ####

    def _query_prompting(self, inference_data: dict):
        inference_data["inference_input_log"] = {"message": repr(inference_data["message"])}

        return self.generate_with_backoff(
            messages=inference_data["message"],
            model=self.model_name.replace("-novita", ""),
            temperature=self.temperature,
        )
