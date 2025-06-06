from typing import Any
import json
import random
import string

from bfcl.model_handler.local_inference.base_oss_handler import OSSHandler
from bfcl.model_handler.utils import (
    convert_to_function_call,
    func_doc_language_specific_pre_processing,
)
from overrides import override


class MistralFCHandler(OSSHandler):
    """
    Handler for Mistral function calling models that implements the OSSHandler interface. This class provides methods to format prompts, process responses, and handle function calls specifically for Mistral models.
    """
    def __init__(self, model_name: str, temperature: float) -> None:
        super().__init__(model_name, temperature)

    @override
    def decode_ast(self, result, language: str="Python") -> list[dict]:
        """
        Decodes the AST (Abstract Syntax Tree) from the model's output. For Mistral models, the output is already in the expected list of dictionaries format.
        
        Args:
            result (Any): The raw output from the model
            language (str, optional): The programming language of the output. Defaults to "Python".
        
        Returns:
            list[dict]: List of function call dictionaries in the format [{func1:{param1:val1,...}},{func2:{param2:val2,...}}]
        """
        # The input is already a list of dictionaries, so no need to decode
        # `[{func1:{param1:val1,...}},{func2:{param2:val2,...}}]`
        if type(result) != list:
            return []
        return result

    @override
    def decode_execute(self, result) -> list[dict]:
        """
        Converts the model's output into executable function calls.
        
        Args:
            result (Any): The raw output from the model
        
        Returns:
            list[dict]: List of executable function call dictionaries
        """
        if type(result) != list:
            return []
        return convert_to_function_call(result)

    @staticmethod
    def _construct_func_doc(functions: list[dict]) -> str:
        """
        {{- "[AVAILABLE_TOOLS][" }}
        {%- for tool in tools %}
            {%- set tool = tool.function %}
            {{- '{"type": "function", "function": {' }}
            {%- for key, val in tool.items() if key != "return" %}
                {%- if val is string %}
                    {{- '"' + key + '": "' + val + '"' }}
                {%- else %}
                    {{- '"' + key + '": ' + val|tojson }}
                {%- endif %}
                {%- if not loop.last %}
                    {{- ", " }}
                {%- endif %}
            {%- endfor %}
            {{- "}}" }}
            {%- if not loop.last %}
                {{- ", " }}
            {%- else %}
                {{- "]" }}
            {%- endif %}
        {%- endfor %}
        {{- "[/AVAILABLE_TOOLS]" }}
        """
        func_docs = []
        for tool in functions:
            func_doc = '{"type": "function", "function": {'
            func_doc += ", ".join(
                (
                    f'"{key}": "{val}"'
                    if isinstance(val, str)
                    else f'"{key}": {json.dumps(val)}'
                )
                for key, val in tool.items()
                if key != "return"
            )
            func_doc += "}}"
            func_docs.append(func_doc)

        result_str = "[AVAILABLE_TOOLS][" + ", ".join(func_docs) + "][/AVAILABLE_TOOLS]"
        return result_str

    @override
    def _format_prompt(self, messages: list[dict], function: list[dict]) -> str:
        """
        "bos_token": "<s>"
        "eos_token": "</s>"
        "chat_template":
        {%- if messages[0]["role"] == "system" %}
            {%- set system_message = messages[0]["content"] %}
            {%- set loop_messages = messages[1:] %}
        {%- else %}
            {%- set loop_messages = messages %}
        {%- endif %}
        {%- if not tools is defined %}
            {%- set tools = none %}
        {%- endif %}
        {%- set user_messages = loop_messages | selectattr("role", "equalto", "user") | list %}

        {#- This block checks for alternating user/assistant messages, skipping tool calling messages #}
        {%- set ns = namespace() %}
        {%- set ns.index = 0 %}
        {%- for message in loop_messages %}
            {%- if not (message.role == "tool" or message.role == "tool_results" or (message.tool_calls is defined and message.tool_calls is not none)) %}
                {%- if (message["role"] == "user") != (ns.index % 2 == 0) %}
                    {{- raise_exception("After the optional system message, conversation roles must alternate user/assistant/user/assistant/...") }}
                {%- endif %}
                {%- set ns.index = ns.index + 1 %}
            {%- endif %}
        {%- endfor %}

        {{- bos_token }}
        {%- for message in loop_messages %}
            {%- if message["role"] == "user" %}
                {%- if tools is not none and (message == user_messages[-1]) %}
                    {{- "[AVAILABLE_TOOLS][" }}
                    {%- for tool in tools %}
                        {%- set tool = tool.function %}
                        {{- '{"type": "function", "function": {' }}
                        {%- for key, val in tool.items() if key != "return" %}
                            {%- if val is string %}
                                {{- '"' + key + '": "' + val + '"' }}
                            {%- else %}
                                {{- '"' + key + '": ' + val|tojson }}
                            {%- endif %}
                            {%- if not loop.last %}
                                {{- ", " }}
                            {%- endif %}
                        {%- endfor %}
                        {{- "}}" }}
                        {%- if not loop.last %}
                            {{- ", " }}
                        {%- else %}
                            {{- "]" }}
                        {%- endif %}
                    {%- endfor %}
                    {{- "[/AVAILABLE_TOOLS]" }}
                    {%- endif %}
                {%- if loop.last and system_message is defined %}
                    {{- "[INST]" + system_message + "\n\n" + message["content"] + "[/INST]" }}
                {%- else %}
                    {{- "[INST]" + message["content"] + "[/INST]" }}
                {%- endif %}
            {%- elif (message.tool_calls is defined and message.tool_calls is not none) %}
                {{- "[TOOL_CALLS][" }}
                {%- for tool_call in message.tool_calls %}
                    {%- set out = tool_call.function|tojson %}
                    {{- out[:-1] }}
                    {%- if not tool_call.id is defined or tool_call.id|length != 9 %}
                        {{- raise_exception("Tool call IDs should be alphanumeric strings with length 9!") }}
                    {%- endif %}
                    {{- ', "id": "' + tool_call.id + '"}' }}
                    {%- if not loop.last %}
                        {{- ", " }}
                    {%- else %}
                        {{- "]" + eos_token }}
                    {%- endif %}
                {%- endfor %}
            {%- elif message["role"] == "assistant" %}
                {{- message["content"] + eos_token}}
            {%- elif message["role"] == "tool_results" or message["role"] == "tool" %}
                {%- if message.content is defined and message.content.content is defined %}
                    {%- set content = message.content.content %}
                {%- else %}
                    {%- set content = message.content %}
                {%- endif %}
                {{- '[TOOL_RESULTS]{"content": ' + content|string + ", " }}
                {%- if not message.tool_call_id is defined or message.tool_call_id|length != 9 %}
                    {{- raise_exception("Tool call IDs should be alphanumeric strings with length 9!") }}
                {%- endif %}
                {{- '"call_id": "' + message.tool_call_id + '"}[/TOOL_RESULTS]' }}
            {%- else %}
                {{- raise_exception("Only user and assistant roles are supported, with the exception of an initial optional system message!") }}
            {%- endif %}
        {%- endfor %}
        """
        bos_token = "<s>"
        eos_token = "</s>"

        formatted_prompt = bos_token

        # Handle optional system message
        first_message = messages[0]
        if first_message["role"] == "system":
            system_message = first_message["content"]
            loop_messages = messages[1:]
        else:
            system_message = None
            loop_messages = messages

        # Extract user messages for later reference
        user_messages = [msg for msg in loop_messages if msg["role"] == "user"]

        for idx, message in enumerate(loop_messages):
            role = message["role"]

            if role == "user":
                # If this is the last user message and tools are provided, append AVAILABLE_TOOLS
                if len(function) > 0 and message == user_messages[-1]:
                    formatted_prompt += self._construct_func_doc(function)

                # If it's the last message and there's a system message, include it
                if idx == len(loop_messages) - 1 and system_message:
                    formatted_prompt += (
                        f"[INST]{system_message}\n\n{message['content']}[/INST]"
                    )
                else:
                    formatted_prompt += f"[INST]{message['content']}[/INST]"

            elif role == "assistant":
                # There is no need to further special handle the tool calls messages
                # They are already correctly formatted in the `_parse_query_response_prompting` method, including the tool call id and the `[TOOL_CALLS]` tag
                formatted_prompt += f"{message['content']}{eos_token}"

            elif role == "tool":
                tool_results = {
                    "content": message["content"],
                    "call_id": message["tool_call_id"],
                }
                formatted_prompt += (
                    f"[TOOL_RESULTS]{json.dumps(tool_results)}[/TOOL_RESULTS]"
                )

        formatted_prompt += eos_token
        return formatted_prompt

    @override
    def _pre_query_processing_prompting(self, test_entry: dict) -> dict:
        """
        Pre-processes the test entry before querying the model. Performs language-specific processing on functions.
        
        Args:
            test_entry (dict): The test case containing functions to process
        
        Returns:
            dict: Processed test entry with messages and functions
        """
        functions: list = test_entry["function"]
        test_category: str = test_entry["id"].rsplit("_", 1)[0]

        functions = func_doc_language_specific_pre_processing(functions, test_category)
        # We don't add system prompt

        return {"message": [], "function": functions}

    @override
    def _add_execution_results_prompting(
        self, inference_data: dict, execution_results: list[str], model_response_data: dict
    ) -> dict:
        """
        Adds execution results to the inference data for subsequent model calls.
        
        Args:
            inference_data (dict): Current inference state
            execution_results (list[str]): Results from executing the function calls
            model_response_data (dict): Data from the model's response
        
        Returns:
            dict: Updated inference data with execution results
        """
        for execution_result, tool_call_id in zip(
            execution_results, model_response_data["tool_call_ids"]
        ):
            inference_data["message"].append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": execution_result,
                }
            )

        return inference_data

    @staticmethod
    def generate_random_string() -> str:
        """Generates a random string of alphanumeric characters of length 9."""
        characters = string.ascii_letters + string.digits
        random_string = "".join(random.choices(characters, k=9))
        return random_string

    @override
    def _parse_query_response_prompting(self, api_response: any) -> dict:
        """
        Parses the model's response into function calls and generates required tool call IDs.
        
        Args:
            api_response (any): Raw response from the model API
        
        Returns:
            dict: Parsed response containing model responses, chat history message, tool call IDs, and token counts
        """
        model_responses = api_response.choices[0].text
        tool_call_ids = []
        """
        Mistral models require a tool_call_id, which should be 9 randomly-generated alphanumeric characters, and assigned to the id key of the tool call dictionary.
        Source: https://huggingface.co/docs/transformers/main/chat_templating#advanced-tool-use--function-calling
        
        "[{\"name\": \"math.factorial\", \"arguments\": {\"number\": 5}}, {\"name\": \"math.factorial\", \"arguments\": {\"number\": 10}}, {\"name\": \"math.factorial\", \"arguments\": {\"number\": 15}}]"
        """
        try:
            model_responses = json.loads(model_responses)
            for model_response in model_responses:
                tool_call_id = self.generate_random_string()
                model_response["id"] = tool_call_id
                tool_call_ids.append(tool_call_id)

            # We prepare the model responses here because it's easier to do it here than in the `_format_prompt` method
            # The `[TOOL_CALLS]` tag is added here, as required by the chat template
            model_responses_message_for_chat_history = (
                f"[TOOL_CALLS]{json.dumps(model_responses)}"
            )

            model_responses = [
                {item["name"]: item["arguments"]} for item in model_responses
            ]
        except json.JSONDecodeError:
            model_responses_message_for_chat_history = model_responses

        return {
            "model_responses": model_responses,
            "model_responses_message_for_chat_history": model_responses_message_for_chat_history,
            "tool_call_ids": tool_call_ids,
            "input_token": api_response.usage.prompt_tokens,
            "output_token": api_response.usage.completion_tokens,
        }

    @override
    def _add_assistant_message_prompting(
        self, inference_data: dict, model_response_data: dict
    ) -> dict:
        """
        Adds the assistant's response message to the inference data.
        
        Args:
            inference_data (dict): Current inference state
            model_response_data (dict): Data from the model's response
        
        Returns:
            dict: Updated inference data with assistant message
        """
        inference_data["message"].append(
            {
                "role": "assistant",
                "content": model_response_data["model_responses_message_for_chat_history"],
            }
        )
        return inference_data
