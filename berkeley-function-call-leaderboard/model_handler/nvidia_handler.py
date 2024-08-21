import time, os
from openai import OpenAI
from model_handler.handler import BaseHandler
from model_handler.model_style import ModelStyle
from model_handler.utils import ast_parse
from model_handler.utils import (
    func_doc_language_specific_pre_processing,
    system_prompt_pre_processing_chat_model,
    combine_consecutive_user_prompr,
)
from model_handler.constant import (
    DEFAULT_SYSTEM_PROMPT,
)


class NvidiaHandler(BaseHandler):
    def __init__(self, model_name, temperature=0.001, top_p=1, max_tokens=1000) -> None:
        super().__init__(model_name, temperature, top_p, max_tokens)
        self.model_style = ModelStyle.OpenAI
        self.client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=os.getenv("NVIDIA_API_KEY"),
        )

    def inference(self, prompt, functions, test_category):
        functions = func_doc_language_specific_pre_processing(functions, test_category)
        prompt = system_prompt_pre_processing_chat_model(prompt, DEFAULT_SYSTEM_PROMPT, functions)
        
        prompt = combine_consecutive_user_prompr(prompt)
        message = prompt

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
        metadata = {
            "input_tokens": input_token,
            "output_tokens": output_token,
            "latency": latency,
        }
        return result, metadata

    def decode_ast(self, result, language="Python"):
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
        decode_output = ast_parse(result, language)
        return decode_output

    def decode_execute(self, result, language="Python"):
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
        decode_output = ast_parse(result, language)
        execution_list = []
        for function_call in decode_output:
            for key, value in function_call.items():
                execution_list.append(
                    f"{key}({','.join([f'{k}={repr(v)}' for k, v in value.items()])})"
                )
        return execution_list
