import time
import os

from openai import OpenAI

from bfcl.model_handler import utils
from bfcl.model_handler import constants
from bfcl.model_handler.base import BaseHandler, ModelStyle


class NvidiaHandler(BaseHandler):
    model_style = ModelStyle.OPENAI

    def __init__(self, model_name, temperature=0.7, top_p=1, max_tokens=1000) -> None:
        super().__init__(model_name, temperature, top_p, max_tokens)
        self.client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=os.getenv("NVIDIA_API_KEY")
        )
    
    @classmethod
    def supported_models(cls):
        return [
            'nvidia/nemotron-4-340b-instruct',
        ]

    def inference(self, prompt, functions, test_category):
        prompt = utils.augment_prompt_by_languge(prompt, test_category)
        functions = utils.language_specific_pre_processing(functions, test_category, False)
        message = [
            {
                "role": "system",
                "content": constants.SYSTEM_PROMPT_FOR_CHAT_MODEL,
            },
            {
                "role": "user",
                "content": "Questions:" + constants.USER_PROMPT_FOR_CHAT_MODEL.format(user_prompt=prompt, 
                                                                                      functions=str(functions)),
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

    def decode_ast(self, result, language="python"):
        result = result.replace("\n", "")
        if not result.startswith("["):
            result = "[ " + result
        if not result.endswith("]"):
            result = result + " ]"
        if result.startswith("['"):
            result = result.replace("['", "[")
            result = result.replace("', '", ", ")
            result = result.replace("','", ", ")
        if result.endswith("']"):
            result = result.replace("']", "]")
        decode_output = utils.ast_parse(result, language)
        return decode_output
        
    def decode_execute(self, result, language="python"):
        result = result.replace("\n", "")
        if not result.startswith("["):
            result = "[ " + result
        if not result.endswith("]"):
            result = result + " ]"
        if result.startswith("['"):
            result = result.replace("['", "[")
            result = result.replace("', '", ", ")
            result = result.replace("','", ", ")
        if result.endswith("']"):
            result = result.replace("']", "]")
        decode_output = utils.ast_parse(result, language)
        execution_list = []
        for function_call in decode_output:
            for key, value in function_call.items():
                execution_list.append(
                    f"{key}({','.join([f'{k}={repr(v)}' for k, v in value.items()])})"
                )
        return execution_list