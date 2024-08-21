import json
import os
import time

from anthropic import Anthropic
from anthropic.types import TextBlock, ToolUseBlock
from bfcl.model_handler.constant import (
    GORILLA_TO_OPENAPI,
    USER_PROMPT_FOR_CHAT_MODEL,
    DEFAULT_SYSTEM_PROMPT,
)
from bfcl.model_handler.handler import BaseHandler
from bfcl.model_handler.model_style import ModelStyle
from bfcl.model_handler.utils import (
    ast_parse,
    convert_to_function_call,
    convert_to_tool,
    func_doc_language_specific_pre_processing,
    user_prompt_pre_processing_chat_model,
    convert_system_prompt_into_user_prompt,
    combine_consecutive_user_prompr,
)


class ClaudeHandler(BaseHandler):
    def __init__(self, model_name, temperature=0.001, top_p=1, max_tokens=1000) -> None:
        super().__init__(model_name, temperature, top_p, max_tokens)
        self.model_style = ModelStyle.Anthropic

        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    def inference(self, prompt, functions, test_category):
        # Chatting model
        if "FC" not in self.model_name:
            start = time.time()
            functions = func_doc_language_specific_pre_processing(
                functions, test_category
            )

            # Claude takes in system prompt in a specific field, not in the message field, so we don't need to add it to the message
            prompt = user_prompt_pre_processing_chat_model(
                prompt, USER_PROMPT_FOR_CHAT_MODEL, test_category, functions
            )
            # This deals with any system prompts that come with the question
            prompt = convert_system_prompt_into_user_prompt(prompt)

            prompt = combine_consecutive_user_prompr(prompt)
            
            message = prompt

            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                top_p=self.top_p,
                system=DEFAULT_SYSTEM_PROMPT,
                messages=message,
            )
            latency = time.time() - start
            metadata = {}
            metadata["input_tokens"] = response.usage.input_tokens
            metadata["output_tokens"] = response.usage.output_tokens
            metadata["latency"] = latency
            result = response.content[0].text
            return result, metadata
        # Function call model
        else:
            functions = func_doc_language_specific_pre_processing(
                functions, test_category
            )

            claude_tool = convert_to_tool(
                functions, GORILLA_TO_OPENAPI, self.model_style, test_category
            )
            prompt = convert_system_prompt_into_user_prompt(prompt)
            message = combine_consecutive_user_prompr(prompt)
            
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
            result = tool_call_outputs if tool_call_outputs else text_outputs[0]
            return result, {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "latency": latency,
            }

    def decode_ast(self, result, language="Python"):
        if "FC" not in self.model_name:
            func = result
            if " " == func[0]:
                func = func[1:]
            if not func.startswith("["):
                func = "[" + func
            if not func.endswith("]"):
                func = func + "]"
            decode_output = ast_parse(func, language)
            return decode_output

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
            decode_output = ast_parse(func)
            execution_list = []
            for function_call in decode_output:
                for key, value in function_call.items():
                    execution_list.append(
                        f"{key}({','.join([f'{k}={repr(v)}' for k, v in value.items()])})"
                    )
            return execution_list

        else:
            function_call = convert_to_function_call(result)
            return function_call
