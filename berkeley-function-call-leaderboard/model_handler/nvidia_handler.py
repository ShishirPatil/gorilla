import time,os,json
from openai import OpenAI
from model_handler.handler import BaseHandler
from model_handler.model_style import ModelStyle
from model_handler.utils import (
    augment_prompt_by_languge,
    language_specific_pre_processing,
)
from model_handler.constant import (
    USER_PROMPT_FOR_CHAT_MODEL,
    SYSTEM_PROMPT_FOR_CHAT_MODEL,
)

class NvidiaHandler(BaseHandler):
    def __init__(self, model_name, temperature=0.7, top_p=1, max_tokens=1000) -> None:
        self.model_name = model_name
        self.temperature = temperature
        self.top_p = top_p
        self.max_tokens = max_tokens
        self.model_style = ModelStyle.OpenAI
        self.client = OpenAI(
            base_url = "https://integrate.api.nvidia.com/v1",
            api_key = os.getenv("NVIDIA_API_KEY")
        )
    def inference(self, prompt, functions, test_category):
        prompt = augment_prompt_by_languge(prompt,test_category)
        functions = language_specific_pre_processing(functions,test_category,False)
        message = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT_FOR_CHAT_MODEL,
            },
            {
                "role": "user",
                "content": "Questions:"
                + USER_PROMPT_FOR_CHAT_MODEL.format(
                    user_prompt=prompt, functions=str(functions)
                ),
            },
        ]
        start_time = time.time()
        response = self.client.chat.completions.create(
            messages=message,
            model=self.model_name,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            top_p=self.top_p,
        )
        latency = time.time() - start_time
        result = response.choices[0].message.content
        input_token = response.usage.prompt_tokens
        output_token = response.usage.completion_tokens
        metadata = {"input_tokens": input_token, "output_tokens": output_token, "latency": latency}
        return result, metadata
    
    def write(self, result, file_to_open):
        if not os.path.exists("./result"):
            os.mkdir("./result")
        if not os.path.exists("./result/" + self.model_name.replace("/", "_")):
            os.mkdir("./result/" + self.model_name.replace("/", "_"))
        with open(
            "./result/" + self.model_name.replace("/", "_") + "/" + file_to_open.replace(".json", "_result.json"), "a+"
        ) as f:
            f.write(json.dumps(result) + "\n")
