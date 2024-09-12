from bfcl.model_handler.base_handler import BaseHandler
from bfcl.model_handler.model_style import ModelStyle
from bfcl.model_handler.utils import (
    convert_to_tool,
    convert_to_function_call,
    system_prompt_pre_processing_chat_model,
    func_doc_language_specific_pre_processing,
    ast_parse,
    convert_system_prompt_into_user_prompt,
    combine_consecutive_user_prompr,
)
from bfcl.model_handler.constant import (
    GORILLA_TO_OPENAPI,
    DEFAULT_SYSTEM_PROMPT,
)
from openai import OpenAI
import os, time, json


class OpenAIHandler(BaseHandler):
    def __init__(self, model_name, temperature=0.001, top_p=1, max_tokens=1000) -> None:
        super().__init__(model_name, temperature, top_p, max_tokens)
        self.model_style = ModelStyle.OpenAI
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def inference(self, prompt, functions, test_category):
        # Chatting model
        if "FC" not in self.model_name:
            functions = func_doc_language_specific_pre_processing(
                functions, test_category
            )

            prompt = system_prompt_pre_processing_chat_model(
                prompt, DEFAULT_SYSTEM_PROMPT, functions
            )
            # Special handling for o1-preview and o1-mini as they don't support system prompts yet
            if "o1-preview" in self.model_name or "o1-mini" in self.model_name:
                prompt = convert_system_prompt_into_user_prompt(prompt)
                prompt = combine_consecutive_user_prompr(prompt)
            message = prompt

            start_time = time.time()
            # These two models have temperature and top_p fixed to 1, and max_tokens is not supported
            # Beta limitation: https://platform.openai.com/docs/guides/reasoning/beta-limitations
            if "o1-preview" in self.model_name or "o1-mini" in self.model_name:
                response = self.client.chat.completions.create(
                    messages=message,
                    model=self.model_name,
                    temperature=1,
                    # max_tokens=self.max_tokens,
                    top_p=1,
                )
            else:
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
            metadata["input_token_count"] = response.usage.prompt_tokens
            metadata["output_token_count"] = response.usage.completion_tokens
            metadata["latency"] = latency
            metadata["processed_message"] = message
        # Function call model
        else:
            functions = func_doc_language_specific_pre_processing(
                functions, test_category
            )

            message = prompt
            oai_tool = convert_to_tool(
                functions, GORILLA_TO_OPENAPI, self.model_style, test_category
            )
            start_time = time.time()
            if len(oai_tool) > 0:
                response = self.client.chat.completions.create(
                    messages=message,
                    model=self.model_name.replace("-FC", ""),
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    top_p=self.top_p,
                    tools=oai_tool,
                )
            else:
                response = self.client.chat.completions.create(
                    messages=message,
                    model=self.model_name.replace("-FC", ""),
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    top_p=self.top_p,
                )
            latency = time.time() - start_time
            try:
                result = [
                    {func_call.function.name: func_call.function.arguments}
                    for func_call in response.choices[0].message.tool_calls
                ]
            except:
                result = response.choices[0].message.content
            metadata = {}
            metadata["input_token_count"] = response.usage.prompt_tokens
            metadata["output_token_count"] = response.usage.completion_tokens
            metadata["latency"] = latency
            metadata["processed_message"] = message
            metadata["processed_tool"] = oai_tool

        return result, metadata

    def decode_ast(self, result, language="Python"):
        if "FC" not in self.model_name:
            func = result
            if " " == func[0]:
                func = func[1:]
            if not func.startswith("["):
                func = "[" + func
            if not func.endswith("]"):
                func = func + "]"
            decoded_output = ast_parse(func, language)
        else:
            decoded_output = []
            for invoked_function in result:
                name = list(invoked_function.keys())[0]
                params = json.loads(invoked_function[name])
                decoded_output.append({name: params})
        return decoded_output

    def decode_execute(self, result):
        if "FC" not in self.model_name:
            func = result
            if " " == func[0]:
                func = func[1:]
            if not func.startswith("["):
                func = "[" + func
            if not func.endswith("]"):
                func = func + "]"
            decoded_output = ast_parse(func)
            execution_list = []
            for function_call in decoded_output:
                for key, value in function_call.items():
                    execution_list.append(
                        f"{key}({','.join([f'{k}={repr(v)}' for k, v in value.items()])})"
                    )
            return execution_list
        else:
            function_call = convert_to_function_call(result)
            return function_call
