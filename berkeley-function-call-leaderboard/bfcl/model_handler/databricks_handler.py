from bfcl.model_handler.handler import BaseHandler
from bfcl.model_handler.model_style import ModelStyle
from bfcl.model_handler.utils import (
    func_doc_language_specific_pre_processing,
    system_prompt_pre_processing,
    user_prompt_pre_processing_chat_model,
    combine_consecutive_user_prompr,
    ast_parse,
)
from bfcl.model_handler.constant import (
    DEFAULT_SYSTEM_PROMPT,
    USER_PROMPT_FOR_CHAT_MODEL,
)
import time
from openai import OpenAI
import re


class DatabricksHandler(BaseHandler):
    def __init__(self, model_name, temperature=0.001, top_p=1, max_tokens=1000) -> None:
        super().__init__(model_name, temperature, top_p, max_tokens)
        self.model_style = ModelStyle.OpenAI

        # NOTE: To run the Databricks model, you need to provide your own Databricks API key and your own Azure endpoint URL.
        self.client = OpenAI(
            api_key="{YOUR_DATABRICKS_API_KEY}",
            base_url="{YOUR_DATABRICKS_AZURE_ENDPOINT_URL}",
        )

    def inference(self, prompt, functions, test_category):
        functions = func_doc_language_specific_pre_processing(functions, test_category)

        prompt = system_prompt_pre_processing(prompt, DEFAULT_SYSTEM_PROMPT)
        prompt = user_prompt_pre_processing_chat_model(
            prompt, USER_PROMPT_FOR_CHAT_MODEL, test_category, functions
        )
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
        metadata = {}
        metadata["input_tokens"] = response.usage.prompt_tokens
        metadata["output_tokens"] = response.usage.completion_tokens
        metadata["latency"] = latency
        return result, metadata

    def decode_ast(self, result, language="Python"):
        func = re.sub(r"'([^']*)'", r"\1", result)
        func = func.replace("\n    ", "")
        if not func.startswith("["):
            func = "[" + func
        if not func.endswith("]"):
            func = func + "]"
        if func.startswith("['"):
            func = func.replace("['", "[")
        try:
            decode_output = ast_parse(func, language)
        except:
            decode_output = ast_parse(result, language)
        return decode_output

    def decode_execute(self, result, language="Python"):
        func = re.sub(r"'([^']*)'", r"\1", result)
        func = func.replace("\n    ", "")
        if not func.startswith("["):
            func = "[" + func
        if not func.endswith("]"):
            func = func + "]"
        if func.startswith("['"):
            func = func.replace("['", "[")
        try:
            decode_output = ast_parse(func, language)
        except:
            decode_output = ast_parse(result, language)
        execution_list = []
        for function_call in decode_output:
            for key, value in function_call.items():
                execution_list.append(
                    f"{key}({','.join([f'{k}={repr(v)}' for k, v in value.items()])})"
                )
        return execution_list
