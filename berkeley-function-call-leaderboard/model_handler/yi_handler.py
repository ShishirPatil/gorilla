from model_handler.handler import BaseHandler
from model_handler.model_style import ModelStyle
from model_handler.utils import (
    convert_to_tool,
    convert_to_function_call,
    augment_prompt_by_languge,
    language_specific_pre_processing,
    ast_parse,
)
from model_handler.constant import (
    GORILLA_TO_OPENAPI,
    USER_PROMPT_FOR_CHAT_MODEL,
    SYSTEM_PROMPT_FOR_CHAT_MODEL,
)
from openai import OpenAI
import os, time, json


class YiHandler(BaseHandler):
    def __init__(self, model_name, temperature=0.0, top_p=1, max_tokens=1000) -> None:
        super().__init__(model_name, temperature, top_p, max_tokens)
        self.model_style = ModelStyle.OpenAI
        self.base_url = "https://api.lingyiwanwu.com/v1"
        self.client = OpenAI(base_url=self.base_url, api_key=os.getenv("YI_API_KEY"))

    def inference(self, prompt, functions, test_category):
        if "FC" not in self.model_name:
            prompt = augment_prompt_by_languge(prompt,test_category)
            functions = language_specific_pre_processing(functions,test_category,False)
            if type(prompt) is list:
                assert not functions, "When using prompting mode with a list of messages, " +\
                    "functions must already exist in the list of messages"
                message = prompt
                assert message[0]['role'] == 'system', "System prompt must be provided in the test case."
            else:
                message = [
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT_FOR_CHAT_MODEL,

                    },
                    {
                        "role": "user",
                        "content": USER_PROMPT_FOR_CHAT_MODEL.format(
                            user_prompt=prompt, functions=str(functions)
                        ),
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
        else:
            prompt = augment_prompt_by_languge(prompt, test_category)
            functions = language_specific_pre_processing(functions, test_category, True)
            if type(functions) is not list:
                functions = [functions]

            message = [{"role": "user", "content": "Questions:" + prompt}]
            oai_tool = convert_to_tool(
                functions, GORILLA_TO_OPENAPI, self.model_style, test_category, True
            )
            print('message = ', message)
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
            except Exception as e:
                result = response.choices[0].message.content
        metadata = {}
        metadata["input_tokens"] = response.usage.prompt_tokens
        metadata["output_tokens"] = response.usage.completion_tokens
        metadata["latency"] = latency
        return result,metadata

    def decode_ast(self,result,language="Python"):
        if "FC" not in self.model_name:
            decoded_output = ast_parse(result,language)
        else:
            decoded_output = []
            for invoked_function in result:
                name = list(invoked_function.keys())[0]
                params = json.loads(invoked_function[name])
                if language == "Python":
                    pass
                else:
                    # all values of the json are casted to string for java and javascript
                    for key in params:
                        params[key] = str(params[key])
                decoded_output.append({name: params})
        return decoded_output

    def decode_execute(self,result):
        if "FC" not in self.model_name:
            decoded_output = ast_parse(result)
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
