from typing import Union
import json

from bfcl_eval.model_handler.local_inference.base_oss_handler import OSSHandler
from overrides import override


class ThinkAgentHandler(OSSHandler):
    """
    A handler class for the ThinkAgent model that extends OSSHandler. This class provides methods to format prompts, convert function formats, extract JSON from text, and decode model outputs into AST and executable formats.
    """
    def __init__(self, model_name: str, temperature: float) -> None:
        super().__init__(model_name, temperature)

    def _convert_functions_format(self, functions: Union[dict, list]) -> Union[dict, list]:
        """
        Converts function definitions into a standardized format for the ThinkAgent model.
        
        Args:
            functions (Union[dict, list]): The function definitions to convert. Can be a single function (dict) or list of functions.
        
        Returns:
            Union[dict, list]: The converted function(s) in ThinkAgent format with name, description, and parameters.
        """
        if isinstance(functions, dict):
            return {
                "name": functions["name"],
                "description": functions["description"],
                "parameters": {
                    k: v for k, v in functions["parameters"].get("properties", {}).items()
                },
            }
        elif isinstance(functions, list):
            return [self._convert_functions_format(f) for f in functions]
        else:
            return functions

    def _extract_json_from_text(self, text: str) -> str:
        """
        Extracts JSON content from model output text by splitting at the closing </think> tag.
        
        Args:
            text (str): The model output text containing JSON.
        
        Returns:
            str: The extracted JSON string, or empty array string if no </think> tag found.
        """
        # Split the text at the closing </think> tag and take the part after it
        split_text = text.split("</think>", 1)

        # If the split was successful (there was a </think> tag), process the second part
        if len(split_text) > 1:
            # Strip whitespace from the remaining text to isolate the JSON
            json_str = split_text[1].strip()
        else:
            # Return empty string if no </think> tag found
            json_str = "[]"

        return json_str

    @override
    def _format_prompt(self, messages: list[dict[str, str]], function: dict) -> str:
        # Think agent is doing the tools_in_user_message approach
        """
        {{- bos_token }}
        {%- if custom_tools is defined %}
            {%- set tools = custom_tools %}
        {%- endif %}
        {%- if not tools_in_user_message is defined %}
            {%- set tools_in_user_message = true %}
        {%- endif %}
        {%- if not date_string is defined %}
            {%- if strftime_now is defined %}
                {%- set date_string = strftime_now("%d %b %Y") %}
            {%- else %}
                {%- set date_string = "07 Dec 2024" %}
            {%- endif %}
        {%- endif %}
        {%- if not tools is defined %}
            {%- set tools = [] %}
        {%- endif %}
        {#- System message #}
        {{- "<|start_header_id|>system<|end_header_id|>" }}
        {{- "Cutting Knowledge Date: December 2023" }}
        {{- "Today Date: " + date_string + "" }}
        {%- if tools is not none and not tools_in_user_message %}
            {{- "Given the following functions, please respond with a JSON for a function call with its proper arguments that best answers the given prompt." }}
            {{- 'Respond in the format {"name": function name, "parameters": dictionary of argument name and its value}.' }}
            {{- "Do not use variables." }}
            {{- "Available tools:" }}
            {{- tools | tojson(indent=4) }}
        {%- endif %}
        {{- system_message }}
        {{- "<|eot_id|>" }}
        {%- if tools_in_user_message and tools|length > 0 %}
            {%- if messages | length != 0 %}
                {%- set first_user_message = messages[0]['content']|trim %}
                {%- set messages = messages[1:] %}
            {%- else %}
                {{- raise_exception("Cannot put tools in the first user message when there's no first user message!") }}
        {%- endif %}
            {{- '<|start_header_id|>user<|end_header_id|>' }}
            {{- "Given the following functions, please respond with a JSON for a function call with its proper arguments that best answers the given prompt." }}
            {{- 'Respond in the format {"name": function name, "parameters": dictionary of argument name and its value}.' }}
            {{- "Do not use variables." }}
            {{- "Available tools:" }}
            {{- tools | tojson(indent=4) }}
            {{- first_user_message + "<|eot_id|>"}}
        {%- endif %}
        {%- for message in messages %}
            {%- if not (message.role == 'tool' or 'tool_calls' in message) %}
                {{- '<|start_header_id|>' + message['role'] + '<|end_header_id|>' + message['content'] | trim + '<|eot_id|>' }}
            {%- elif 'tool_calls' in message %}
                {%- if not message.tool_calls|length == 1 %}
                    {{- raise_exception("This model only supports single tool-calls at once!") }}
                {%- endif %}
                {%- set tool_call = message.tool_calls[0].function %}
                {{- '<|start_header_id|>assistant<|end_header_id|>' }}
                {{- '{"name": "' + tool_call.name + '", ' }}
                {{- '"parameters": ' }}
                {{- tool_call.arguments | tojson }}
                {{- "}" }}
                {{- "<|eot_id|>" }}
            {%- endif %}
        {%- endfor %}
        {%- if add_generation_prompt %}
            {{- '<|start_header_id|>assistant<|end_header_id|>' }}
        {%- endif %}
        """
        # We first format the function signature and then add the messages
        tools = self._convert_functions_format(function)

        formatted_prompt = "<|begin_of_text|>"

        remaining_messages = messages
        if messages[0]["role"] == "system":
            remaining_messages = messages[1:]

        formatted_prompt += "<|start_header_id|>system<|end_header_id|>"
        formatted_prompt += "Cutting Knowledge Date: December 2023"
        formatted_prompt += "Today Date: 07 Dec 2024"
        formatted_prompt += "<|eot_id|>"

        if len(remaining_messages) > 0:
            formatted_prompt += "<|start_header_id|>user<|end_header_id|>"
            formatted_prompt += "Given the following functions, please respond with a JSON for a function call with its proper arguments that best answers the given prompt."
            formatted_prompt += 'Respond in the format {"name": function name, "parameters": dictionary of argument name and its value}.'
            formatted_prompt += "Do not use variables."
            formatted_prompt += "Available tools:"
            formatted_prompt += f"{tools}"
            formatted_prompt += remaining_messages[0]["content"].strip()
            formatted_prompt += "<|eot_id|>"

        formatted_prompt += "<|start_header_id|>assistant<|end_header_id|>"

        return formatted_prompt

    @override
    def decode_ast(self, result: str, language: str="Python") -> list[dict[str, dict]]:
        """
        Decodes model output into an abstract syntax tree (AST) representation of function calls.
        
        Args:
            result (str): The raw model output text.
            language (str, optional): The programming language of the output. Defaults to "Python".
        
        Returns:
            list[dict[str, dict]]: List of function calls where each dict contains function name and arguments.
        """
        # The output is a list of dictionaries, where each dictionary contains the function name and its arguments
        result = result.strip()
        result = result.replace("'", '"')  # replace single quotes with double quotes
        result = self._extract_json_from_text(result)
        result = json.loads(result)

        func_calls = []
        for item in result:
            function_name = item["name"]
            arguments = item["arguments"]
            func_calls.append({function_name: arguments})

        return func_calls

    @override
    def decode_execute(self, result: str) -> list[str]:
        """
        Decodes model output into executable function call strings.
        
        Args:
            result (str): The raw model output text.
        
        Returns:
            list[str]: List of executable function call strings in format 'function_name(arguments)'.
        """
        # The output is a list of dictionaries, where each dictionary contains the function name and its arguments
        result = result.strip()
        result = result.replace("'", '"')  # replace single quotes with double quotes
        result = self._extract_json_from_text(result)
        result = json.loads(result)

        # put the functions in format function_name(arguments)
        function_call_list = []
        for item in result:
            function_name = item["name"]
            arguments = item["arguments"]
            function_call_list.append(f"{function_name}({arguments})")

        execution_list = []
        for function_call in function_call_list:
            for key, value in function_call.items():
                execution_list.append(
                    f"{key}({','.join([f'{k}={repr(v)}' for k,v in value.items()])})"
                )
        return execution_list