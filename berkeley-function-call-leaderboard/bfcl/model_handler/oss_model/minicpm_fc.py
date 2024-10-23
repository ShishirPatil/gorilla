import ast
import json
import keyword
import logging
import traceback
from typing import Dict, List

import datamodel_code_generator
from datamodel_code_generator import DataModelType
from datamodel_code_generator.model import get_data_model_types
from datamodel_code_generator.parser.jsonschema import JsonSchemaParser
from overrides import overrides

from bfcl.eval_checker.ast_eval.ast_checker import convert_func_name
from bfcl.model_handler.constant import (
    GORILLA_TO_OPENAPI,
)
from bfcl.model_handler.oss_model.base_oss_handler import OSSHandler
from bfcl.model_handler.utils import (
    convert_to_tool,
    func_doc_language_specific_pre_processing,
    resolve_ast_call,
)
from overrides import overrides

logger = logging.getLogger("minicpm")


class MiniCPMFCHandler(OSSHandler):
    def __init__(self, model_name, temperature) -> None:
        super().__init__(model_name, temperature)
        self.stop_token_ids = [2, 73440]

    @overrides
    def _query_prompting(self, inference_data: dict):
        # We use the OpenAI Completions API with vLLM
        function: list[dict] = inference_data["function"]
        message: list[dict] = inference_data["message"]

        formatted_prompt: str = self._format_prompt(message, function)
        inference_data["inference_input_log"] = {"formatted_prompt": formatted_prompt}

        if hasattr(self, "stop_token_ids"):
            api_response = self.client.completions.create(
                model=self.model_name_huggingface,
                temperature=self.temperature,
                prompt=formatted_prompt,
                extra_body={
                    "skip_special_tokens": False,
                    "stop_token_ids": self.stop_token_ids,
                },
                max_tokens=512,  # TODO: Is there a better way to handle this?
            )
        else:
            api_response = self.client.completions.create(
                model=self.model_name_huggingface,
                temperature=self.temperature,
                prompt=formatted_prompt,
                extra_body={"skip_special_tokens": False},
                max_tokens=512,
            )

        return api_response

    @overrides
    def _format_prompt(self, messages, function):
        """
        "chat_template": "{% for message in messages %}{{'<|im_start|>' + message['role'] + '\n' + message['content'] + '<|im_end|>' + '\n'}}{% endfor %}{% if add_generation_prompt %}{{ '<|im_start|>assistant\n' }}{% endif %}"
        """
        tools = convert_to_tool(function, GORILLA_TO_OPENAPI, self.model_style)

        formated_messages = minicpm_input_format(
            messages=messages, tools=function, model_name=self.model_name
        )
        formatted_prompt = ""
        for message in formated_messages:
            formatted_prompt += (
                f"<|im_start|>{message['role']}\n{message['content']}<|im_end|>\n"
            )

        formatted_prompt += "<|im_start|>assistant\n"
        return formatted_prompt

    @overrides
    def _pre_query_processing_prompting(self, test_entry: dict) -> dict:
        functions: list = test_entry["function"]
        test_category: str = test_entry["id"].rsplit("_", 1)[0]

        functions = func_doc_language_specific_pre_processing(functions, test_category)

        # Hermes use its own system prompt

        return {"message": [], "function": functions}

    @overrides
    def _add_execution_results_prompting(
        self,
        inference_data: dict,
        execution_results: list[str],
        model_response_data: dict,
    ) -> dict:
        for execution_result, decoded_model_response in zip(
            execution_results, model_response_data["model_responses_decoded"]
        ):
            inference_data["message"].append(
                {"role": "tool", "content": execution_result}
            )

        return inference_data

    def decode_ast(self, result, language="Python"):
        msg = fc2dict(result)
        if (
            "tool_calls" in msg
            and msg["tool_calls"] is not None
            and len(msg["tool_calls"]) > 0
        ):
            return [
                {tool_call["name"]: tool_call["arguments"]}
                for tool_call in msg["tool_calls"]
            ]
        else:
            return msg["content"]

    def decode_execute(self, result):
        msg = fc2dict(result)
        if (
            "tool_calls" in msg
            and msg["tool_calls"] is not None
            and len(msg["tool_calls"]) > 0
        ):
            execution_list = []
            for tool_call in msg["tool_calls"]:
                func_name = tool_call["name"]
                args_str = ", ".join(
                    f"{k}={repr(v)}" for k, v in tool_call["arguments"].items()
                )
                execution_list.append(f"{func_name}({args_str})")
            return execution_list
        else:
            return msg["content"]


def message_format(msg, system_suffix="", user_prefix=""):
    if "thought" in msg and msg["thought"] is not None and len(msg["thought"]) > 0:
        thought_prefix = f"<|thought_start|>\n{msg['thought']}\n<|thought_end|>\n"
    else:
        thought_prefix = ""
    if msg["role"] == "assistant":
        content = msg.get("content", "")
        if content is None:
            content = ""
        if (
            "tool_calls" in msg
            and msg["tool_calls"] is not None
            and len(msg["tool_calls"]) > 0
        ):

            def add_quotes(variable):
                if isinstance(variable, str):
                    return repr(variable)
                else:
                    return str(variable)

            tool_calls = []
            for tool_call in msg["tool_calls"]:
                if tool_call is None:
                    continue
                tool_name = tool_call["name"]
                if "arguments" not in tool_call or tool_call["arguments"] is None:
                    continue
                if isinstance(tool_call["arguments"], str):
                    try:
                        tool_call["arguments"] = json.loads(tool_call["arguments"])
                    except:
                        continue
                args = ",".join(
                    [k + "=" + add_quotes(v) for k, v in tool_call["arguments"].items()]
                )
                tool_calls.append(f"{tool_name}({args})")

            content = (
                thought_prefix
                + "<|tool_call_start|>\n```python\n"
                + "\n".join(tool_calls).strip()
                + "\n```\n<|tool_call_end|>\n"
                + content
            )
            # msg["tool_call_string"] = "\n".join(tool_calls).strip()
            msg["content"] = content
        else:
            content = thought_prefix + content
            msg["content"] = content
    elif msg["role"] == "user":
        msg["content"] = user_prefix + "\n" + msg["content"]
    elif msg["role"] == "system":
        msg["content"] = msg["content"] + "\n" + system_suffix
    msg["content"] = msg["content"].strip()
    return msg


def jsonschema_to_code(jsonschema: dict) -> str:
    input_text = json.dumps(jsonschema)
    if datamodel_code_generator.get_version() < "0.26.2":
        from datamodel_code_generator.format import PythonVersion

        data_model_types = get_data_model_types(
            DataModelType.PydanticBaseModel,
            target_python_version=PythonVersion.PY_310,
        )
    else:
        from datamodel_code_generator.format import DatetimeClassType, PythonVersion

        data_model_types = get_data_model_types(
            DataModelType.PydanticBaseModel,
            target_python_version=PythonVersion.PY_310,
            target_datetime_class=DatetimeClassType.Datetime,
        )
    parser = JsonSchemaParser(
        source=input_text,
        data_model_type=data_model_types.data_model,
        data_model_root_type=data_model_types.root_model,
        data_model_field_type=data_model_types.field_model,
        data_type_manager_type=data_model_types.data_type_manager,
        target_python_version=PythonVersion.PY_311,
        dump_resolve_reference_action=data_model_types.dump_resolve_reference_action,
        field_constraints=True,
    )
    results = parser.parse()
    return results


def transform_function(function: dict):
    """turn json format of function into signature"""
    params, default_params = [], []
    for prop_name, prop in function["parameters"]["properties"].items():
        if "default" in prop:
            default_params.append(f'{prop_name}={repr(prop["default"])}')
        elif prop_name not in function["parameters"].get("required", []):
            default_params.append(f"{prop_name}={repr(None)}")
        else:
            params.append(prop_name)
    ps = ", ".join(params + default_params)
    res = "def {f_name}({ps}):\n".format(f_name=function["name"], ps=ps)
    f_des = function.get("description", "")
    content = jsonschema_to_code(function["parameters"])
    if "class" in content:
        i = content.index("class")
        # print(content[:i])
        content = content[i:]
    classes, args = content.split("class Model(BaseModel):", 1)
    lint_msg = f'    """\n    {f_des}\n    Args:\n{args}\n    """\n'
    res += lint_msg
    if len(classes) > 0:
        res = classes + res
    return res


def rename_tool(tool, model_name):
    properties = {}
    tool["name"] = convert_func_name(tool["name"], model_name)
    for key, value in tool["parameters"]["properties"].items():
        if key in keyword.kwlist:
            properties["_" + key] = value
        else:
            properties[key] = value
    tool["parameters"]["properties"] = properties
    return tool


def minicpm_input_format(
    messages: List[Dict],
    tools: List[Dict],
    add_to_system=True,
    model_name="openbmb/MiniCPM3-4B",
):
    """
    Process the input messages, global_arguments, tools, tool_choice,
        and convert it into a input string.
    The global arguments and tools can not be both empty.
    parameters:
        messages: List[Dict]
            the input messages
            For example:
        tools: List[Dict]
            the tools list you can use
            For example:
    """
    if tools is not None and len(tools) > 0:
        header = "from enum import Enum\nfrom typing import List, Dict, Optional\nfrom pydantic import BaseModel, Field\n\n"
        tools_string = header
        for tool in tools:
            tool = rename_tool(tool, model_name)
            try:
                tools_string += "\n\n" + transform_function(tool)
            except:
                print(traceback.format_exc())
        tools_template = """# Functions
Here is a list of functions that you can invoke:
```python
{tools}
```

# Function Call Rule and Output Format
- If the user's question can be answered without calling any function, please answer the user's question directly. In this situation, you should return your thought and answer the user's question directly.
- If the user cannot be answered without calling any function, and the user does not provide enough information to call functions, please ask the user for more information. In this situation, you should return your thought and ask the user for more information.
- If the user's question cannot be answered without calling any function, and the user has provided enough information to call functions to solve it, you should call the functions. In this situation, the assistant should return your thought and call the functions.
- Use default parameters unless the user has specified otherwise.
- You should answer in the following format:

<|thought_start|>
{{explain why the user's question can be answered without calling a function or why you should ask the user for more information or why you should call one or more functions and your plan to solve the user's question.}}
<|thought_end|>
<|tool_call_start|>
```python
func1(params_name=params_value, params_name2=params_value2...)
func2(params)
```
<|tool_call_end|>
{{answer the user's question directly or ask the user for more information}}
"""
        tools_string = tools_template.format(tools=tools_string).strip()
    else:
        tools_string = ""

    if add_to_system:
        if len(messages) > 0 and messages[0]["role"] != "system":
            messages.insert(0, {"role": "system", "content": ""})
        return [
            message_format(msg, system_suffix=tools_string, user_prefix="")
            for msg in messages
        ]
    else:
        return [
            message_format(msg, system_suffix="", user_prefix=tools_string)
            for msg in messages
        ]


def convert_function_call_to_json(string):
    # print('converting', string)
    try:
        tool_calls = []
        x = ast.parse(string)
        for tool in x.body:
            function_name = tool.value.func.id
            function_args = {}
            for kw in tool.value.keywords:
                function_args[kw.arg] = ast.literal_eval(kw.value)
            this_one = {"name": function_name, "arguments": function_args}
            # print('converted to', this_one)
            tool_calls.append(this_one)
        return tool_calls
    except Exception:
        return []


def fc2dict(
    sequence: str,
    tool_call_start="<|tool_call_start|>",
    tool_call_end="<|tool_call_end|>",
    thought_start="<|thought_start|>",
    thought_end="<|thought_end|>",
):
    if thought_end in sequence and thought_start in sequence:
        thought_string, sequence = sequence.rsplit(thought_end, 1)
        thought_string = thought_string.split(thought_start, 1)[1]
    else:
        thought_string = ""
    if tool_call_start in sequence and tool_call_end in sequence:
        tool_call_string, content = sequence.rsplit(tool_call_end, 1)
        tool_call_string = tool_call_string.split(tool_call_start, 1)[1]
        try:
            tool_calls = []
            tool_call_string = tool_call_string.strip()
            if tool_call_string.startswith("```"):
                tool_call_string = tool_call_string.lstrip("```").strip()
                if tool_call_string.startswith("python"):
                    tool_call_string = tool_call_string.lstrip("python").strip()
            if tool_call_string.endswith("```"):
                tool_call_string = tool_call_string.rstrip("```").strip()
            for kw in keyword.kwlist:
                tool_call_string = tool_call_string.replace(
                    "," + kw + "=", "," + kw + "_="
                )
                tool_call_string = tool_call_string.replace(
                    " " + kw + "=", " " + kw + "_="
                )
                tool_call_string = tool_call_string.replace(
                    "(" + kw + "=", "(" + kw + "_="
                )

            parsed = ast.parse(tool_call_string)

            for elem in parsed.body:
                assert isinstance(elem.value, ast.Call)
                calls = resolve_ast_call(elem.value)

                for func_name, func_args in calls.items():
                    new_args = {}
                    for k, v in func_args.items():
                        for kw in keyword.kwlist:
                            if k == kw + "_":
                                k = kw
                        new_args[k] = v

                    this_one = {"name": func_name, "arguments": new_args}
                    tool_calls.append(this_one)

            return {
                "content": content.strip(),
                "tool_calls": tool_calls,
                "role": "assistant",
            }
        except:
            logger.error(traceback.format_exc())
            return {
                "content": content.strip(),
                "role": "assistant",
                "thought": thought_string,
            }
    else:
        return {
            "content": sequence.strip(),
            "role": "assistant",
            "thought": thought_string,
        }
