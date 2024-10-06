import json
import os

import vertexai
from bfcl.model_handler.base_handler import BaseHandler
from bfcl.model_handler.constant import DEFAULT_SYSTEM_PROMPT, GORILLA_TO_OPENAPI
from bfcl.model_handler.model_style import ModelStyle
from bfcl.model_handler.utils import (
    convert_to_tool,
    default_decode_ast_prompting,
    default_decode_execute_prompting,
    extract_system_prompt,
    format_execution_results_prompting,
    func_doc_language_specific_pre_processing,
    system_prompt_pre_processing_chat_model,
)

# This import from struct_pb2 should eventually be removed. See comment in the `_handle_struct_values` and `_handle_list_values` method below
from google.protobuf.struct_pb2 import ListValue, Struct
from vertexai.generative_models import (
    Content,
    FunctionDeclaration,
    GenerationConfig,
    GenerativeModel,
    Part,
    Tool,
)


class GeminiHandler(BaseHandler):
    def __init__(self, model_name, temperature) -> None:
        super().__init__(model_name, temperature)
        self.model_style = ModelStyle.Google
        # Initialize Vertex AI
        vertexai.init(
            project=os.getenv("VERTEX_AI_PROJECT_ID"),
            location=os.getenv("VERTEX_AI_LOCATION"),
        )
        self.client = GenerativeModel(self.model_name.replace("-FC", ""))

    @staticmethod
    def _substitute_prompt_role(prompts: list[dict]) -> list[dict]:
        # Allowed roles: user, model, function
        for prompt in prompts:
            if prompt["role"] == "user":
                prompt["role"] = "user"
            elif prompt["role"] == "assistant":
                prompt["role"] = "model"
            elif prompt["role"] == "tool":
                prompt["role"] = "function"

        return prompts

    def _handle_struct_values(self, input):
        # Note: Below is a workaround for a bug in the Vertex AI library
        # Accoding to the Vertex AI documentation https://ai.google.dev/gemini-api/docs/function-calling/tutorial?lang=python, cited below:
        """
        # Set the model up with tools.
        house_fns = [power_disco_ball, start_music, dim_lights]

        model = genai.GenerativeModel(model_name="gemini-1.5-flash", tools=house_fns)

        # Call the API.
        chat = model.start_chat()
        response = chat.send_message("Turn this place into a party!")

        # Print out each of the function calls requested from this single call.
        for part in response.parts:
            if fn := part.function_call:
                args = ", ".join(f"{key}={val}" for key, val in fn.args.items())
                print(f"{fn.name}({args})")
        """
        # ", ".join(f"{key}={val}" for key, val in fn.args.items()) should get the function call arguments in a ready-to-execute format
        # However, the above code snippet will not work as expected when `val` is a ListValue object, and it would further cause the json serialization error when writing the result to a file
        """
        # This is a typical ListValue object that is causing the issue. It is a list of 4 string values
        values {
            string_value: "driver"
        }
        values {
            string_value: "passenger"
        }
        values {
            string_value: "rear_left"
        }
        values {
            string_value: "rear_right"
        }
        """
        # To fix this, we need to unpack the ListValue object to a list of string values before joining them
        # So the above example gets converted to:
        """
        ["driver", "passenger", "rear_left", "rear_right"]
        """
        # This will be the temporary fix until the bug in the Vertex AI library is fixed
        # Convert it to dictionary for easier manipulation
        input = {k: v for k, v in input.items()}
        for k, v in input.items():
            if type(v) == ListValue:
                input[k] = self._handle_list_values(v)
            elif type(v) == Struct:
                input[k] = self._handle_struct_values(v)
        return input

    def _handle_list_values(self, input):
        """
        @typing.final
        class Value(google.protobuf.message.Message):
            "`Value` represents a dynamically typed value which can be either
            null, a number, a string, a boolean, a recursive struct value, or a
            list of values. A producer of value is expected to set one of these
            variants. Absence of any variant indicates an error.

            The JSON representation for `Value` is JSON value.
            "

            DESCRIPTOR: google.protobuf.descriptor.Descriptor

            NULL_VALUE_FIELD_NUMBER: builtins.int
            NUMBER_VALUE_FIELD_NUMBER: builtins.int
            STRING_VALUE_FIELD_NUMBER: builtins.int
            BOOL_VALUE_FIELD_NUMBER: builtins.int
            STRUCT_VALUE_FIELD_NUMBER: builtins.int
            LIST_VALUE_FIELD_NUMBER: builtins.int
            null_value: global___NullValue.ValueType
            "Represents a null value."
            number_value: builtins.float
            "Represents a double value."
            string_value: builtins.str
            "Represents a string value."
            bool_value: builtins.bool
            "Represents a boolean value."
            @property
            def struct_value(self) -> global___Struct:
                "Represents a structured value."

            @property
            def list_value(self) -> global___ListValue:
                "Represents a repeated `Value`."

            def __init__(
                self,
                *,
                null_value: global___NullValue.ValueType | None = ...,
                number_value: builtins.float | None = ...,
                string_value: builtins.str | None = ...,
                bool_value: builtins.bool | None = ...,
                struct_value: global___Struct | None = ...,
                list_value: global___ListValue | None = ...,
            ) -> None: ...
            def HasField(self, field_name: typing.Literal["bool_value", b"bool_value", "kind", b"kind", "list_value", b"list_value", "null_value", b"null_value", "number_value", b"number_value", "string_value", b"string_value", "struct_value", b"struct_value"]) -> builtins.bool: ...
            def ClearField(self, field_name: typing.Literal["bool_value", b"bool_value", "kind", b"kind", "list_value", b"list_value", "null_value", b"null_value", "number_value", b"number_value", "string_value", b"string_value", "struct_value", b"struct_value"]) -> None: ...
            def WhichOneof(self, oneof_group: typing.Literal["kind", b"kind"]) -> typing.Literal["null_value", "number_value", "string_value", "bool_value", "struct_value", "list_value"] | None: ...
        """
        parsed_list_result = []
        for item in input.values:
            field_name = item.WhichOneof("kind")
            if field_name == "null_value":
                value = item.null_value
            elif field_name == "number_value":
                value = item.number_value
            elif field_name == "string_value":
                value = item.string_value
            elif field_name == "bool_value":
                value = item.bool_value
            elif field_name == "struct_value":
                value = self._handle_struct_values(item.struct_value)
            elif field_name == "list_value":
                value = self._handle_list_values(item.list_value)
            else:
                value = None
            parsed_list_result.append(value)

        return parsed_list_result

    def decode_ast(self, result, language="Python"):
        if "FC" not in self.model_name:
            result = result.replace("```tool_code\n", "").replace("\n```", "")
            return default_decode_ast_prompting(result, language)
        else:
            if type(result) is not list:
                result = [result]
            return result

    def decode_execute(self, result):
        if "FC" not in self.model_name:
            result = result.replace("```tool_code\n", "").replace("\n```", "")
            return default_decode_execute_prompting(result)
        else:
            func_call_list = []
            for function_call in result:
                for func_name, func_args in function_call.items():
                    func_call_list.append(
                        f"{func_name}({','.join([f'{k}={repr(v)}' for k, v in func_args.items()])})"
                    )
            return func_call_list

    #### FC methods ####

    def _query_FC(self, inference_data: dict):
        # Gemini models needs to first conver the function doc to FunctionDeclaration and Tools objects.
        # We do it here to avoid json serialization issues.
        func_declarations = []
        for function in inference_data["tools"]:
            func_declarations.append(
                FunctionDeclaration(
                    name=function["name"],
                    description=function["description"],
                    parameters=function["parameters"],
                )
            )

        tools = [Tool(function_declarations=func_declarations)]

        inference_data["inference_input_log"] = {
            "message": repr(inference_data["message"]),
            "tools": inference_data["tools"],
            "system_prompt": inference_data.get("system_prompt", None),
        }

        # messages are already converted to Content object
        if "system_prompt" in inference_data:
            # We re-instantiate the GenerativeModel object with the system prompt
            # We cannot reassign the self.client object as it will affect other entries
            client = GenerativeModel(
                self.model_name.replace("-FC", ""),
                system_instruction=inference_data["system_prompt"],
            )
            api_response = client.generate_content(
                contents=inference_data["message"],
                generation_config=GenerationConfig(
                    temperature=self.temperature,
                ),
                tools=tools if len(tools) > 0 else None,
            )
        else:
            api_response = self.client.generate_content(
                contents=inference_data["message"],
                generation_config=GenerationConfig(
                    temperature=self.temperature,
                ),
                tools=tools if len(tools) > 0 else None,
            )
        return api_response

    def _pre_query_processing_FC(self, inference_data: dict, test_entry: dict) -> dict:

        for round_idx in range(len(test_entry["question"])):
            test_entry["question"][round_idx] = self._substitute_prompt_role(
                test_entry["question"][round_idx]
            )

        inference_data["message"] = []

        system_prompt = extract_system_prompt(test_entry["question"][0])
        if system_prompt:
            inference_data["system_prompt"] = system_prompt
        return inference_data

    def _compile_tools(self, inference_data: dict, test_entry: dict) -> dict:
        functions: list = test_entry["function"]
        test_category: str = test_entry["id"].rsplit("_", 1)[0]

        functions = func_doc_language_specific_pre_processing(functions, test_category)
        tools = convert_to_tool(functions, GORILLA_TO_OPENAPI, self.model_style)

        inference_data["tools"] = tools

        return inference_data

    def _parse_query_response_FC(self, api_response: any) -> dict:
        response_function_call_content = api_response.candidates[0].content
        tool_call_func_names = []
        fc_parts = []
        text_parts = []
        for part in api_response.candidates[0].content.parts:
            # part.function_call is a FunctionCall object, so it will always be True even if it contains no function call
            # So we need to check if the function name is empty `""` to determine if Gemini returned a function call
            if part.function_call and part.function_call.name:
                part_func_name = part.function_call.name
                part_func_args = part.function_call.args
                # Bug patch for the Vertex AI library
                part_func_args_dict = self._handle_struct_values(part_func_args)

                fc_parts.append({part_func_name: part_func_args_dict})
                tool_call_func_names.append(part_func_name)
            else:
                # Note: Below is a workaround for a bug in the Vertex AI library
                # We should use `part.text` to get the text content of the part, per the Vertex AI documentation
                # However, calling part.text will yield the error
                """TypeError: argument of type 'Part' is not iterable"""
                # This is a bug in the Vertex AI library, specifically from line `if "text" not in self._raw_part:` in the `text` method in `Part` class in vertexai.generative_models._generative_models
                """
                class Part:
                    @property
                    def text(self) -> str:
                        if "text" not in self._raw_part:
                            raise AttributeError(
                                "Response candidate content part has no text.\n"
                                "Part:\n" + _dict_to_pretty_string(self.to_dict())
                            )
                        return self._raw_part.text
                """
                # Directly accessing the `part._raw_part.text` attribute is a workaround for this bug, until the bug is fixed
                text_parts.append(part._raw_part.text)

        model_responses = fc_parts if fc_parts else text_parts

        return {
            "model_responses": model_responses,
            "model_responses_message_for_chat_history": response_function_call_content,
            "tool_call_func_names": tool_call_func_names,
            "input_token": api_response.usage_metadata.prompt_token_count,
            "output_token": api_response.usage_metadata.candidates_token_count,
        }

    def add_first_turn_message_FC(
        self, inference_data: dict, first_turn_message: list[dict]
    ) -> dict:
        for message in first_turn_message:
            inference_data["message"].append(
                Content(
                    role=message["role"],
                    parts=[
                        Part.from_text(message["content"]),
                    ],
                )
            )
        return inference_data

    def _add_next_turn_user_message_FC(
        self, inference_data: dict, user_message: list[dict]
    ) -> dict:
        return self.add_first_turn_message_FC(inference_data, user_message)

    def _add_assistant_message_FC(
        self, inference_data: dict, model_response_data: dict
    ) -> dict:
        inference_data["message"].append(
            model_response_data["model_responses_message_for_chat_history"]
        )
        return inference_data

    def _add_execution_results_FC(
        self,
        inference_data: dict,
        execution_results: list[str],
        model_response_data: dict,
    ) -> dict:
        # Tool response needs to be converted to Content object as well.
        # One Content object for all tool responses.
        tool_response_parts = []
        for execution_result, tool_call_func_name in zip(
            execution_results, model_response_data["tool_call_func_names"]
        ):
            tool_response_parts.append(
                Part.from_function_response(
                    name=tool_call_func_name,
                    response={
                        "content": execution_result,
                    },
                )
            )

        tool_response_content = Content(parts=tool_response_parts)
        inference_data["message"].append(tool_response_content)

        return inference_data

    #### Prompting methods ####

    def _query_prompting(self, inference_data: dict):
        inference_data["inference_input_log"] = {
            "message": repr(inference_data["message"]),
            "system_prompt": inference_data.get("system_prompt", None),
        }

        # messages are already converted to Content object
        if "system_prompt" in inference_data:
            client = GenerativeModel(
                self.model_name.replace("-FC", ""),
                system_instruction=inference_data["system_prompt"],
            )
            api_response = client.generate_content(
                contents=inference_data["message"],
                generation_config=GenerationConfig(
                    temperature=self.temperature,
                ),
            )
        else:
            api_response = self.client.generate_content(
                contents=inference_data["message"],
                generation_config=GenerationConfig(
                    temperature=self.temperature,
                ),
            )
        return api_response

    def _pre_query_processing_prompting(self, test_entry: dict) -> dict:
        functions: list = test_entry["function"]
        test_category: str = test_entry["id"].rsplit("_", 1)[0]

        functions = func_doc_language_specific_pre_processing(functions, test_category)

        for round_idx in range(len(test_entry["question"])):
            test_entry["question"][round_idx] = self._substitute_prompt_role(
                test_entry["question"][round_idx]
            )

        test_entry["question"][0] = system_prompt_pre_processing_chat_model(
            test_entry["question"][0], DEFAULT_SYSTEM_PROMPT, functions
        )
        # Gemini has system prompt in a specific field
        system_prompt = extract_system_prompt(test_entry["question"][0])

        if system_prompt:
            return {"message": [], "system_prompt": system_prompt}
        else:
            return {"message": []}

    def _parse_query_response_prompting(self, api_response: any) -> dict:
        # Note: Same issue as with mentioned in `_parse_query_response_FC` method
        # According to the Vertex AI documentation, `api_response.text` should be enough.
        # However, under the hood, it is calling `api_response.candidates[0].content.parts[0].text` which is causing the issue
        """TypeError: argument of type 'Part' is not iterable"""
        # So again, we need to directly access the `api_response.candidates[0].content.parts[0]._raw_part.text` attribute to get the text content of the part
        # This is a workaround for this bug, until the bug is fixed

        if len(api_response.candidates[0].content.parts) > 0:
            model_responses = api_response.candidates[0].content.parts[0]._raw_part.text
        else:
            model_responses = "The model did not return any response."
        return {
            "model_responses": model_responses,
            "input_token": api_response.usage_metadata.prompt_token_count,
            "output_token": api_response.usage_metadata.candidates_token_count,
        }

    def add_first_turn_message_prompting(
        self, inference_data: dict, first_turn_message: list[dict]
    ) -> dict:
        for message in first_turn_message:
            inference_data["message"].append(
                Content(
                    role=message["role"],
                    parts=[
                        Part.from_text(message["content"]),
                    ],
                )
            )
        return inference_data

    def _add_next_turn_user_message_prompting(
        self, inference_data: dict, user_message: list[dict]
    ) -> dict:
        return self.add_first_turn_message_prompting(inference_data, user_message)

    def _add_assistant_message_prompting(
        self, inference_data: dict, model_response_data: dict
    ) -> dict:
        inference_data["message"].append(
            Content(
                role="model",
                parts=[
                    Part.from_text(model_response_data["model_responses"]),
                ],
            )
        )
        return inference_data

    def _add_execution_results_prompting(
        self, inference_data: dict, execution_results: list[str], model_response_data: dict
    ) -> dict:
        formatted_results_message = format_execution_results_prompting(
            inference_data, execution_results, model_response_data
        )
        tool_message = Content(
            role="user",
            parts=[
                Part.from_text(formatted_results_message),
            ],
        )
        inference_data["message"].append(tool_message)
        return inference_data
