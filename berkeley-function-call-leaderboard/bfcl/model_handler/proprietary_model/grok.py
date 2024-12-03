import json
import os
import time
from openai import OpenAI, RateLimitError
from bfcl.model_handler.base_handler import BaseHandler
from bfcl.model_handler.model_style import ModelStyle
from bfcl.model_handler.utils import (
    ast_parse,
    convert_to_function_call,
    func_doc_language_specific_pre_processing,
    system_prompt_pre_processing_chat_model,
)
from bfcl.model_handler.proprietary_model.openai import OpenAIHandler

class GrokHandler(OpenAIHandler):
    def __init__(self, model_name, temperature) -> None:
        super().__init__(model_name, temperature)
        self.model_style = ModelStyle.Grok
        
        self.api_key = os.getenv("GROK_API_KEY")
        self.base_url = os.getenv("GROK_API_BASE_URL", "https://api.x.ai/v1")
        
        if not self.api_key:
            raise ValueError("GROK_API_KEY is not set in environment variables.")
            
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

    def _get_actual_model_name(self, model_name: str) -> str:
        return "grok-beta"

    def decode_ast(self, result, language="Python"):
        if "FC" in self.model_name:
            decoded_output = []
            for invoked_function in result:
                name = list(invoked_function.keys())[0]
                params = json.loads(invoked_function[name])
                decoded_output.append({name: params})
            return decoded_output
        else:
            func = result
            func = func.replace("\\_", "_")
            if not func.startswith("["):
                func = "[" + func
            if not func.endswith("]"):
                func = func + "]"
            decoded_output = ast_parse(func, language)
            return decoded_output

    def decode_execute(self, result):
        if "FC" in self.model_name:
            function_call = convert_to_function_call(result)
            return function_call
        else:
            func = result
            func = func.replace("\\_", "_")
            decode_output = ast_parse(func)
            execution_list = []
            for function_call in decode_output:
                for key, value in function_call.items():
                    execution_list.append(
                        f"{key}({','.join([f'{k}={repr(v)}' for k, v in value.items()])})"
                    )
            return execution_list

    def _query_FC(self, inference_data: dict):
        message = inference_data["message"]
        tools = inference_data.get("tools", [])
        
        actual_model_name = self._get_actual_model_name(self.model_name)
        
        kwargs = {
            "model": actual_model_name,
            "messages": message,
            "temperature": self.temperature,
        }
        if tools:
            kwargs["tools"] = tools
        
        return self.generate_with_backoff(**kwargs)

    def _pre_query_processing_FC(self, inference_data: dict, test_entry: dict) -> dict:
        inference_data["message"] = [
            {"role": "system", "content": "You are a helpful assistant skilled at using the provided tools."}
        ]
        return inference_data

    def _compile_tools(self, inference_data: dict, test_entry: dict) -> dict:
        functions = test_entry["function"]
        test_category = test_entry["id"].rsplit("_", 1)[0]
        functions = func_doc_language_specific_pre_processing(functions, test_category)
        tools = [{"type": "function", "function": f} for f in functions]
        inference_data["tools"] = tools
        return inference_data

    def _query_prompting(self, inference_data: dict):
        message = inference_data["message"]
        actual_model_name = self._get_actual_model_name(self.model_name)
        
        return self.generate_with_backoff(
            model=actual_model_name,
            messages=message,
            temperature=self.temperature,
        )

    def _pre_query_processing_prompting(self, test_entry: dict) -> dict:
        functions = test_entry["function"]
        test_category = test_entry["id"].rsplit("_", 1)[0]
        
        functions = func_doc_language_specific_pre_processing(functions, test_category)
        test_entry["question"][0] = system_prompt_pre_processing_chat_model(
            test_entry["question"][0], functions, test_category
        )
        return {"message": []}