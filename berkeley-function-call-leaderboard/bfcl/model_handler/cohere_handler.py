import os

from bfcl.model_handler.handler import BaseHandler
from bfcl.model_handler.model_style import ModelStyle
from bfcl.model_handler.utils import (
    user_prompt_pre_processing_chat_model,
    func_doc_language_specific_pre_processing,
    convert_to_tool,
    ast_parse,
)
from bfcl.model_handler.constant import (
    DEFAULT_SYSTEM_PROMPT,
    USER_PROMPT_FOR_CHAT_MODEL,
    GORILLA_TO_PYTHON,
)
import time
import cohere

from bfcl.model_handler.constant import USE_COHERE_OPTIMIZATION


class CohereHandler(BaseHandler):
    client: cohere.Client

    def __init__(self, model_name, temperature=0.001, top_p=1, max_tokens=1000) -> None:
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

    def _substitute_prompt_role(self, prompts):
        # Cohere use CHATBOT, USER, SYSTEM, TOOL as roles
        for prompt in prompts:
            if prompt["role"] == "user":
                prompt["role"] = "USER"
            elif prompt["role"] == "assistant":
                prompt["role"] = "CHATBOT"
            elif prompt["role"] == "system":
                prompt["role"] = "SYSTEM"
            elif prompt["role"] == "tool":
                prompt["role"] = "TOOL"
        return prompts
    
    def _substitute_content_name(self, prompts):
        for prompt in prompts:
            prompt["message"] = prompt["content"]
            del prompt["content"]
        return prompts

    def _extract_last_user_message(self, chat_history):
        for i in range(len(chat_history) - 1, -1, -1):
            if chat_history[i]["role"] == "USER":
                last_user_message = chat_history[i]["message"]
                del chat_history[i]
                return last_user_message
        return "User did not specify a query."

    def inference(self, prompt, functions, test_category):
        # Chatting model
        if "FC" not in self.model_name:
            functions = func_doc_language_specific_pre_processing(
                functions, test_category
            )
            prompt = user_prompt_pre_processing_chat_model(
                prompt, USER_PROMPT_FOR_CHAT_MODEL, test_category, functions
            )
            
            chat_history = self._substitute_prompt_role(prompt)
            chat_history = self._substitute_content_name(chat_history)
            message = self._extract_last_user_message(chat_history)
            
            start_time = time.time()
            response = self.client.chat(
                message=message,
                model=self.model_name,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                preamble=DEFAULT_SYSTEM_PROMPT,
                chat_history=chat_history,
            )
            latency = time.time() - start_time
            result = response.text
            
        # Function call model
        else:
            # preamble for system prompt
            # chat_hitory for all past chat messages
            # message is a string
            functions = func_doc_language_specific_pre_processing(
                functions, test_category
            )
            chat_history = self._substitute_prompt_role(prompt)
            chat_history = self._substitute_content_name(chat_history)
            message = self._extract_last_user_message(chat_history)
 
            # Convert JSON schema into R+ compatible function calls.
            cohere_tool = convert_to_tool(
                functions, GORILLA_TO_PYTHON, self.model_style, test_category
            )
            start_time = time.time()

            response = self.client.chat(
                message=message,
                model=self.model_name.replace("-FC", ""),
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                tools=cohere_tool if len(cohere_tool) > 0 else None,
                preamble=self.preamble,
                chat_history=chat_history if len(chat_history) > 0 else None,
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
