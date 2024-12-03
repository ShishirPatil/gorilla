from bfcl.model_handler.proprietary_model.openai import OpenAIHandler
from openai import OpenAI


class GrokHandler(OpenAIHandler):
    def __init__(self, model_name, temperature) -> None:
        super().__init__(model_name, temperature)
        self.client = OpenAI(
            api_key=os.getenv("GROK_API_KEY"), base_url="https://api.x.ai/v1"
        )
        self.is_fc_model = True
