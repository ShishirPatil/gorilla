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
    GORILLA_TO_PYTHON,
    USER_PROMPT_FOR_CHAT_MODEL,
    SYSTEM_PROMPT_FOR_CHAT_MODEL,
)
from openai import OpenAI
import os, time, json


class GenericVLLMHandler(BaseHandler):
    def __init__(self, model_name, temperature=0.7, top_p=1, max_tokens=1000) -> None:
        super().__init__(model_name, temperature, top_p, max_tokens)
        self.model_style = ModelStyle.OpenAI
        # TODO: to avoid changing BFCL too much, just passing these as environment variables
        if os.environ.get("VLLM_ENDPOINT_KEY") is None or os.environ.get("VLLM_ENDPOINT_URL") is None or os.environ.get("VLLM_MODEL_NAME") is None:
            raise ValueError("VLLM_ENDPOINT_KEY or VLLM_ENDPOINT_URL or VLLM_MODEL_NAME environment variables are not set. Please set them to use the GenericVLLMHandler.")
        self.client = OpenAI(
            api_key=os.environ["VLLM_ENDPOINT_KEY"],
            base_url=os.environ["VLLM_ENDPOINT_URL"],
        )

    def inference(self, prompt,functions,test_category):
        # TODO: do this more elegantly
        API_FAILURE_MESSAGE = None # hacky way to get the error message out of the try block

        if "FC" not in self.model_name:
            prompt = augment_prompt_by_languge(prompt,test_category)
            functions = language_specific_pre_processing(functions,test_category,False)
            message = [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT_FOR_CHAT_MODEL,
                },
                {
                    "role": "user",
                    "content": "Questions:"
                    + USER_PROMPT_FOR_CHAT_MODEL.format(
                        user_prompt=prompt, functions=str(functions)
                    ),
                },
            ]
            start_time = time.time()
            response = self.client.chat.completions.create(
                messages=message,
                model=os.environ.get("VLLM_MODEL_NAME", self.model_name),
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
            start_time = time.time()
            if len(oai_tool) > 0:
                try:
                    response = self.client.chat.completions.create(
                        messages=message,
                        model=os.environ.get("VLLM_MODEL_NAME", self.model_name).replace("-FC", ""),
                        temperature=self.temperature,
                        max_tokens=self.max_tokens,
                        top_p=self.top_p,
                        tools=oai_tool,
                        tool_choice='auto', # this is important as it let's the model decide when to use FC
                    )
                except Exception as e:
                    print(f"\nError while trying to do FC: {e}\n")
                    print(f"Messages={message}")
                    print(f"Functions={functions}\n")
                    API_FAILURE_MESSAGE = f"API Failure: {e}"
            else:
                # @KS: TODO: Gorilla decided not to use the tool? What's going on here.
                print(f"DEBUG: BFCL decided to not use the tool.")
                print(f"Prompt = {prompt}")
                print(f"Functions = {functions}")
                response = self.client.chat.completions.create(
                    messages=message,
                    model=os.environ.get("VLLM_MODEL_NAME", self.model_name).replace("-FC", ""),
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
                print("Error while trying to extract function calls from response:", e)
                if API_FAILURE_MESSAGE:
                    result = API_FAILURE_MESSAGE
                else:
                    result = response.choices[0].message.content
        metadata = {}
        if API_FAILURE_MESSAGE:
            # do something
            metadata["input_tokens"] = -1
            metadata["output_tokens"] = -1
        else:
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
