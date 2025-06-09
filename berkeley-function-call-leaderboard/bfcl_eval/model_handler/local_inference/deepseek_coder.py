import json
import re

from bfcl_eval.model_handler.local_inference.base_oss_handler import OSSHandler
from bfcl_eval.model_handler.utils import (
    combine_consecutive_user_prompts,
    convert_system_prompt_into_user_prompt,
    convert_to_function_call,
    func_doc_language_specific_pre_processing,
)
from overrides import override


class DeepseekCoderHandler(OSSHandler):
    """
    This is the handler for the Deepseek-Coder models. Models are benchmarked in their Function Calling mode.
    """

    def __init__(self, model_name, temperature) -> None:
        super().__init__(model_name, temperature)

    @override
    def decode_ast(self, result, language="Python"):
        # The input is already a list of dictionaries, so no need to decode
        # `[{func1:{param1:val1,...}},{func2:{param2:val2,...}}]`
        if type(result) != list:
            return []
        return result

    @override
    def decode_execute(self, result):
        if type(result) != list:
            return []
        return convert_to_function_call(result)

    @override
    def _format_prompt(self, messages, function):
        """
        "bos_token": {
            "__type": "AddedToken",
            "content": "<｜begin▁of▁sentence｜>",
            "lstrip": false,
            "normalized": true,
            "rstrip": false,
            "single_word": false
        },
        "chat_template": "{% if not add_generation_prompt is defined %}{% set add_generation_prompt = false %}{% endif %}{% set ns = namespace(is_first=false, is_tool=false, is_output_first=true, system_prompt='') %}{%- for message in messages %}    {%- if message['role'] == 'system' %}        {% set ns.system_prompt = message['content'] %}    {%- endif %}{%- endfor %}{{bos_token}}{{ns.system_prompt}}{%- for message in messages %}    {%- if message['role'] == 'user' %}    {%- set ns.is_tool = false -%}{{'<｜User｜>' + message['content']}}    {%- endif %}    {%- if message['role'] == 'assistant' and message['content'] is none %}        {%- set ns.is_tool = false -%}        {%- for tool in message['tool_calls']%}            {%- if not ns.is_first %}{{'<｜Assistant｜><｜tool▁calls▁begin｜><｜tool▁call▁begin｜>' + tool['type'] + '<｜tool▁sep｜>' + tool['function']['name'] + '\\n' + '```json' + '\\n' + tool['function']['arguments'] + '\\n' + '```' + '<｜tool▁call▁end｜>'}}            {%- set ns.is_first = true -%}            {%- else %}{{'\\n' + '<｜tool▁call▁begin｜>' + tool['type'] + '<｜tool▁sep｜>' + tool['function']['name'] + '\\n' + '```json' + '\\n' + tool['function']['arguments'] + '\\n' + '```' + '<｜tool▁call▁end｜>'}}{{'<｜tool▁calls▁end｜><｜end▁of▁sentence｜>'}}                   {%- endif %}        {%- endfor %}    {%- endif %}    {%- if message['role'] == 'assistant' and message['content'] is not none %}        {%- if ns.is_tool %}{{'<｜tool▁outputs▁end｜>' + message['content'] + '<｜end▁of▁sentence｜>'}}        {%- set ns.is_tool = false -%}        {%- else %}{{'<｜Assistant｜>' + message['content'] + '<｜end▁of▁sentence｜>'}}        {%- endif %}    {%- endif %}    {%- if message['role'] == 'tool' %}        {%- set ns.is_tool = true -%}        {%- if ns.is_output_first %}{{'<｜tool▁outputs▁begin｜><｜tool▁output▁begin｜>' + message['content'] + '<｜tool▁output▁end｜>'}}        {%- set ns.is_output_first = false %}        {%- else %}{{'\\n<｜tool▁output▁begin｜>' + message['content'] + '<｜tool▁output▁end｜>'}}        {%- endif %}    {%- endif %}{%- endfor -%}{% if ns.is_tool %}{{'<｜tool▁outputs▁end｜>'}}{% endif %}{% if add_generation_prompt and not ns.is_tool %}{{'<｜Assistant｜>'}}{% endif %}"
        """
        formatted_prompt = "<｜begin▁of▁sentence｜>"

        is_first_tool_call = True
        is_output_first = True
        is_tool = False

        # Extract the system prompt
        for message in messages:
            if message["role"] == "system":
                formatted_prompt += message["content"]
                break

        for message in messages:
            if message["role"] == "user":
                is_tool = False
                formatted_prompt += f"<｜User｜>{message['content']}"

            elif message["role"] == "assistant" and message["content"] is None:
                is_tool = False
                formatted_prompt += "<｜Assistant｜><｜tool▁calls▁begin｜>"
                for tool_call in message["tool_calls"]:
                    tool_call_template = (
                        "<｜tool▁call▁begin｜>{type}<｜tool▁sep｜>{name}\\n"
                        "```json\\n{arguments}\\n```<｜tool▁call▁end｜>"
                    )
                    tool_call_formatted = tool_call_template.format(
                        type=tool_call["type"],
                        name=tool_call["function"]["name"],
                        arguments=tool_call["function"]["arguments"],
                    )
                    if not is_first_tool_call:
                        formatted_prompt += f"\\n{tool_call_formatted}"
                    else:
                        formatted_prompt += tool_call_formatted
                        is_first_tool_call = False
                formatted_prompt += "<｜tool▁calls▁end｜><｜end▁of▁sentence｜>"

            elif message["role"] == "assistant" and message["content"] is not None:
                if is_tool:
                    formatted_prompt += (
                        f"<｜tool▁outputs▁end｜>{message['content']}<｜end▁of▁sentence｜>"
                    )
                    is_tool = False
                else:
                    formatted_prompt += (
                        f"<｜Assistant｜>{message['content']}<｜end▁of▁sentence｜>"
                    )

            elif message["role"] == "tool":
                is_tool = True
                tool_output_template = (
                    "<｜tool▁output▁begin｜>{content}<｜tool▁output▁end｜>"
                )
                if is_output_first:
                    formatted_prompt += f"<｜tool▁outputs▁begin｜>{tool_output_template.format(content=message['content'])}"
                    is_output_first = False
                else:
                    formatted_prompt += (
                        f"\\n{tool_output_template.format(content=message['content'])}"
                    )

        if is_tool:
            formatted_prompt += "<｜tool▁outputs▁end｜>"

        if not is_tool:
            formatted_prompt += "<｜Assistant｜>"

        return formatted_prompt

    @override
    def _pre_query_processing_prompting(self, test_entry: dict) -> dict:
        functions: list = test_entry["function"]
        test_category: str = test_entry["id"].rsplit("_", 1)[0]

        functions = func_doc_language_specific_pre_processing(functions, test_category)

        # Deepseek coder use its own system prompt
        for round_idx in range(len(test_entry["question"])):
            test_entry["question"][round_idx] = convert_system_prompt_into_user_prompt(
                test_entry["question"][round_idx]
            )
            test_entry["question"][round_idx] = combine_consecutive_user_prompts(
                test_entry["question"][round_idx]
            )

        tool_system_prompt = "You are a helpful Assistant.\n\n## Tools\n\n### Function\n\nYou have the following functions available:\n\n"
        for function in functions:
            tool_system_prompt += f"- `{function['name']}`:\n"
            tool_system_prompt += f"```json\n{json.dumps(function, indent=4)}\n```\n"

        test_entry["question"][0].insert(
            0, {"role": "system", "content": tool_system_prompt}
        )

        return {"message": [], "function": functions}

    @override
    def _parse_query_response_prompting(self, api_response: any) -> dict:
        model_responses = api_response.choices[0].text
        extracted_tool_calls = self.extract_tool_calls(model_responses)

        if len(extracted_tool_calls) > 0:
            model_responses_message_for_chat_history = {
                "role": "assistant",
                "content": None,
                "tool_calls": extracted_tool_calls,
            }
            model_responses = [
                {item["function"]["name"]: item["function"]["arguments"]}
                for item in extracted_tool_calls
            ]
        else:
            model_responses_message_for_chat_history = {
                "role": "assistant",
                "content": api_response.choices[0].text,
            }

        return {
            "model_responses": model_responses,
            "model_responses_message_for_chat_history": model_responses_message_for_chat_history,
            "input_token": api_response.usage.prompt_tokens,
            "output_token": api_response.usage.completion_tokens,
        }

    @override
    def _add_assistant_message_prompting(
        self, inference_data: dict, model_response_data: dict
    ) -> dict:
        inference_data["message"].append(
            model_response_data["model_responses_message_for_chat_history"],
        )
        return inference_data

    @staticmethod
    def extract_tool_calls(input_string):
        """
        Input is like this:
        "<｜tool▁calls▁begin｜><｜tool▁call▁begin｜>function<｜tool▁sep｜>calculate_cosine.similarity
        ```json
        {"vectorA": [0.5, 0.7, 0.2, 0.9, 0.1], "vectorB": [0.3, 0.6, 0.2, 0.8, 0.1]}
        ```<｜tool▁call▁end｜>
        <｜tool▁call▁begin｜>function<｜tool▁sep｜>calculate_cosine_similarity
        ```json
        {"vectorA": [0.2, 0.4, 0.6, 0.8, 1.0], "vectorB": [1.0, 0.8, 0.6, 0.4, 0.2]}
        ```<｜tool▁call▁end｜>
        <｜tool▁call▁begin｜>function<｜tool▁sep｜>calculate_cosine_similarity
        ```json
        {"vectorA": [0.1, 0.2, 0.3, 0.4, 0.5], "vectorB": [0.5, 0.4, 0.3, 0.2, 0.1]}
        ```<｜tool▁call▁end｜><｜tool▁calls▁end｜>"

        We want to extract the tool calls from this string.
        Expected output:
        [{'type': 'function', 'name': 'calculate_cosine.similarity', 'argument': {'vectorA': [0.5, 0.7, 0.2, 0.9, 0.1], 'vectorB': [0.3, 0.6, 0.2, 0.8, 0.1]}}, {'type': 'function', 'name': 'calculate_cosine_similarity', 'argument': {'vectorA': [0.2, 0.4, 0.6, 0.8, 1.0], 'vectorB': [1.0, 0.8, 0.6, 0.4, 0.2]}}, {'type': 'function', 'name': 'calculate_cosine_similarity', 'argument': {'vectorA': [0.1, 0.2, 0.3, 0.4, 0.5], 'vectorB': [0.5, 0.4, 0.3, 0.2, 0.1]}}]
        """
        # Regular expression to match tool calls
        pattern = re.compile(
            r"<｜tool▁call▁begin｜>(\w+)<｜tool▁sep｜>(.*?)(?:\n|\\n)```json(?:\n|\\n)(.*?)(?:\n|\\n)```<｜tool▁call▁end｜>"
        )

        # Find all matches in the input string
        matches = pattern.findall(input_string)

        # Process matches into a list of dictionaries
        result = []
        for match in matches:
            type = match[0]
            name = match[1]
            argument = match[2]
            try:
                argument = json.loads(argument)
            except Exception as e:
                pass
            result.append({"type": type, "function": {"name": name, "arguments": argument}})
        return result
