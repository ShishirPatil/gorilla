from bfcl.model_handler.handler import BaseHandler
from bfcl.model_handler.model_style import ModelStyle
from bfcl.model_handler.constant import (
    SYSTEM_PROMPT_FOR_CHAT_MODEL,
    USER_PROMPT_FOR_CHAT_MODEL,
    GORILLA_TO_OPENAPI,
)
from bfcl.model_handler.utils import (
    convert_to_tool,
    ast_parse,
    convert_to_function_call,
    augment_prompt_by_languge,
    language_specific_pre_processing,
)
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage
import os, time, json


class MistralHandler(BaseHandler):
    def __init__(self, model_name, temperature=0.7, top_p=1, max_tokens=1000) -> None:
        super().__init__(model_name, temperature, top_p, max_tokens)
        self.model_style = ModelStyle.Mistral

        self.client = MistralClient(api_key=os.getenv("MISTRAL_API_KEY"))

    def inference(self, prompt, functions, test_category):
        prompt = augment_prompt_by_languge(prompt, test_category)
        if "FC" in self.model_name:
            functions = language_specific_pre_processing(functions, test_category)
            tool = convert_to_tool(
                functions, GORILLA_TO_OPENAPI, self.model_style, test_category
            )
            message = [
                ChatMessage(role="user", content=prompt),
            ]
            start = time.time()
            if "Any" in self.model_name:
                tool_choice = "any"
            else:
                tool_choice = "auto"
            chat_response = self.client.chat(
                model=self.model_name.replace("-FC-Any", "").replace("-FC-Auto", ""),
                messages=message,
                tools=tool,
                tool_choice=tool_choice,
                temperature=self.temperature,
                top_p=self.top_p,
            )
            latency = time.time() - start
            try:
                result = [
                    {func_call.function.name: func_call.function.arguments}
                    for func_call in chat_response.choices[0].message.tool_calls
                ]
            except:
                result = chat_response.choices[0].message.content
        else:
            functions = language_specific_pre_processing(
                functions, test_category
            )
            message = [
                ChatMessage(role="system", content=SYSTEM_PROMPT_FOR_CHAT_MODEL),
                ChatMessage(
                    role="user",
                    content=USER_PROMPT_FOR_CHAT_MODEL.format(
                        user_prompt=prompt, functions=str(functions)
                    ),
                ),
            ]
            start = time.time()
            chat_response = self.client.chat(
                model=self.model_name,
                messages=message,
                temperature=self.temperature,
                top_p=self.top_p,
            )
            latency = time.time() - start
            result = chat_response.choices[0].message.content
        metadata = {
            "input_tokens": chat_response.usage.prompt_tokens,
            "output_tokens": chat_response.usage.completion_tokens,
            "latency": latency,
        }
        return result, metadata

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
