import os
import time

import cohere

from bfcl.model_handler import utils
from bfcl.model_handler import constants
from bfcl.model_handler.base import BaseHandler, ModelStyle


OPTIMIZED_PREAMBLE = """## Task & Context
You help people answer their questions and other requests interactively. You will be asked a very wide array of requests on all kinds of topics. You will be equipped with a wide range of search engines or similar tools to help you, which you can use to research your answer. You should focus on serving the user's needs as best you can, which will be wide-ranging.

When a question is irrelevant or unrelated to the available tools you should choose to directly answer. This is especially important when the question or available tools are about specialist subject like math or biology or physics: DO NOT ANSWER UNRELATED QUESTIONS.

## Style Guide
Unless the user asks for a different style of answer, you should answer in full sentences, using proper grammar and spelling.
"""

PREAMBLE = """## Task & Context
You help people answer their questions and other requests interactively. You will be asked a very wide array of requests on all kinds of topics. You will be equipped with a wide range of search engines or similar tools to help you, which you use to research your answer. You should focus on serving the user's needs as best you can, which will be wide-ranging.

## Style Guide
Unless the user asks for a different style of answer, you should answer in full sentences, using proper grammar and spelling.
"""


class CohereHandler(BaseHandler):
    model_style = ModelStyle.COHERE

    def __init__(
        self, 
        model_name, 
        temperature=0.7, 
        top_p=1, 
        max_tokens=1000, 
        use_cohere_optimization: bool = constants.USE_COHERE_OPTIMIZATION
    ) -> None:
        
        super().__init__(model_name, temperature, top_p, max_tokens)
        self.use_cohere_optimization = use_cohere_optimization
        self.client = cohere.Client(api_key=os.getenv("COHERE_API_KEY"))
        self.preamble = OPTIMIZED_PREAMBLE if use_cohere_optimization else PREAMBLE
    
    @classmethod
    def supported_models(cls):
        return [
            'command-r-plus',
            'command-r-plus-FC',
            'command-r-plus-optimized',
            'command-r-plus-FC-optimized',
        ]

    def inference(self, prompt, functions, test_category):
        if "FC" not in self.model_name:
            prompt = utils.augment_prompt_by_languge(prompt, test_category)
            functions = utils.language_specific_pre_processing(
                functions, test_category, False
            )
            message = constants.USER_PROMPT_FOR_CHAT_MODEL.format(user_prompt=prompt, 
                                                                  functions=str(functions))
            start_time = time.time()
            response = self.client.chat(
                message=message,
                model=self.model_name,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                preamble=constants.SYSTEM_PROMPT_FOR_CHAT_MODEL,
            )
            latency = time.time() - start_time
            result = response.text
        else:
            prompt = utils.augment_prompt_by_languge(prompt, test_category)
            functions = utils.language_specific_pre_processing(functions, test_category, True)
            if type(functions) is not list:
                functions = [functions]
            message = prompt
            # Convert JSON schema into R+ compatible function calls.
            cohere_tool = utils.convert_to_tool(
                functions, constants.GORILLA_TO_PYTHON, self.model_style, test_category, True
            )
            start_time = time.time()
            if len(cohere_tool) > 0:
                try:
                    if self.use_cohere_optimization:
                        response = self.client.chat(
                            message=message,
                            model=self.model_name.replace("-FC", ""),
                            preamble=self.preamble,
                            tools=cohere_tool,
                            # The API default is used for the following parameters in FC:
                            temperature=None,
                            max_tokens=None,
                        )   
                    else:
                        response = self.client.chat(
                        message=message,
                        model=self.model_name.replace("-FC", ""),
                        temperature=self.temperature,
                        max_tokens=self.max_tokens,
                        tools=cohere_tool,
                        preamble=self.preamble,
                    )
                except Exception as e:
                    return "Error", {
                        "input_tokens": 0,
                        "output_tokens": 0,
                        "latency": 0,
                    }
            else:
                response = self.client.chat(
                    message=message,
                    model=self.model_name.replace("-FC", ""),
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    preamble=self.preamble,
                )
            latency = time.time() - start_time
            try:
                result = [
                    {func_call.name: func_call.parameters}
                    for func_call in response.tool_calls
                ]
            except:
                result = response.text
        api_metadata = response.meta
        metadata = {}
        if api_metadata is not None:
            metadata["input_tokens"] = api_metadata.billed_units.input_tokens
            metadata["output_tokens"] = api_metadata.billed_units.output_tokens
        metadata["latency"] = latency
        return result, metadata

    def decode_ast(self, result, language="python"):
        if "FC" not in self.model_name:
            if not result.startswith("["):
                result = "[" + result
            if not result.endswith("]"):
                result = result + "]"
            decoded_output = utils.ast_parse(result, language)
        else:
            decoded_output = []
            for invoked_function in result:
                name = list(invoked_function.keys())[0]
                params = invoked_function[name]
                if language == "Python":
                    pass
                else:
                    if self.use_cohere_optimization:
                        # all values of the json are cast to string for java and javascript
                        for key, value in params.items():
                            value = str(value)
                            # Booleans are converted from JSON -> Python, and then turned into a string.
                            # Use e.g. 'true' instead of the Python 'True'.
                            if isinstance(params[key], bool):
                                value = value.lower()
                            params[key] = value
                    else:
                        for key in params:
                            params[key] = str(params[key])
                decoded_output.append({name: params})
        return decoded_output

    def decode_execute(self, result):
        if "FC" not in self.model_name:
            if not result.startswith("["):
                result = "[" + result
            if not result.endswith("]"):
                result = result + "]"
            decoded_output = utils.ast_parse(result)
            execution_list = []
            for function_call in decoded_output:
                for key, value in function_call.items():
                    execution_list.append(
                        f"{key}({','.join([f'{k}={repr(v)}' for k, v in value.items()])})"
                    )
            return execution_list
        else:
            function_call_list = result
            if type(function_call_list) == dict:
                function_call_list = [function_call_list]
            execution_list = []
            for function_call in function_call_list:
                for key, value in function_call.items():
                    execution_list.append(
                        f"{key}({','.join([f'{k}={repr(v)}' for k,v in value.items()])})"
                    )
            return execution_list
