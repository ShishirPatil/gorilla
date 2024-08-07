import json
import os
import time

from anthropic import Anthropic
from anthropic.types import TextBlock, ToolUseBlock
from bfcl.model_handler.claude_prompt_handler import ClaudePromptingHandler
from bfcl.model_handler.constant import GORILLA_TO_OPENAPI
from bfcl.model_handler.handler import BaseHandler
from bfcl.model_handler.model_style import ModelStyle
from bfcl.model_handler.utils import (
    ast_parse,
    augment_prompt_by_languge,
    convert_to_function_call,
    convert_to_tool,
    language_specific_pre_processing,
)


class ClaudeFCHandler(BaseHandler):
    def __init__(self, model_name, temperature=0.7, top_p=1, max_tokens=1000) -> None:
        super().__init__(model_name, temperature, top_p, max_tokens)
        self.model_style = ModelStyle.Anthropic_Prompt

        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    def inference(self, prompt, functions, test_category):
        if "FC" not in self.model_name:
            handler = ClaudePromptingHandler(self.model_name, self.temperature, self.top_p, self.max_tokens)
            return handler.inference(prompt, functions, test_category)
        else:
            prompt = augment_prompt_by_languge(prompt, test_category)
            functions = language_specific_pre_processing(functions, test_category)
            if type(functions) is not list:
                functions = [functions]
            claude_tool = convert_to_tool(
                functions, GORILLA_TO_OPENAPI, self.model_style, test_category
            )
            message = [{"role": "user", "content": prompt}]
            start_time = time.time()

            response = self.client.messages.create(
                model=self.model_name.strip("-FC"),
                max_tokens=self.max_tokens,
                tools=claude_tool,
                messages=message,
            )
            latency = time.time() - start_time
            text_outputs = []
            tool_call_outputs = []
            for content in response.content:
                if isinstance(content, TextBlock):
                    text_outputs.append(content.text)
                elif isinstance(content, ToolUseBlock):
                    tool_call_outputs.append({content.name: json.dumps(content.input)})
            result =  tool_call_outputs if tool_call_outputs else text_outputs[0]
            return result, {"input_tokens": response.usage.input_tokens, "output_tokens": response.usage.output_tokens, "latency": latency}

    def decode_ast(self,result,language="Python"):
        if "FC" not in self.model_name:
            decoded_output = ast_parse(result,language)
        else:
            decoded_output = []
            for invoked_function in result:
                name = list(invoked_function.keys())[0]
                params = json.loads(invoked_function[name])
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
