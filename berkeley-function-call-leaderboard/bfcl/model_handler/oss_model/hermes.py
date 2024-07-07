import json

from bfcl.model_handler.constants import GORILLA_TO_OPENAPI
from bfcl.model_handler.utils import convert_to_tool
from bfcl.model_handler.oss_model.base import OssModelHandler


class HermesHandler(OssModelHandler):
    prompt_template = (
        '<|im_start|>system\n'
        'You are a function calling AI model. You are provided with function signatures within <tools></tools> XML tags. '
        "You may call one or more functions to assist with the user query. Don't make assumptions about what values to "
        'plug into functions. Here are the available tools: <tools>{functions}</tools> Use the following pydantic model '
        'json schema for each tool call you will make: {pydantic_func_schema}. '
        'For each function call return a json object with function name and arguments within <tool_call></tool_call> XML tags as follows:\n'
        '<tool_call>{{"arguments": <args-dict>, "name": <function-name>}}</tool_call><|im_end|>'
        '<|im_start|>user\n{user_input}<|im_end|>'
    )

    @classmethod
    def supported_models(cls):
        return [
            'NousResearch/Hermes-2-Pro-Mistral-7B',
        ]

    def get_prompt(self, user_input, functions, test_category) -> str:
        # Hermes use Langchain to OpenAI conversion. It does not use tool call but function call.
        function = convert_to_tool(function, GORILLA_TO_OPENAPI, self.model_style, test_category, True)
        pydantic_func_schema = {
            "properties": {
                "arguments": {
                    "title": "Arguments",
                    "type": "object"
                },
                "name": {
                    "title": "Name",
                    "type": "string"
                }
            },
            "required": ["arguments", "name"],
            "title": "FunctionCall",
            "type": "object"
        }
        return self.prompt_template.format(
            pydantic_func_schema=pydantic_func_schema,
            functions=functions, 
            user_input=user_input,
        )

    def decode_ast(self, result, language="python"):
        lines = result.split("\n")
        flag = False
        func_call = []
        for line in lines:
            if "<tool_call>" == line:
                flag = True
            elif "</tool_call>" == line:
                flag = False
            else:
                if flag:
                    line = line.replace("'", '"')
                    tool_result = json.loads(line)
                    if language.lower() != "python":
                        # all values of the json are casted to string for java and javascript
                        for key in tool_result["arguments"]:
                            tool_result["arguments"][key] = str(
                                tool_result["arguments"][key]
                            )
                    func_call.append({tool_result["name"]: tool_result["arguments"]})
                flag = False
        return func_call

    def decode_execute(self, result):
        lines = result.split("\n")
        flag = False
        function_call_list = []
        for line in lines:
            if "<tool_call>" == line:
                flag = True
            elif "</tool_call>" == line:
                flag = False
            else:
                if flag:
                    line = line.replace("'", '"')
                    tool_result = json.loads(line)
                    function_call_list.append(
                        {tool_result["name"]: tool_result["arguments"]}
                    )
                flag = False
        execution_list = []
        for function_call in function_call_list:
            for key, value in function_call.items():
                execution_list.append(
                    f"{key}({','.join([f'{k}={repr(v)}' for k,v in value.items()])})"
                )
        return execution_list
