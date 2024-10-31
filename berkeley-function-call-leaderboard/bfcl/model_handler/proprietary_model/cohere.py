import os
import time

import cohere
from bfcl.model_handler.base_handler import BaseHandler
from bfcl.model_handler.constant import GORILLA_TO_PYTHON
from bfcl.model_handler.model_style import ModelStyle
from bfcl.model_handler.utils import (
    ast_parse,
    convert_system_prompt_into_user_prompt,
    convert_to_tool,
    extract_last_user_message,
    extract_system_prompt,
    func_doc_language_specific_pre_processing,
    system_prompt_pre_processing_chat_model,
    format_execution_results_prompting,
)

USE_COHERE_OPTIMIZATION = os.getenv("USE_COHERE_OPTIMIZATION") == "True"


class CohereHandler(BaseHandler):
    client: cohere.Client

    def __init__(self, model_name, temperature) -> None:
        super().__init__(model_name, temperature)
        self.model_style = ModelStyle.COHERE
        self.client = cohere.Client(api_key=os.getenv("COHERE_API_KEY"))

        # System prompt for function calling.
        if USE_COHERE_OPTIMIZATION:
            self.preamble = """## Task & Context
    You help people answer their questions and other requests interactively. You will be asked a very wide array of requests on all kinds of topics. You will be equipped with a wide range of search engines or similar tools to help you, which you can use to research your answer. You should focus on serving the user's needs as best you can, which will be wide-ranging.

    When a question is irrelevant or unrelated to the available tools you should choose to directly answer. This is especially important when the question or available tools are about specialist subject like math or biology or physics: DO NOT ANSWER UNRELATED QUESTIONS.

    ## Style Guide
    Unless the user asks for a different style of answer, you should answer in full sentences, using proper grammar and spelling.
    """
        else:
            self.preamble = """
        ## Task & Context
        You help people answer their questions and other requests interactively. You will be asked a very wide array of requests on all kinds of topics. You will be equipped with a wide range of search engines or similar tools to help you, which you use to research your answer. You should focus on serving the user's needs as best you can, which will be wide-ranging.

        ## Style Guide
        Unless the user asks for a different style of answer, you should answer in full sentences, using proper grammar and spelling.
        """

    @staticmethod
    def _substitute_prompt_role(prompts: list[dict]) -> list[dict]:
        # Cohere use CHATBOT, USER, SYSTEM, TOOL as roles
        for prompt in prompts:
            if prompt["role"] == "user":
                prompt["role"] = "USER"
            elif prompt["role"] == "assistant":
                prompt["role"] = "CHATBOT"
            elif prompt["role"] == "system":
                prompt["role"] = "SYSTEM"
            elif prompt["role"] == "tool":
                prompt["role"] = "TOOL"
        return prompts

    @staticmethod
    def _substitute_content_name(prompts: list[dict]) -> list[dict]:
        for prompt in prompts:
            prompt["message"] = prompt["content"]
            del prompt["content"]
        return prompts

    def decode_ast(self, result, language="Python"):
        if "FC" not in self.model_name:
            if not result.startswith("["):
                result = "[" + result
            if not result.endswith("]"):
                result = result + "]"
            decoded_output = ast_parse(result, language)
        else:
            decoded_output = []
            for invoked_function in result:
                name = list(invoked_function.keys())[0]
                params = invoked_function[name]
                if language == "Python":
                    pass
                else:
                    if USE_COHERE_OPTIMIZATION:
                        # all values of the json are cast to string for java and javascript
                        for key, value in params.items():
                            value = str(value)
                            # Booleans are converted from JSON -> Python, and then turned into a string.
                            # Use e.g. 'true' instead of the Python 'True'.
                            if isinstance(params[key], bool):
                                value = value.lower()
                            params[key] = value

                decoded_output.append({name: params})
        return decoded_output

    def decode_execute(self, result):
        if "FC" not in self.model_name:
            if not result.startswith("["):
                result = "[" + result
            if not result.endswith("]"):
                result = result + "]"
            decoded_output = ast_parse(result)
            execution_list = []
            for function_call in decoded_output:
                for key, value in function_call.items():
                    execution_list.append(
                        f"{key}({','.join([f'{k}={repr(v)}' for k, v in value.items()])})"
                    )
            return execution_list
        else:
            function_call_list = result
            if type(function_call_list) == dict:
                function_call_list = [function_call_list]
            execution_list = []
            for function_call in function_call_list:
                for key, value in function_call.items():
                    execution_list.append(
                        f"{key}({','.join([f'{k}={repr(v)}' for k,v in value.items()])})"
                    )
            return execution_list

    #### FC methods ####

    def _query_FC(self, inference_data: dict):
        inference_data["inference_input_log"] = {
            "message": inference_data["message"],
            "tools": inference_data.get("tools", None),
            "tool_results": inference_data.get("tool_results", None),
            "chat_history": inference_data.get("chat_history", None),
            "preamble": self.preamble,
        }
        api_response = self.client.chat(
            message=inference_data["message"],
            model=self.model_name.replace("-FC", ""),
            temperature=self.temperature,
            tools=inference_data.get("tools", None),
            tool_results=inference_data.get("tool_results", None),
            preamble=self.preamble,
            chat_history=inference_data.get("chat_history", None),
        )

        return api_response

    def _pre_query_processing_FC(self, inference_data: dict, test_entry: dict) -> dict:
        for round_idx in range(len(test_entry["question"])):
            test_entry["question"][round_idx] = convert_system_prompt_into_user_prompt(
                test_entry["question"][round_idx]
            )
            test_entry["question"][round_idx] = self._substitute_content_name(
                test_entry["question"][round_idx]
            )
            test_entry["question"][round_idx] = self._substitute_prompt_role(
                test_entry["question"][round_idx]
            )

        # Cohere message is a string, not a list of dictionaries
        inference_data["message"] = ""
        inference_data["chat_history"] = []
        return inference_data

    def _compile_tools(self, inference_data: dict, test_entry: dict) -> dict:
        functions: list = test_entry["function"]
        test_category: str = test_entry["id"].rsplit("_", 1)[0]

        functions = func_doc_language_specific_pre_processing(functions, test_category)
        # Convert to Cohere compatible function schema
        tools = convert_to_tool(functions, GORILLA_TO_PYTHON, self.model_style)

        inference_data["tools"] = tools

        return inference_data

    def _parse_query_response_FC(self, api_response: any) -> dict:
        try:
            model_responses = [
                {func_call.name: func_call.parameters}
                for func_call in api_response.tool_calls
            ]
        except:
            model_responses = api_response.text

        return {
            "model_responses": model_responses,
            "tool_calls": api_response.tool_calls,
            "chat_history": api_response.chat_history,
            "input_token": api_response.meta.billed_units.input_tokens,
            "output_token": api_response.meta.billed_units.output_tokens,
        }

    def add_first_turn_message_FC(
        self, inference_data: dict, first_turn_message: list[dict]
    ) -> dict:
        message = extract_last_user_message(first_turn_message, "USER")["message"]
        inference_data["message"] = message
        if len(first_turn_message) > 0:
            inference_data["chat_history"] = first_turn_message
        return inference_data

    def _add_next_turn_user_message_FC(
        self, inference_data: dict, user_message: list[dict]
    ) -> dict:
        inference_data["message"] = user_message[0]["message"]
        # Cohere does not allow both message and tool_results to appear at the same time
        if "tool_results" in inference_data:
            del inference_data["tool_results"]
        return inference_data

    def _add_assistant_message_FC(
        self, inference_data: dict, model_response_data: dict
    ) -> dict:
        # Cohere has all the messages in the chat history already, so no need to add anything here
        return inference_data

    def _add_execution_results_FC(
        self, inference_data: dict, execution_results: list[str], model_response_data: dict
    ) -> dict:
        tool_results = []
        # Add the execution results to the current round result, one at a time
        for execution_result, tool_call in zip(
            execution_results, model_response_data["tool_calls"]
        ):
            # Cohere expects the `outputs` section to be a list of dictionaries, so we have to convert the string to that format
            tool_message = {
                "call": tool_call,
                "outputs": [{"function execution result": execution_result}],
            }
            tool_results.append(tool_message)

        inference_data["tool_results"] = tool_results
        # Cohere does not allow both message and tool_results to appear at the same time
        inference_data["message"] = ""
        return inference_data

    #### Prompting methods ####

    def _query_prompting(self, inference_data: dict):
        inference_data["inference_input_log"] = {
            "message": inference_data["message"],
            "preamble": inference_data["system_prompt"],
            "chat_history": inference_data.get("chat_history", None),
        }

        api_response = self.client.chat(
            message=inference_data["message"],
            model=self.model_name,
            temperature=self.temperature,
            preamble=inference_data["system_prompt"],
            chat_history=inference_data.get("chat_history", None),
        )

        return api_response

    def _pre_query_processing_prompting(self, test_entry: dict) -> dict:
        functions: list = test_entry["function"]
        test_entry_id: str = test_entry["id"]
        test_category: str = test_entry_id.rsplit("_", 1)[0]

        functions = func_doc_language_specific_pre_processing(functions, test_category)

        test_entry["question"][0] = system_prompt_pre_processing_chat_model(
            test_entry["question"][0], functions, test_category
        )
        # Cohere takes in system prompt in a specific field
        system_prompt = extract_system_prompt(test_entry["question"][0])

        for round_idx in range(len(test_entry["question"])):
            test_entry["question"][round_idx] = self._substitute_content_name(
                test_entry["question"][round_idx]
            )
            test_entry["question"][round_idx] = self._substitute_prompt_role(
                test_entry["question"][round_idx]
            )

        # Cohere message is a string, not a list of dictionaries
        return {"message": "", "system_prompt": system_prompt}

    def _parse_query_response_prompting(self, api_response: any) -> dict:

        return {
            "model_responses": api_response.text,
            "chat_history": api_response.chat_history,
            "input_token": api_response.meta.billed_units.input_tokens,
            "output_token": api_response.meta.billed_units.output_tokens,
        }

    def add_first_turn_message_prompting(
        self, inference_data: dict, first_turn_message: list[dict]
    ) -> dict:
        return self.add_first_turn_message_FC(inference_data, first_turn_message)

    def _add_next_turn_user_message_prompting(
        self, inference_data: dict, user_message: list[dict]
    ) -> dict:
        return self._add_next_turn_user_message_FC(inference_data, user_message)

    def _add_assistant_message_prompting(
        self, inference_data: dict, model_response_data: dict
    ) -> dict:
        # Cohere has all the messages in the chat history already, so no need to add anything here
        return inference_data

    def _add_execution_results_prompting(
        self, inference_data: dict, execution_results: list[str], model_response_data: dict
    ) -> dict:
        formatted_results_message = format_execution_results_prompting(
            inference_data, execution_results, model_response_data
        )
        # Cohere's message is a string, not a list of dictionaries
        inference_data["message"] = formatted_results_message

        return inference_data
