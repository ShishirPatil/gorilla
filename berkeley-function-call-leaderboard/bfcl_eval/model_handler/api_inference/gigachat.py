import json
import os
import time
from typing import Any

from bfcl_eval.constants.type_mappings import GORILLA_TO_OPENAPI
from bfcl_eval.model_handler.base_handler import BaseHandler
from bfcl_eval.constants.enums import ModelStyle
from bfcl_eval.model_handler.utils import (
    convert_to_function_call,
    convert_to_tool,
    retry_with_backoff,
)
from langchain_gigachat.chat_models import GigaChat
from langchain_core.messages import AIMessage


class GigaChatHandler(BaseHandler):
    def __init__(
        self,
        model_name,
        temperature,
        registry_name,
        is_fc_model,
        **kwargs,
    ) -> None:
        super().__init__(model_name, temperature, registry_name, is_fc_model, **kwargs)
        self.model_style = ModelStyle.OPENAI_COMPLETIONS  # GigaChat uses OpenAI-compatible format

        base_url = None
        if "IFT" in model_name:
            base_url = os.getenv("GIGA_IFT_BASE_URL")
        elif "PROD" in model_name:
            base_url = os.getenv("GIGA_PROD_BASE_URL")
        
        if not base_url:
            base_url = os.getenv("GIGA_BASE_URL")

        self.client = GigaChat(
            model=model_name.split("--")[0],
            user=os.getenv("GIGA_USER"),
            password=os.getenv("GIGA_PASSWORD"),
            credentials=os.getenv("GIGA_CREDENTIALS"),
            base_url=base_url,
            auth_url="https://gigachat.sberdevices.ru/v1/token",
            verify_ssl_certs=False,
            profanity_check=False,
            repetition_penalty=1.0,
            temperature=temperature,
            timeout=os.getenv("GIGA_TIMEOUT", 100)
        )

    def decode_ast(self, result, language, has_tool_call_tag):
        if "FC" in self.model_name or self.is_fc_model:
            decoded_output = []
            for invoked_function in result:
                name = list(invoked_function.keys())[0]
                params = json.loads(invoked_function[name])
                decoded_output.append({name: params})
            return decoded_output
        else:
            # This should not be called for FC models
            raise NotImplementedError("GigaChatHandler only supports function calling mode")

    def decode_execute(self, result, has_tool_call_tag):
        if "FC" in self.model_name or self.is_fc_model:
            return convert_to_function_call(result)
        else:
            # This should not be called for FC models
            raise NotImplementedError("GigaChatHandler only supports function calling mode")

    @retry_with_backoff(error_type=Exception)
    def generate_with_backoff(self, **kwargs):
        start_time = time.time()

        # Bind tools if provided
        giga_tools = [
            tool["function"] for tool in kwargs.get("tools", [])
        ]

        # fix function schemas
        for tool in giga_tools:
            is_valid, error_msg = fix_function_schema(tool)
            if not is_valid:
                print(f"ERROR: Function schema for tool {tool['name']} is invalid: {error_msg}")

        if giga_tools:
            llm_with_tools = self.client.bind_tools(giga_tools)
            api_response = llm_with_tools.invoke(kwargs["messages"])
        else:
            api_response = self.client.invoke(kwargs["messages"])
        
        end_time = time.time()

        return api_response, end_time - start_time

    #### FC methods ####

    def _query_FC(self, inference_data: dict):
        message: list[dict] = inference_data["message"]
        tools = inference_data["tools"]
        inference_data["inference_input_log"] = {"message": repr(message), "tools": tools}

        kwargs = {
            "messages": message,
            "temperature": self.temperature,
        }

        if len(tools) > 0:
            kwargs["tools"] = tools

        return self.generate_with_backoff(**kwargs)

    def _pre_query_processing_FC(self, inference_data: dict, test_entry: dict) -> dict:
        inference_data["message"] = []
        return inference_data

    def _compile_tools(self, inference_data: dict, test_entry: dict) -> dict:
        functions: list = test_entry["function"]

        tools = convert_to_tool(functions, GORILLA_TO_OPENAPI, self.model_style)

        inference_data["tools"] = tools

        return inference_data

    def _parse_query_response_FC(self, api_response: AIMessage) -> dict:

        tool_calls = getattr(api_response, 'tool_calls', [])
        model_responses = []
        tool_call_ids = []

        if not tool_calls:
            model_responses = api_response.content
        else:
            for tool_call in tool_calls:
                model_responses.append({tool_call["name"]: json.dumps(tool_call["args"])})
                tool_call_ids.append(tool_call["id"])

        token_usage_metadata = api_response.response_metadata.get("token_usage", None)

        return {
            "model_responses": model_responses,
            "model_responses_message_for_chat_history": api_response,
            "tool_call_ids": tool_call_ids,
            "input_token": token_usage_metadata["prompt_tokens"],
            "output_token": token_usage_metadata["completion_tokens"],
        }

    def add_first_turn_message_FC(
        self, inference_data: dict, first_turn_message: list[dict]
    ) -> dict:
        inference_data["message"].extend(first_turn_message)
        return inference_data

    def _add_next_turn_user_message_FC(
        self, inference_data: dict, user_message: list[dict]
    ) -> dict:
        inference_data["message"].extend(user_message)
        return inference_data

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
        # Add the execution results to the current round result, one at a time
        for execution_result, tool_call_id in zip(
            execution_results, model_response_data["tool_call_ids"]
        ):
            tool_message = {
                "role": "tool",
                "content": execution_result,
                "tool_call_id": tool_call_id,
            }
            inference_data["message"].append(tool_message)

        return inference_data

    def _add_reasoning_content_if_available_FC(
        self, api_response: Any, response_data: dict
    ) -> None:
        """
        GigaChat doesn't show reasoning content in the api response like some other models.
        This method is included for compatibility but doesn't do anything for GigaChat.
        """
        pass


def fix_function_schema(schema, print_fixes: bool = False):
    """
    Validates a JSON schema for a function.
    
    Args:
        schema (dict): The function schema to validate
        
    Returns:
        tuple: (is_valid, error_message)
               - is_valid (bool): True if schema is valid, False otherwise
               - error_message (str): Error description if invalid, empty string if valid
    """
    
    def validate_parameters(params, param_type="parameter"):
        """Recursively validate parameters"""
        if not isinstance(params, dict):
            return False, f"{param_type} must be a dictionary"
        
        for param_name, param_def in params.items():
            if not isinstance(param_def, dict):
                return False, f"Parameter '{param_name}' definition must be a dictionary"
            
            # Check required fields
            if "type" not in param_def:
                return False, f"Parameter '{param_name}' missing required field 'type'"
            
            if param_def["type"] == "dict":
                param_def["type"] = "object"

            if "description" not in param_def:
                if print_fixes:
                    print(f"FIXED: Parameter '{param_name}' missing required field 'description'")
                param_def["description"] = ""
                # return False, f"Parameter '{param_name}' missing required field 'description'"
            
            param_type_value = param_def["type"]
            
            # Check for invalid fields based on type
            allowed_fields = {"type", "description"}
            
            if param_type_value == "string":
                allowed_fields.add("enum")

            elif param_type_value == "array":
                allowed_fields.add("items")
                is_valid, error = validate_parameters({"items": param_def["items"]}, f"array parameter '{param_name}'")
                if not is_valid:
                    return False, error

            elif param_type_value == "object":
                allowed_fields.add("properties")
                allowed_fields.add("required")
                # Recursively validate object parameters
                if "properies" in param_def:
                    is_valid, error = validate_parameters(param_def["properties"], f"object parameter '{param_name}'")
                    if not is_valid:
                        return False, error
                else:
                    if print_fixes:
                        print(f"FIXED: Parameter '{param_name}' has no properties")
                    param_def["properties"] = {}

            # Check for disallowed fields
            fields_to_remove = []
            for field in param_def:
                if field not in allowed_fields:
                    if print_fixes:
                        print(f"FIXED: Parameter '{param_name}' has disallowed field '{field}' for type '{param_type_value}'")
                    fields_to_remove.append(field)
                    # return False, f"Parameter '{param_name}' has disallowed field '{field}' for type '{param_type_value}'"

            if not param_def["description"].endswith("."):
                param_def["description"] += "."

            for field in fields_to_remove:
                param_def["description"] += f" {field}: {param_def[field]};"
                del param_def[field]

        return True, ""
    
    # Check if schema is a dictionary
    if not isinstance(schema, dict):
        return False, "Schema must be a dictionary"
    
    # Check required top-level fields
    if "name" not in schema:
        schema["name"] = "unknown_name"
    if "description" not in schema:
        schema["description"] = "unknown"
    if "parameters" not in schema:
        schema["parameters"] = {
            "properties": {},
        }

    schema["parameters"]["type"] = "object"

    # Validate parameters
    is_valid, error = validate_parameters(schema["parameters"]["properties"], "input parameter")
    if not is_valid:
        return False, f"Input parameters validation failed: {error}"

    # Validate return_parameters
    if "return_parameters" in schema:
        if "properties" not in schema["return_parameters"]:
            if print_fixes:
                print(f"FIXED: Return parameters has no properties")
            schema["return_parameters"]["properties"] = {}
        is_valid, error = validate_parameters(schema["return_parameters"]["properties"], "return parameter")
        if not is_valid:
            return False, f"Return parameters validation failed: {error}"

    return True, ""
