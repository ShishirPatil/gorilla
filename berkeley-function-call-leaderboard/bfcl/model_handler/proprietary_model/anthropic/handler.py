import json
import time

from anthropic.types import TextBlock, ToolUseBlock

from bfcl.model_handler import utils
from bfcl.model_handler import constants
from bfcl.model_handler.base import ModelStyle
from bfcl.model_handler.proprietary_model.anthropic.prompt_handler import AnthropicPromptHandler


class AnthropicFCHandler(AnthropicPromptHandler):
    model_style = ModelStyle.ANTHROPIC_FC

    @classmethod
    def supported_models(cls):
        return [
            'claude-3-opus-20240229-FC',
            'claude-3-sonnet-20240229-FC',
            'claude-3-5-sonnet-20240620-FC',
            'claude-3-haiku-20240307-FC',
        ]

    def inference(self, prompt, functions, test_category):
        if "FC" not in self.model_name:
            return super().inference(prompt, functions, test_category)

        prompt = utils.augment_prompt_by_languge(prompt, test_category)
        functions = utils.language_specific_pre_processing(functions, test_category, True)
        if type(functions) is not list:
            functions = [functions]
        claude_tool = utils.convert_to_tool(
            functions, constants.GORILLA_TO_OPENAPI, self.model_style, test_category, True
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

    def decode_ast(self, result, language="python"):
        if "FC" not in self.model_name:
            decoded_output = utils.ast_parse(result,language)
        else:
            decoded_output = []
            for invoked_function in result:
                name = list(invoked_function.keys())[0]
                params = json.loads(invoked_function[name])
                if language.lower() != "python":
                    for key in params:
                        params[key] = str(params[key])
                decoded_output.append({name: params})
        return decoded_output

    def decode_execute(self, result):
        if "FC" not in self.model_name:
            decoded_output = utils.ast_parse(result)
            execution_list = []
            for function_call in decoded_output:
                for key, value in function_call.items():
                    execution_list.append(
                        f"{key}({','.join([f'{k}={repr(v)}' for k, v in value.items()])})"
                    )
            return execution_list
        else:
            function_call = utils.convert_to_function_call(result)
            return function_call
