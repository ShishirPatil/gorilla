import json

from bfcl.model_handler.oss_model.base_oss_handler import OSSHandler
from bfcl.model_handler.utils import (
    convert_system_prompt_into_user_prompt,
    func_doc_language_specific_pre_processing,
)

TASK_INSTRUCTION = """You are a tool calling assistant. In order to complete the user's request, you need to select one or more appropriate tools from the following tools and fill in the correct values for the tool parameters. Your specific tasks are:
1. Make one or more function/tool calls to meet the request based on the question.
2. If none of the function can be used, point it out and refuse to answer.
3. If the given question lacks the parameters required by the function, also point it out.
"""

FORMAT_INSTRUCTION = """
The output MUST strictly adhere to the following JSON format, and NO other text MUST be included.
The example format is as follows. Please make sure the parameter type is correct. If no function call is needed, please directly output an empty list '[]'
```
[
    {"name": "func_name1", "arguments": {"argument1": "value1", "argument2": "value2"}},
    ... (more tool calls as required)
]
```
"""


class HammerHandler(OSSHandler):
    def __init__(self, model_name, temperature) -> None:
        super().__init__(model_name, temperature)

    def _format_prompt(self, messages, function):
        """
        "chat_template": "{% set system_message = 'You are a helpful assistant.' %}{% if messages[0]['role'] == 'system' %}{% set system_message = messages[0]['content'] %}{% endif %}{% if system_message is defined %}{{ '<|im_start|>system\n' + system_message + '<|im_end|>\n' }}{% endif %}{% for message in messages %}{% set content = message['content'] %}{% if message['role'] == 'user' %}{{ '<|im_start|>user\n' + content + '<|im_end|>\n<|im_start|>assistant\n' }}{% elif message['role'] == 'assistant' %}{{ content + '<|im_end|>' + '\n' }}{% endif %}{% endfor %}",
        """

        def convert_to_format_tool(tools):

            if isinstance(tools, dict):
                format_tools = {
                    "name": tools["name"],
                    "description": tools["description"],
                    "parameters": tools["parameters"].get("properties", {}),
                }

                for param in format_tools["parameters"].keys():
                    if "properties" in format_tools["parameters"][param] and isinstance(
                        format_tools["parameters"][param]["properties"], dict
                    ):
                        required = format_tools["parameters"][param].get("required", [])
                        format_tools["parameters"][param] = format_tools["parameters"][param]["properties"]
                        for p in required:
                            format_tools["parameters"][param][p]["required"] = True

                required = tools["parameters"].get("required", [])
                for param in required:
                    format_tools["parameters"][param]["required"] = True
                for param in format_tools["parameters"].keys():
                    if "default" in format_tools["parameters"][param]:
                        default = format_tools["parameters"][param]["default"]
                        format_tools["parameters"][param][
                            "description"
                        ] += f"default is '{default}'"
                return format_tools
            elif isinstance(tools, list):
                return [convert_to_format_tool(tool) for tool in tools]
            else:
                return tools

        tools = convert_to_format_tool(function)

        user_query = ""

        for message in messages:
            user_query += f"{message['role']}: {message['content']}\n"
        if messages[-1]["role"] != "user":
            user_query += "user:  \n"

        content = f"[BEGIN OF TASK INSTRUCTION]\n{TASK_INSTRUCTION}\n[END OF TASK INSTRUCTION]\n\n"
        content += (
            "[BEGIN OF AVAILABLE TOOLS]\n"
            + json.dumps(tools)
            + "\n[END OF AVAILABLE TOOLS]\n\n"
        )
        content += f"[BEGIN OF FORMAT INSTRUCTION]\n{FORMAT_INSTRUCTION}\n[END OF FORMAT INSTRUCTION]\n\n"
        content += f"[BEGIN OF QUERY]\n{user_query}\n[END OF QUERY]\n\n"

        return f"<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n<|im_start|>user\n{content}<|im_end|>\n<|im_start|>assistant\n"

    def decode_ast(self, result, language="Python"):
        result = result.replace("```", "")
        try:
            result = json.loads(result)
        except:
            result = []

        decoded_output = []
        for invoked_function in result:
            name = invoked_function["name"]
            params = invoked_function["arguments"]
            decoded_output.append({name: params})
        return decoded_output

    @staticmethod
    def xlam_json_to_python_tool_calls(tool_calls):
        """
        Converts a list of function calls in xLAM JSON format to Python format.

        Parameters:
        tool_calls (list): A list of dictionaries, where each dictionary represents a function call in xLAM JSON format.

        Returns:
        python_format (list): A list of strings, where each string is a function call in Python format.
        """
        if not isinstance(tool_calls, list):
            tool_calls = [tool_calls]

        python_format = []
        for tool_call in tool_calls:
            if isinstance(tool_call, dict):
                name = tool_call.get("name", "")
                arguments = tool_call.get("arguments", {})
                args_str = ", ".join(
                    [f"{key}={repr(value)}" for key, value in arguments.items()]
                )
                python_format.append(f"{name}({args_str})")

        return python_format

    def decode_execute(self, result):
        result = result.replace("```", "")
        try:
            result = json.loads(result)
        except:
            result = []

        if isinstance(result, list):
            tool_calls = result
        elif isinstance(result, dict):
            tool_calls = result.get("tool_calls", [])
        else:
            tool_calls = []
        function_call = self.xlam_json_to_python_tool_calls(tool_calls)
        return function_call

    def _pre_query_processing_prompting(self, test_entry: dict) -> dict:
        functions: list = test_entry["function"]
        test_category: str = test_entry["id"].rsplit("_", 1)[0]

        functions = func_doc_language_specific_pre_processing(functions, test_category)

        # Convert all system prompts to user prompts, as Hammer doesn't take system prompts
        test_entry["question"][0] = convert_system_prompt_into_user_prompt(
            test_entry["question"][0]
        )

        # Hammer have its own system prompt, so we don't need to add the default system prompt

        return {"message": [], "function": functions}
