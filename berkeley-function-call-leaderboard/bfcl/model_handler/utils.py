import ast
import builtins
import copy
import json
import operator
import re
from functools import reduce
from typing import Callable, List, Optional, Type, Union

from bfcl.constants.default_prompts import DEFAULT_SYSTEM_PROMPT
from bfcl.constants.type_mappings import GORILLA_TO_OPENAPI
from bfcl.model_handler.model_style import ModelStyle
from bfcl.model_handler.parser.java_parser import parse_java_function_call
from bfcl.model_handler.parser.js_parser import parse_javascript_function_call
from tenacity import (
    retry,
    retry_if_exception_message,
    retry_if_exception_type,
    wait_random_exponential,
)


def _cast_to_openai_type(properties, mapping):
    for key, value in properties.items():
        if "type" not in value:
            properties[key]["type"] = "string"
        else:
            var_type = value["type"]
            if mapping == GORILLA_TO_OPENAPI and var_type == "float":
                properties[key]["format"] = "float"
                properties[key]["description"] += " This is a float type value."
            if var_type in mapping:
                properties[key]["type"] = mapping[var_type]
            else:
                properties[key]["type"] = "string"

        # Currently support:
        # - list of any
        # - list of list of any
        # - list of dict
        # - list of list of dict
        # - dict of any

        if properties[key]["type"] == "array" or properties[key]["type"] == "object":
            if "properties" in properties[key]:
                properties[key]["properties"] = _cast_to_openai_type(
                    properties[key]["properties"], mapping
                )
            elif "items" in properties[key]:
                properties[key]["items"]["type"] = mapping[properties[key]["items"]["type"]]
                if (
                    properties[key]["items"]["type"] == "array"
                    and "items" in properties[key]["items"]
                ):
                    properties[key]["items"]["items"]["type"] = mapping[
                        properties[key]["items"]["items"]["type"]
                    ]
                elif (
                    properties[key]["items"]["type"] == "object"
                    and "properties" in properties[key]["items"]
                ):
                    properties[key]["items"]["properties"] = _cast_to_openai_type(
                        properties[key]["items"]["properties"], mapping
                    )
    return properties


def convert_to_tool(functions, mapping, model_style):
    functions = copy.deepcopy(functions)
    oai_tool = []
    for item in functions:
        if "." in item["name"] and model_style in [
            ModelStyle.OpenAI,
            ModelStyle.Mistral,
            ModelStyle.Google,
            ModelStyle.OSSMODEL,
            ModelStyle.Anthropic,
            ModelStyle.COHERE,
            ModelStyle.AMAZON,
            ModelStyle.NOVITA_AI,
        ]:
            # OAI does not support "." in the function name so we replace it with "_". ^[a-zA-Z0-9_-]{1,64}$ is the regex for the name.
            item["name"] = re.sub(r"\.", "_", item["name"])

        item["parameters"]["type"] = "object"
        item["parameters"]["properties"] = _cast_to_openai_type(
            item["parameters"]["properties"], mapping
        )

        if model_style == ModelStyle.Anthropic:
            item["input_schema"] = item["parameters"]
            del item["parameters"]

        if model_style == ModelStyle.AMAZON:
            item["inputSchema"] = {"json": item["parameters"]}
            del item["parameters"]

        if model_style in [
            ModelStyle.Google,
            ModelStyle.WRITER,
        ]:
            # Remove fields that are not supported by Gemini or Palmyra.
            # No `optional` field in function schema.
            if "optional" in item["parameters"]:
                del item["parameters"]["optional"]
            for params in item["parameters"]["properties"].values():
                # No `default` field in Google or Palmyra's schema.
                if "default" in params:
                    params["description"] += f" Default is: {str(params['default'])}."
                    del params["default"]
                # No `optional` field in parameter schema as well.
                if "optional" in params:
                    params["description"] += f" Optional: {str(params['optional'])}."
                    del params["optional"]
                # No `maximum` field.
                if "maximum" in params:
                    params["description"] += f" Maximum value: {str(params['maximum'])}."
                    del params["maximum"]
                # No `minItems` field.
                if "minItems" in params:
                    params[
                        "description"
                    ] += f" Minimum number of items: {str(params['minItems'])}."
                    del params["minItems"]
                # No `maxItems` field.
                if "maxItems" in params:
                    params[
                        "description"
                    ] += f" Maximum number of items: {str(params['maxItems'])}."
                    del params["maxItems"]
                # No `additionalProperties` field.
                if "additionalProperties" in params:
                    params[
                        "description"
                    ] += f" Additional properties: {str(params['additionalProperties'])}."
                    del params["additionalProperties"]
                # For Gemini, only `enum` field when the type is `string`.
                # For Palmyra, `enum` field is not supported.
                if "enum" in params and (
                    model_style == ModelStyle.WRITER
                    or (model_style == ModelStyle.Google and params["type"] != "string")
                ):
                    params["description"] += f" Enum values: {str(params['enum'])}."
                    del params["enum"]

        # Process the return field
        if "response" in item:
            if model_style in [
                ModelStyle.Anthropic,
                ModelStyle.Google,
                ModelStyle.FIREWORK_AI,
                ModelStyle.WRITER,
                ModelStyle.AMAZON,
                ModelStyle.NOVITA_AI,
            ]:
                item[
                    "description"
                ] += f" The response field has the following schema: {json.dumps(item['response'])}"
                del item["response"]

        if model_style in [
            ModelStyle.Anthropic,
            ModelStyle.Google,
            ModelStyle.OSSMODEL,
        ]:
            oai_tool.append(item)
        elif model_style in [
            ModelStyle.COHERE,
            ModelStyle.OpenAI,
            ModelStyle.Mistral,
            ModelStyle.FIREWORK_AI,
            ModelStyle.WRITER,
            ModelStyle.NOVITA_AI,
        ]:
            oai_tool.append({"type": "function", "function": item})
        elif model_style == ModelStyle.AMAZON:
            oai_tool.append({"toolSpec": item})

    return oai_tool


def convert_to_function_call(function_call_list):
    if type(function_call_list) == dict:
        function_call_list = [function_call_list]
    # function_call_list is of type list[dict[str, str]] or list[dict[str, dict]]
    execution_list = []
    for function_call in function_call_list:
        for key, value in function_call.items():
            if type(value) == str:
                value = json.loads(value)
            execution_list.append(
                f"{key}({','.join([f'{k}={repr(v)}' for k,v in value.items()])})"
            )

    return execution_list


def convert_value(value, type_str):
    """Convert a string value into its appropriate Python data type based on the provided type string.

    Arg:
        value: the value to convert
        type_str: the type to convert the value to

    Returns:
        The value converted into the requested type or the original value
        if the conversion failed.
    """

    if type_str in ("list", "dict"):
        try:
            return ast.literal_eval(value)
        except:
            return value

    type_class = getattr(builtins, type_str)
    try:
        return type_class(value)
    except ValueError:
        return value


def ast_parse(input_str, language="Python"):
    if language == "Python":
        cleaned_input = input_str.strip("[]'")
        parsed = ast.parse(cleaned_input, mode="eval")
        extracted = []
        if isinstance(parsed.body, ast.Call):
            extracted.append(resolve_ast_call(parsed.body))
        else:
            for elem in parsed.body.elts:
                assert isinstance(elem, ast.Call)
                extracted.append(resolve_ast_call(elem))
        return extracted
    elif language == "Java":
        return parse_java_function_call(
            input_str[1:-1]
        )  # Remove the [ and ] from the string
    elif language == "JavaScript":
        return parse_javascript_function_call(input_str[1:-1])
    else:
        raise NotImplementedError(f"Unsupported language: {language}")


def resolve_ast_call(elem):
    # Handle nested attributes for deeply nested module paths
    func_parts = []
    func_part = elem.func
    while isinstance(func_part, ast.Attribute):
        func_parts.append(func_part.attr)
        func_part = func_part.value
    if isinstance(func_part, ast.Name):
        func_parts.append(func_part.id)
    func_name = ".".join(reversed(func_parts))
    args_dict = {}
    for arg in elem.keywords:
        output = resolve_ast_by_type(arg.value)
        args_dict[arg.arg] = output
    return {func_name: args_dict}


def resolve_ast_by_type(value):
    if isinstance(value, ast.Constant):
        if value.value is Ellipsis:
            output = "..."
        else:
            output = value.value
    elif isinstance(value, ast.UnaryOp):
        output = -value.operand.value
    elif isinstance(value, ast.List):
        output = [resolve_ast_by_type(v) for v in value.elts]
    elif isinstance(value, ast.Dict):
        output = {
            resolve_ast_by_type(k): resolve_ast_by_type(v)
            for k, v in zip(value.keys, value.values)
        }
    elif isinstance(
        value, ast.NameConstant
    ):  # Added this condition to handle boolean values
        output = value.value
    elif isinstance(
        value, ast.BinOp
    ):  # Added this condition to handle function calls as arguments
        output = eval(ast.unparse(value))
    elif isinstance(value, ast.Name):
        output = value.id
    elif isinstance(value, ast.Call):
        if len(value.keywords) == 0:
            output = ast.unparse(value)
        else:
            output = resolve_ast_call(value)
    elif isinstance(value, ast.Tuple):
        output = tuple(resolve_ast_by_type(v) for v in value.elts)
    elif isinstance(value, ast.Lambda):
        output = eval(ast.unparse(value.body[0].value))
    elif isinstance(value, ast.Ellipsis):
        output = "..."
    elif isinstance(value, ast.Subscript):
        try:
            output = ast.unparse(value.body[0].value)
        except:
            output = ast.unparse(value.value) + "[" + ast.unparse(value.slice) + "]"
    else:
        raise Exception(f"Unsupported AST type: {type(value)}")
    return output


def system_prompt_pre_processing_chat_model(prompts, function_docs, test_category):
    """
    Add a system prompt to the chat model to instruct the model on the available functions and the expected response format.
    If the prompts list already contains a system prompt, append the additional system prompt content to the existing system prompt.
    """
    assert type(prompts) == list

    system_prompt_template = DEFAULT_SYSTEM_PROMPT

    system_prompt = system_prompt_template.format(functions=function_docs)

    # System prompt must be in the first position
    # If the question comes with a system prompt, append its content at the end of the chat template.
    if prompts[0]["role"] == "system":
        prompts[0]["content"] = system_prompt + "\n\n" + prompts[0]["content"]
    # Otherwise, use the system prompt template to create a new system prompt.
    else:
        prompts.insert(
            0,
            {"role": "system", "content": system_prompt},
        )

    return prompts


def convert_system_prompt_into_user_prompt(prompts: list[dict]) -> list[dict]:
    """
    Some FC models doesn't support system prompt in the message field, so we turn it into user prompt
    """
    for prompt in prompts:
        if prompt["role"] == "system":
            prompt["role"] = "user"
    return prompts


def combine_consecutive_user_prompts(prompts: list[dict]) -> list[dict]:
    """
    Some models require the prompt to be alternating between user and assistant.
    We combine consecutive user prompts into a single user prompt.
    """
    combined_prompts = []
    for prompt in prompts:
        if (
            prompt["role"] == "user"
            and combined_prompts
            and combined_prompts[-1]["role"] == "user"
        ):
            combined_prompts[-1]["content"] += "\n\n" + prompt["content"]
        else:
            combined_prompts.append(prompt)

    return combined_prompts


def _get_language_specific_hint(test_category):
    if test_category == "java":
        return " Note that the provided function is in Java 8 SDK syntax."
    elif test_category == "javascript":
        return " Note that the provided function is in JavaScript syntax."
    else:
        return " Note that the provided function is in Python 3 syntax."


def func_doc_language_specific_pre_processing(function, test_category):
    if len(function) == 0:
        return function

    assert type(function) == list
    for item in function:
        # Add language specific hints to the function description
        func_description = item["description"]
        item["description"] = item["description"] + _get_language_specific_hint(
            test_category
        )
        # Process the parameters
        properties = item["parameters"]["properties"]
        if test_category == "java":
            for key, value in properties.items():
                if value["type"] == "any":
                    properties[key][
                        "description"
                    ] += " This parameter can be of any type of Java object in string representation."
                else:
                    value[
                        "description"
                    ] += f" This is Java {value['type']} type parameter in string representation."
                if value["type"] == "ArrayList" or value["type"] == "Array":
                    value[
                        "description"
                    ] += f" The list elements are of type {value['items']['type']}; they are not in string representation."
                    del value["items"]

                value["type"] = "string"

        elif test_category == "javascript":
            for key, value in properties.items():
                if value["type"] == "any":
                    properties[key][
                        "description"
                    ] += " This parameter can be of any type of JavaScript object in string representation."
                else:
                    value[
                        "description"
                    ] += f" This is JavaScript {value['type']} type parameter in string representation."
                if value["type"] == "array":
                    value[
                        "description"
                    ] += f" The list elements are of type {value['items']['type']}; they are not in string representation."
                    del value["items"]

                if value["type"] == "dict":
                    if "properties" in value:  # not every dict has properties
                        value[
                            "description"
                        ] += f" The dictionary entries have the following schema; they are not in string representation. {json.dumps(value['properties'])}"
                        del value["properties"]

                value["type"] = "string"

    return function


def construct_tool_use_system_prompt(tools):
    tool_use_system_prompt = (
        "In this environment you have access to a set of tools you can use to answer the user's question.\n"
        "\n"
        "You may call them like this:\n"
        "<function_calls>\n"
        "<invoke>\n"
        "<tool_name>$TOOL_NAME</tool_name>\n"
        "<parameters>\n"
        "<$PARAMETER_NAME>$PARAMETER_VALUE</$PARAMETER_NAME>\n"
        "...\n"
        "</parameters>\n"
        "</invoke>\n"
        "</function_calls>\n"
        "\n"
        "Here are the tools available:\n"
        "<tools>\n"
        + "\n".join(
            [
                construct_format_tool_for_claude_prompt(
                    tool["name"], tool["description"], tool["parameters"]["properties"]
                )
                for tool in tools
            ]
        )
        + "\n</tools>"
    )

    return tool_use_system_prompt


def construct_format_tool_for_claude_prompt(name, description, parameters):
    constructed_prompt = (
        "<tool_description>\n"
        f"<tool_name>{name}</tool_name>\n"
        "<description>\n"
        f"{description}\n"
        "</description>\n"
        "<parameters>\n"
        f"{construct_format_parameters_prompt(parameters)}\n"
        "</parameters>\n"
        "</tool_description>"
    )

    return constructed_prompt


def construct_format_parameters_prompt(parameters):
    constructed_prompt = ""
    for parameter_name, parameter in parameters.items():
        if parameter_name == "required":
            continue
        if "description" in parameter:
            description_string = parameter["description"]
        else:
            description_string = ""
        if "default" in parameter:
            description_string += f"\nDefault value: {parameter['default']}"
        elif "items" in parameter:
            description_string += f"\n List element type: {str(parameter['items'])}"
        elif "properties" in parameter:
            description_string += (
                f"\n Dictionaries properties: {str(parameter['properties'])}"
            )
        if "description" in parameter:
            constructed_prompt += f"<parameter>\n<name>{parameter_name}</name>\n<type>{parameter['type']}</type>\n<description>{description_string}</description>\n</parameter>\n"
        else:
            constructed_prompt += f"<parameter>\n<name>{parameter_name}</name>\n<type>{parameter['type']}</type>\n</parameter>\n"
    constructed_prompt = constructed_prompt[:-1]
    return constructed_prompt


def _function_calls_valid_format_and_invoke_extraction(last_completion):
    """Check if the function call follows a valid format and extract the attempted function calls if so. Does not check if the tools actually exist or if they are called with the requisite params."""

    # Check if there are any of the relevant XML tags present that would indicate an attempted function call.
    function_call_tags = re.findall(
        r"<function_calls>|</function_calls>|<invoke>|</invoke>|<tool_name>|</tool_name>|<parameters>|</parameters>",
        last_completion,
        re.DOTALL,
    )
    if not function_call_tags:
        return {"status": True, "invokes": []}

    # Extract content between <function_calls> tags. If there are multiple we will only parse the first and ignore the rest, regardless of their correctness.
    match = re.search(r"<function_calls>(.*)</function_calls>", last_completion, re.DOTALL)
    if not match:
        return {
            "status": False,
            "reason": "No valid <function_calls></function_calls> tags present in your query.",
        }

    func_calls = match.group(1)

    prefix_match = re.search(r"^(.*?)<function_calls>", last_completion, re.DOTALL)
    if prefix_match:
        func_call_prefix_content = prefix_match.group(1)

    # Check for invoke tags
    invoke_regex = r"<invoke>.*?</invoke>"
    if not re.search(invoke_regex, func_calls, re.DOTALL):
        return {
            "status": False,
            "reason": "Missing <invoke></invoke> tags inside of <function_calls></function_calls> tags.",
        }

    # Check each invoke contains tool name and parameters
    invoke_strings = re.findall(invoke_regex, func_calls, re.DOTALL)
    invokes = []
    for invoke_string in invoke_strings:
        tool_name = re.findall(r"<tool_name>.*?</tool_name>", invoke_string, re.DOTALL)
        if not tool_name:
            return {
                "status": False,
                "reason": "Missing <tool_name></tool_name> tags inside of <invoke></invoke> tags.",
            }
        if len(tool_name) > 1:
            return {
                "status": False,
                "reason": "More than one tool_name specified inside single set of <invoke></invoke> tags.",
            }

        parameters = re.findall(r"<parameters>.*?</parameters>", invoke_string, re.DOTALL)
        if not parameters:
            return {
                "status": False,
                "reason": "Missing <parameters></paraeters> tags inside of <invoke></invoke> tags.",
            }
        if len(parameters) > 1:
            return {
                "status": False,
                "reason": "More than one set of <parameters></parameters> tags specified inside single set of <invoke></invoke> tags.",
            }

        # Check for balanced tags inside parameters
        tags = re.findall(
            r"<.*?>",
            parameters[0].replace("<parameters>", "").replace("</parameters>", ""),
            re.DOTALL,
        )
        if len(tags) % 2 != 0:
            return {
                "status": False,
                "reason": "Imbalanced tags inside <parameters></parameters> tags.",
            }

        # Loop through the tags and check if each even-indexed tag matches the tag in the position after it (with the / of course). If valid store their content for later use.
        parameters_with_values = []
        for i in range(0, len(tags), 2):
            opening_tag = tags[i]
            closing_tag = tags[i + 1]
            closing_tag_without_second_char = closing_tag[:1] + closing_tag[2:]
            if closing_tag[1] != "/" or opening_tag != closing_tag_without_second_char:
                return {
                    "status": False,
                    "reason": "Non-matching opening and closing tags inside <parameters></parameters> tags.",
                }

            parameters_with_values.append(
                (
                    opening_tag[1:-1],
                    re.search(
                        rf"{opening_tag}(.*?){closing_tag}", parameters[0], re.DOTALL
                    ).group(1),
                )
            )

        # Parse out the full function call
        invokes.append(
            {
                "tool_name": tool_name[0]
                .replace("<tool_name>", "")
                .replace("</tool_name>", ""),
                "parameters_with_values": parameters_with_values,
            }
        )

    return {
        "status": True,
        "invokes": invokes,
        "prefix_content": func_call_prefix_content,
    }


def _convert_value(value, type_str):
    """Convert a string value into its appropriate Python data type based on the provided type string.

    Arg:
        value: the value to convert
        type_str: the type to convert the value to

    Returns:
        The value converted into the requested type or the original value
        if the conversion failed.
    """

    if type_str in ("list", "dict"):
        try:
            return ast.literal_eval(value)
        except:
            return value
    if type_str == "string":
        type_str = "str"
    type_class = getattr(builtins, type_str)
    try:
        return type_class(value)
    except ValueError:
        return value


# TODO: Re-organize this file to make it more readable and maintainable
def extract_system_prompt(prompts: list[dict]) -> str:
    for i, prompt in enumerate(prompts):
        if prompt["role"] == "system":
            system_prompt = prompt["content"]
            del prompts[i]
            return system_prompt
    return None


def extract_last_user_message(prompts: list[dict], user_role_name: str = "user") -> dict:
    for i in range(len(prompts) - 1, -1, -1):
        if prompts[i]["role"] == user_role_name:
            last_user_message = prompts[i]
            del prompts[i]
            return last_user_message
    return "User did not specify a query."


#### utils for multi-turn ####


def format_execution_results_prompting(
    inference_data: dict, execution_results: list[str], model_response_data: dict
) -> str:
    # Add the execution results to one single user message
    tool_results = []
    for execution_result, decoded_model_response in zip(
        execution_results, model_response_data["model_responses_decoded"]
    ):
        tool_results.append(
            {"role": "tool", "name": decoded_model_response, "content": execution_result}
        )

    return repr(tool_results)


def default_decode_ast_prompting(result, language="Python"):
    result = result.strip("`\n ")
    if not result.startswith("["):
        result = "[" + result
    if not result.endswith("]"):
        result = result + "]"
    decoded_output = ast_parse(result, language)
    return decoded_output


def default_decode_execute_prompting(result):
    result = result.strip("`\n ")
    if not result.startswith("["):
        result = "[" + result
    if not result.endswith("]"):
        result = result + "]"
    decoded_output = ast_parse(result)
    return decoded_output_to_execution_list(decoded_output)


def parse_nested_value(value):
    """
    Parse a potentially nested value from the AST output.

    Args:
        value: The value to parse, which could be a nested dictionary, which includes another function call, or a simple value.

    Returns:
        str: A string representation of the value, handling nested function calls and nested dictionary function arguments.
    """
    if isinstance(value, dict):
        # Check if the dictionary represents a function call (i.e., the value is another dictionary or complex structure)
        if all(isinstance(v, dict) for v in value.values()):
            func_name = list(value.keys())[0]
            args = value[func_name]
            args_str = ", ".join(f"{k}={parse_nested_value(v)}" for k, v in args.items())
            return f"{func_name}({args_str})"
        else:
            # If it's a simple dictionary, treat it as key-value pairs
            return (
                "{"
                + ", ".join(f"'{k}': {parse_nested_value(v)}" for k, v in value.items())
                + "}"
            )
    return repr(value)


def decoded_output_to_execution_list(decoded_output):
    """
    Convert decoded output to a list of executable function calls.

    Args:
        decoded_output (list): A list of dictionaries representing function calls.

    Returns:
        list: A list of strings, each representing an executable function call.
    """
    execution_list = []
    for function_call in decoded_output:
        for key, value in function_call.items():
            args_str = ", ".join(f"{k}={parse_nested_value(v)}" for k, v in value.items())
            execution_list.append(f"{key}({args_str})")
    return execution_list


def retry_with_backoff(
    error_type: Optional[Union[Type[Exception], List[Type[Exception]]]] = None,
    error_message_pattern: Optional[str] = None,
    min_wait: int = 6,
    max_wait: int = 120,
    **kwargs,
) -> Callable:
    """
    Decorator to retry a function with exponential backoff based on specified error types or result conditions.

    Note:
        At least one of `error_type` or `error_message_pattern` must be provided.
        If both `error_type` and `error_message_pattern` are provided, the retry will occur if either condition is met.

    Args:
        error_type ([Union[Type[Exception], List[Type[Exception]]]], optional): The exception type to retry on. Supports one exception, or a list of exceptions.
        error_message_pattern (str, optional):
            A regex pattern to match against the exception message to retry on.
            This is useful when the user wants to retry based on the exception message,
            especially if the exception raised is too broad.
        min_wait (int, optional): Minimum wait time in seconds for the backoff.
        max_wait (int, optional): Maximum wait time in seconds for the backoff.
        **kwargs: Additional keyword arguments for the `tenacity.retry` decorator, such as `stop`, `reraise`, etc.

    Returns:
        Callable: The decorated function with retry logic applied.
    """

    def decorator(func: Callable) -> Callable:
        # Collect retry conditions based on provided parameters
        conditions = []
        if error_type is not None:
            if isinstance(error_type, list):
                for et in error_type:
                    conditions.append(retry_if_exception_type(et))
            else:
                conditions.append(retry_if_exception_type(error_type))
        if error_message_pattern is not None:
            conditions.append(retry_if_exception_message(match=error_message_pattern))

        if not conditions:
            raise ValueError("Either error_type or retry_condition must be provided.")

        # Combine all conditions using logical OR
        retry_policy = reduce(operator.or_, conditions)

        @retry(
            wait=wait_random_exponential(min=min_wait, max=max_wait),
            retry=retry_policy,
            before_sleep=lambda retry_state: print(
                f"Attempt {retry_state.attempt_number} failed. "
                f"Sleeping for {retry_state.next_action.sleep:.2f} seconds before retrying... "
                f"Error: {retry_state.outcome.exception()}"
            ),
            **kwargs,
        )
        def wrapped(*args, **inner_kwargs):
            return func(*args, **inner_kwargs)

        return wrapped

    return decorator
