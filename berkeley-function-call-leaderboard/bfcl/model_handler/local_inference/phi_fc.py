import json
import re

from bfcl.model_handler.local_inference.base_oss_handler import OSSHandler
from bfcl.model_handler.utils import (
    convert_to_function_call,
    func_doc_language_specific_pre_processing,
)
from overrides import override


class PhiFCHandler(OSSHandler):
    """
    This class implements a function-calling handler for the Microsoft Phi series of models.

    Specifically, this handler currently supports the following models:
    - microsoft/Phi-4-mini-instruct
    """

    def __init__(self, model_name, temperature) -> None:
        super().__init__(model_name, temperature)
        # Strip the -FC suffix when initializing the actual model
        if model_name.endswith("-FC"):
            self.model_name_huggingface = model_name[:-3]
        else:
            self.model_name_huggingface = model_name

        # Store the original model name for reference
        self.original_model_name = model_name
        self.is_fc_model = True

    @override
    def _format_prompt(self, messages, function):
        """
        "bos_token": "<|endoftext|>",
        "chat_template":
        {% for message in messages %}
          {% if message['role'] == 'system' and 'tools' in message and message['tools'] is not none %}
            {{ '<|' + message['role'] + '|>' + message['content'] + '<|tool|>' + message['tools'] + '<|/tool|>' + '<|end|>' }}
          {% else %}
            {{ '<|' + message['role'] + '|>' + message['content'] + '<|end|>' }}
          {% endif %}
        {% endfor %}
        {% if add_generation_prompt %}
          {{ '<|assistant|>' }}
        {% else %}
          {{ eos_token }}
        {% endif %}
        """

        # Here's Microsoft's documentation on how the Phi-4-mini-instruct model expects tools to be provided to it:
        # Tool-enabled function-calling format
        #
        # # Tools
        # This format is used when the user wants the model to provide function calls based on the given tools.
        # The user should provide the available tools in the system prompt, wrapped by <|tool|> and <|/tool|> tokens.
        # The tools should be specified in JSON format, using a JSON dump structure. Example:
        #
        # <|system|>You are a helpful assistant with some tools.<|tool|>[{"name": "get_weather_updates", "description": "Fetches weather updates for a given city using the RapidAPI Weather API.", "parameters": {"city": {"description": "The name of the city for which to retrieve weather information.", "type": "str", "default": "London"}}}]<|/tool|><|end|><|user|>What is the weather like in Paris today?<|end|><|assistant|>
        #

        # sanity check
        system_messages = [msg for msg in messages if msg["role"] == "system"]
        assert 0 <= len(system_messages) <= 1

        # set the system message
        system_message = "You are a helpful assistant with some tools."
        if messages[0]["role"] == "system":
            system_message = messages[0]["content"]
            messages = messages[1:]

        # extract the tool contents
        tool_contents = ""
        for func in function:
            # microsoft documentation has no guidance on indentation
            tool_contents += json.dumps(func)
            tool_contents += "\n"

        # format the rest of the prompt
        formatted_prompt = (
            f"<|system|>{system_message}<|tool|>{tool_contents}<|/tool|><|end|>"
        )
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            formatted_prompt += f"<|{role}|>{content}<|end|>"

        # provide the generation prompt token
        formatted_prompt += "<|assistant|>"
        return formatted_prompt

    @override
    def decode_ast(self, result, language="Python"):
        if not isinstance(result, list) or any(
            not isinstance(item, dict) for item in result
        ):
            return []

        return result

    @override
    def decode_execute(self, result):
        if type(result) != list or any(type(item) != dict for item in result):
            return []
        return convert_to_function_call(result)

    @override
    def _pre_query_processing_prompting(self, test_entry: dict) -> dict:
        """
        Formats a sample from the dataset into a format usable by the testing suite.

        Args:
            test_entry (dict): Sample from the
        """
        functions: list = test_entry["function"]
        test_category: str = test_entry["id"].rsplit("_", 1)[0]

        functions = func_doc_language_specific_pre_processing(functions, test_category)
        # FC models use its own system prompt, so no need to add any message

        return {"message": [], "function": functions}

    @override
    def _parse_query_response_prompting(self, api_response: any) -> dict:
        """
        Parses the raw response from the model API to extract the result, input token count, and output token count.

        Args:
            api_response (any): The raw response from the model API.

        Returns:
            A dict containing the following elements:
                - model_responses (any): The parsed result that can be directly used as input to the decode method.
                - input_token (int): The number of tokens used in the input to the model.
                - output_token (int): The number of tokens generated by the model as output.
                - Any other metadata that is specific to the model.
        """
        model_responses = api_response.choices[0].text
        extracted_tool_calls = self._extract_tool_calls(model_responses)
        extracted_tool_calls = self._parse_extracted_tool_calls(extracted_tool_calls)

        if len(extracted_tool_calls) > 0:
            model_responses_message_for_chat_history = {
                "role": "assistant",
                "content": None,
                "tool_calls": extracted_tool_calls,
            }
            model_responses = [
                {item["name"]: item["arguments"]} for item in extracted_tool_calls
            ]
        else:
            model_responses_message_for_chat_history = {
                "role": "assistant",
                "content": model_responses,
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
        """
        Add assistant message to the chat history.
        """
        inference_data["message"].append(
            model_response_data["model_responses_message_for_chat_history"],
        )
        return inference_data

    @staticmethod
    def _parse_extracted_tool_calls(tool_calls: list[any]) -> list[dict]:
        """
        Given a list of tool calls, we want to flatten it into one uniform list
        """
        # first we transform into a single list
        flattened = []
        for tc in tool_calls:
            flattened.extend(tc)

        extracted_tool_calls = []
        for fc in flattened:
            # from the Qwen FC implementation:
            # Handle the situation: ['{"name": "random_forest.train", "arguments": {"n_estimators": 100, "max_depth": 5, "data": my_data}}']
            if isinstance(fc, str):
                try:
                    fc = json.loads(fc)
                except json.JSONDecodeError:
                    continue

            # Phi-4-mini-insruct likes to return all its tool calls within a single `<|tool_cal|>...<|/tool_call|>` invocation
            # this handles that case by extending out the list when possible.
            if isinstance(fc, dict):
                extracted_tool_calls.append(fc)
            if isinstance(fc, list):
                extracted_tool_calls.extend(fc)
        return extracted_tool_calls

    @staticmethod
    def _extract_tool_calls(input_string: str) -> list[any]:
        """
        Given some input response, attempt to parse out the tool calls made by the model.

        Args:
            input_string (str): The model response

        Returns:
            (list) The matched objects that we were able to parse out
        """
        pattern = r"<\|tool_call\|>(.*?)<\|/tool_call\|>"
        matches = re.findall(pattern, input_string, re.DOTALL)

        # Process matches into a list of dictionaries
        result = []
        for match in matches:
            try:
                match = json.loads(match)
            except json.JSONDecodeError:
                pass

            result.append(match)

        return result
