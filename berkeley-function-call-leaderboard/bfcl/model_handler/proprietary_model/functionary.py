from openai import OpenAI

from bfcl.model_handler.proprietary_model.openai import OpenAIHandler


# For setup instructions, please refer to https://github.com/MeetKai/functionary
class FunctionaryHandler(OpenAIHandler):
    def __init__(
        self, 
        model_name: str,
        temperature: float = 0.7, 
        top_p: int = 1, 
        max_tokens: int = 1000,
    ) -> None:
        super().__init__(model_name, temperature, top_p, max_tokens)
        self.client = OpenAI(base_url="http://localhost:8000/v1", api_key="functionary")

    @classmethod
    def supported_models(cls):
        return [
            'meetkai/functionary-small-v2.2-FC',
            'meetkai/functionary-medium-v2.2-FC',
            'meetkai/functionary-small-v2.4-FC',
            'meetkai/functionary-medium-v2.4-FC',
        ]
