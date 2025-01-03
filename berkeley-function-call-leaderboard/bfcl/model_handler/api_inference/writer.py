import os
import time

from bfcl.model_handler.model_style import ModelStyle
from bfcl.model_handler.api_inference.openai import OpenAIHandler
from writerai import Writer


class WriterHandler(OpenAIHandler):
    def __init__(self, model_name, temperature) -> None:
        super().__init__(model_name, temperature)
        self.model_style = ModelStyle.WRITER
        self.client = Writer(api_key=os.getenv("WRITER_API_KEY"))
        self.is_fc_model = True

    #### FC methods ####

    def _query_FC(self, inference_data: dict):
        message: list[dict] = inference_data["message"]
        tools = inference_data["tools"]
        inference_data["inference_input_log"] = {"message": repr(message), "tools": tools}

        start_time = time.time()
        if len(tools) > 0:
            api_response = self.client.chat.chat(
                messages=message,
                model=self.model_name,
                temperature=self.temperature,
                tools=tools,
                tool_choice="auto",
            )
        else:
            api_response = self.client.chat.chat(
                messages=message,
                model=self.model_name,
                temperature=self.temperature,
            )
        end_time = time.time()

        return api_response, end_time - start_time
