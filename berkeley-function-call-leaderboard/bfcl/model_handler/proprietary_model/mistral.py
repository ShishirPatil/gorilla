import time
import os
import json

from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage

from bfcl.model_handler import utils, constants
from bfcl.model_handler.base import BaseHandler, ModelStyle


class MistralHandler(BaseHandler):
    model_style = ModelStyle.MISTRAL

    def __init__(self, model_name, temperature=0.7, top_p=1, max_tokens=1000) -> None:
        super().__init__(model_name, temperature, top_p, max_tokens)
        self.client = MistralClient(api_key=os.getenv("MISTRAL_API_KEY"))

    @classmethod
    def supported_models(cls):
        return [
            'mistral-tiny-2312',
            'mistral-small-2402',
            'mistral-small-2402-FC-Any',
            'mistral-small-2402-FC-Auto',
            'mistral-medium-2312',
            'mistral-large-2402',
            'mistral-large-2402-FC-Any',
            'mistral-large-2402-FC-Auto',
        ]

    def inference(self, prompt, functions, test_category):
        prompt = utils.augment_prompt_by_languge(prompt, test_category)
        if "FC" in self.model_name:
            functions = utils.language_specific_pre_processing(functions, test_category, True)
            tool = utils.convert_to_tool(
                functions, constants.GORILLA_TO_OPENAPI, self.model_style, test_category, True
            )
            message = [ChatMessage(role="user", content=prompt)]
            start = time.time()
            tool_choice = "any" if "Any" in self.model_name else "auto"
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
            functions = utils.language_specific_pre_processing(functions, test_category, False)
            message = [
                ChatMessage(role="system", content=constants.SYSTEM_PROMPT_FOR_CHAT_MODEL),
                ChatMessage(
                    role="user",
                    content=constants.USER_PROMPT_FOR_CHAT_MODEL.format(user_prompt=prompt, 
                                                                        functions=str(functions)),
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

    def decode_ast(self, result, language="python"):
        if "FC" in self.model_name:
            decoded_output = []
            for invoked_function in result:
                name = list(invoked_function.keys())[0]
                params = json.loads(invoked_function[name])
                if language != "Python":
                    for key in params:
                        params[key] = str(params[key])
                decoded_output.append({name: params})
            return decoded_output
        else:
            func = result
            func = func.replace("\\_", "_")
            if not func.startswith("["):
                func = "[" + func
            if not func.endswith("]"):
                func = func + "]"
            decoded_output = utils.ast_parse(func, language)
            return decoded_output

    def decode_execute(self, result):
        if "FC" in self.model_name:
            function_call = utils.convert_to_function_call(result)
            return function_call
        else:
            func = result
            func = func.replace("\\_", "_")
            decode_output = utils.ast_parse(func)
            execution_list = []
            for function_call in decode_output:
                for key, value in function_call.items():
                    execution_list.append(f"{key}({','.join([f'{k}={repr(v)}' for k, v in value.items()])})")
            return execution_list
