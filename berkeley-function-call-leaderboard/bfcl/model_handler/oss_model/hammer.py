import json

from bfcl.model_handler.model_style import ModelStyle
from bfcl.model_handler.oss_model.salesforce import SalesforceHandler


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


class HammerHandler(SalesforceHandler):
    def __init__(
        self, model_name, temperature=0.001, top_p=1, max_tokens=512, dtype="bfloat16"
    ) -> None:
        super().__init__(model_name, temperature, top_p, max_tokens, dtype)
        self.model_style = ModelStyle.OSSMODEL

    def _format_prompt(query, functions, test_category):
        def convert_to_format_tool(tools):

            if isinstance(tools, dict):
                format_tools = {
                    "name": tools["name"],
                    "description": tools["description"],
                    "parameters": tools["parameters"].get("properties", {}),
                }
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

        tools = convert_to_format_tool(functions)

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

        return f"<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n<|im_start|>user\n{content}<|im_end|>\n<|im_start|>assistant\n"

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
        )

    def decode_ast(self, result, language="Python"):
        result = result.replace("```", "")
        return super().decode_ast(result)

    def decode_execute(self, result):
        result = result.replace("```", "")
        return super().decode_execute(result)
