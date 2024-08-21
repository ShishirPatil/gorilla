import json

from bfcl.model_handler.oss_handler import OSSHandler
from bfcl.model_handler.model_style import ModelStyle

SYSTEM_PROMPT = """You are an AI assistant for function calling. 
For politically sensitive questions, security and privacy issues, 
and other non-computer science questions, you will refuse to answer\n
""".strip()

TASK_INSTRUCTION = """
You are an expert in composing functions. You are given a question and a set of possible functions. 
Based on the question, you will need to make one or more function/tool calls to achieve the purpose. 
If none of the function can be used, point it out and refuse to answer. 
If the given question lacks the parameters required by the function, also point it out.
""".strip()


FORMAT_INSTRUCTION = """
The output MUST strictly adhere to the following JSON format, and NO other text MUST be included.
The example format is as follows. Please make sure the parameter type is correct. If no function call is needed, please make tool_calls an empty list '[]'
```
{
  "tool_calls": [
    {"name": "func_name1", "arguments": {"argument1": "value1", "argument2": "value2"}},
    ... (more tool calls as required)
  ]
}
```
"""


class xLAMHandler(OSSHandler):
    def __init__(
        self, model_name, temperature=0.001, top_p=1, max_tokens=512, dtype="bfloat16"
    ) -> None:
        super().__init__(model_name, temperature, top_p, max_tokens, dtype)
        self.model_style = ModelStyle.OSSMODEL

    def _format_prompt(query, functions, test_category):
        def convert_to_xlam_tool(tools):
            """Convert the Gorilla function call format to xlam format"""
            if isinstance(tools, dict):
                xlam_tools = {
                    "name": tools["name"],
                    "description": tools["description"],
                    "parameters": tools["parameters"].get("properties", {}),
                }
                required = tools["parameters"].get("required", [])
                for param in required:
                    xlam_tools["parameters"][param]["required"] = True
            elif isinstance(tools, list):
                xlam_tools = []
                for tool in tools:
                    xlam_tools.append(convert_to_xlam_tool(tool))
            else:
                xlam_tools = tools
            return xlam_tools

        tools = convert_to_xlam_tool(functions)

        task_instruction = TASK_INSTRUCTION
        user_query = ""
        for q in query:
            if q["role"] == "system":
                task_instruction += f"\n{q['content']}"
            elif q["role"] == "user":
                user_query += f"\n{q['content']}"

        content = f"[BEGIN OF TASK INSTRUCTION]\n{task_instruction}\n[END OF TASK INSTRUCTION]\n\n"
        content += (
            "[BEGIN OF AVAILABLE TOOLS]\n"
            + json.dumps(tools)
            + "\n[END OF AVAILABLE TOOLS]\n\n"
        )
        content += f"[BEGIN OF FORMAT INSTRUCTION]\n{FORMAT_INSTRUCTION}\n[END OF FORMAT INSTRUCTION]\n\n"
        content += f"[BEGIN OF QUERY]\n{user_query}\n[END OF QUERY]\n\n"
        return SYSTEM_PROMPT + f"### Instruction:\n{content}\n### Response:"

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
            format_prompt_func,
            use_default_system_prompt=False,
            include_default_formatting_prompt=False,
        )

    def decode_ast(self, result, language="Python"):
        result_list = self.convert_to_dict(result)
        return result_list

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
            else:
                print(f"Invalid format: {tool_call}")

        return python_format

    def decode_execute(self, result):
        try:
            result_json = json.loads(result)
        except:
            return result
        if isinstance(result_json, list):
            tool_calls = result_json
        elif isinstance(result_json, dict):
            tool_calls = result_json.get("tool_calls", [])
        else:
            tool_calls = []
        function_call = self.xlam_json_to_python_tool_calls(tool_calls)
        return function_call

    def convert_to_dict(self, input_str):
        """
        Convert a JSON-formatted string into a dictionary of tool calls and their arguments.

        Parameters:
        - input_str (str): A JSON-formatted string containing 'tool_calls' with 'name' and 'arguments'.

        Returns:
        - list[dict]: A list of dictionaries with tool call names as keys and their arguments as values.
        """
        try:
            data = json.loads(input_str)
        except json.JSONDecodeError:
            return input_str

        tool_calls = data if isinstance(data, list) else data.get("tool_calls", [])

        result_list = [
            {tool_call.get("name", ""): tool_call.get("arguments", {})}
            for tool_call in tool_calls
            if isinstance(tool_call, dict)
        ]

        return result_list
