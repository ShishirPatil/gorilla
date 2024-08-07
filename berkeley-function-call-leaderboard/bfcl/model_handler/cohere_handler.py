import os

from bfcl.model_handler.handler import BaseHandler
from bfcl.model_handler.model_style import ModelStyle
from bfcl.model_handler.utils import (
    augment_prompt_by_languge,
    language_specific_pre_processing,
    convert_to_tool,
    ast_parse,
    convert_to_function_call,
)
from bfcl.model_handler.constant import (
    SYSTEM_PROMPT_FOR_CHAT_MODEL,
    USER_PROMPT_FOR_CHAT_MODEL,
    GORILLA_TO_PYTHON,
)
import time
import cohere

from bfcl.model_handler.constant import USE_COHERE_OPTIMIZATION


class CohereHandler(BaseHandler):
    client: cohere.Client

    def __init__(self, model_name, temperature=0.7, top_p=1, max_tokens=1000) -> None:
        super().__init__(model_name, temperature, top_p, max_tokens)
        self.model_style = ModelStyle.COHERE

        self.client = cohere.Client(api_key=os.getenv("COHERE_API_KEY"))

        # System prompt for function calling.
        if USE_COHERE_OPTIMIZATION:
            self.preamble = """## Task & Context
    You help people answer their questions and other requests interactively. You will be asked a very wide array of requests on all kinds of topics. You will be equipped with a wide range of search engines or similar tools to help you, which you can use to research your answer. You should focus on serving the user's needs as best you can, which will be wide-ranging.

    When a question is irrelevant or unrelated to the available tools you should choose to directly answer. This is especially important when the question or available tools are about specialist subject like math or biology or physics: DO NOT ANSWER UNRELATED QUESTIONS.

    ## Style Guide
    Unless the user asks for a different style of answer, you should answer in full sentences, using proper grammar and spelling.
    """
        else:
            self.preamble = """
        ## Task & Context
        You help people answer their questions and other requests interactively. You will be asked a very wide array of requests on all kinds of topics. You will be equipped with a wide range of search engines or similar tools to help you, which you use to research your answer. You should focus on serving the user's needs as best you can, which will be wide-ranging.

        ## Style Guide
        Unless the user asks for a different style of answer, you should answer in full sentences, using proper grammar and spelling.
        """

    def inference(self, prompt, functions, test_category):
        if "FC" not in self.model_name:
            prompt = augment_prompt_by_languge(prompt, test_category)
            functions = language_specific_pre_processing(
                functions, test_category
            )
            message = USER_PROMPT_FOR_CHAT_MODEL.format(
                user_prompt=prompt, functions=str(functions)
            )
            start_time = time.time()
            response = self.client.chat(
                message=message,
                model=self.model_name,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                preamble=SYSTEM_PROMPT_FOR_CHAT_MODEL,
            )
            latency = time.time() - start_time
            result = response.text
        else:
            prompt = augment_prompt_by_languge(prompt, test_category)
            functions = language_specific_pre_processing(functions, test_category)
            if type(functions) is not list:
                functions = [functions]
            message = prompt
            # Convert JSON schema into R+ compatible function calls.
            cohere_tool = convert_to_tool(
                functions, GORILLA_TO_PYTHON, self.model_style, test_category
            )
            start_time = time.time()
            if len(cohere_tool) > 0:
                try:
                    if USE_COHERE_OPTIMIZATION:
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

    def decode_ast(self, result, language="Python"):
        if "FC" not in self.model_name:
            if not result.startswith("["):
                result = "[" + result
            if not result.endswith("]"):
                result = result + "]"
            decoded_output = ast_parse(result, language)
        else:
            decoded_output = []
            for invoked_function in result:
                name = list(invoked_function.keys())[0]
                params = invoked_function[name]
                if language == "Python":
                    pass
                else:
                    if USE_COHERE_OPTIMIZATION:
                        # all values of the json are cast to string for java and javascript
                        for key, value in params.items():
                            value = str(value)
                            # Booleans are converted from JSON -> Python, and then turned into a string.
                            # Use e.g. 'true' instead of the Python 'True'.
                            if isinstance(params[key], bool):
                                value = value.lower()
                            params[key] = value

                decoded_output.append({name: params})
        return decoded_output

    def decode_execute(self, result):
        if "FC" not in self.model_name:
            if not result.startswith("["):
                result = "[" + result
            if not result.endswith("]"):
                result = result + "]"
            decoded_output = ast_parse(result)
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
