import re
import ast
import inspect

from model_handler.oss_handler import OSSHandler
from model_handler.utils import convert_to_tool
from model_handler.constant import GORILLA_TO_OPENAPI
from model_handler.model_style import ModelStyle
from model_handler.utils import ast_parse


def dict_to_function_format(data):
    tool_name = data['tool_name']
    arguments = data.get('tool_arguments', {})
    args_str = ', '.join(f"{k}={repr(v)}" for k, v in arguments.items())
    return f"{tool_name}({args_str})"


def process_multiple_tool_calls(input_string):
    # Extract tool calls using regex
    tool_calls = re.findall(r'<tool_call>(.*?)</tool_call>', input_string, re.DOTALL)

    results = []
    for call in tool_calls:
        try:
            # Convert string representation of dict to actual dict
            call_dict = ast.literal_eval(call)
            # Convert dict to function format
            results.append(dict_to_function_format(call_dict))
        except (ValueError, SyntaxError) as e:
            print(f"Error processing tool call: {e}")
            print(f"Problematic call: {call}")

    return results


class StormHandler(OSSHandler):
    def __init__(self, model_name, temperature=0.001, top_p=1, max_tokens=1000, dtype="bfloat16") -> None:
        super().__init__(model_name, temperature, top_p, max_tokens, dtype)

    def _format_prompt(prompts, function, test_category):
        function = convert_to_tool(
            function, GORILLA_TO_OPENAPI, ModelStyle.OSSMODEL, test_category
        )
        tool_call_format = """{"tool_name": <function-name>, "tool_arguments": <args-dict>}"""

        formatted_prompt = inspect.cleandoc(
            """<|begin_of_text|><|start_header_id|>system<|end_header_id|>

            You are a function calling AI model. You may call one or more functions to assist with the user query. Don't make assumptions about what values to plug into function. The user may use the terms function calling or tool use interchangeably.

            Here are the available functions:
            <tools>{tools}</tools>

            Follow the below guidelines:
            1. If any tool needed to answer the query is not available, you must return an empty list "[]" as response.
            2. Else if query does not provide any must-have argument of a required tool, you must return an empty list "[]" as response. 
            3. Else, for each function call you must return a json object in response with function name and arguments within <tool_call></tool_call> XML tags in the format:
            <tool_call>{tool_call_format}</tool_call><|eot_id|>"""
        )

        formatted_prompt = formatted_prompt.format(
            tools=function,
            tool_call_format=tool_call_format,
        )

        for prompt in prompts:
            formatted_prompt += f"<|start_header_id|>{prompt['role']}<|end_header_id|>\n\n{prompt['content']}<|eot_id|>"

        formatted_prompt += f"<|start_header_id|>assistant<|end_header_id|>\n\n"

        return formatted_prompt

    def inference(
            self,
            test_question,
            num_gpus,
            gpu_memory_utilization,
            format_prompt_func=_format_prompt,
    ):
        return super().inference(
            test_question,
            num_gpus,
            gpu_memory_utilization,
            format_prompt_func=format_prompt_func,
            use_default_system_prompt=False,
            include_default_formatting_prompt=False,
        )

    def decode_ast(self, result, language="Python"):
        func = f"[{', '.join(process_multiple_tool_calls(result.strip()))}]"
        decode_output = ast_parse(func, language)
        return decode_output

    def decode_execute(self, result):
        return process_multiple_tool_calls(result.strip())
