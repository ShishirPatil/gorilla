import json
import os
import time
from openai import OpenAI, RateLimitError
from bfcl.model_handler.base_handler import BaseHandler
from bfcl.model_handler.model_style import ModelStyle
from bfcl.model_handler.utils import (
    ast_parse,
    convert_to_function_call,
    format_execution_results_prompting,
    func_doc_language_specific_pre_processing,
    system_prompt_pre_processing_chat_model,
    retry_with_backoff,
)

class GrokHandler(BaseHandler):
    def __init__(self, model_name, temperature) -> None:
        print(f"\n=== Initializing GrokHandler ===")
        print(f"Input model_name: {model_name}")
        print(f"Temperature: {temperature}")
        
        super().__init__(model_name, temperature)
        self.model_style = ModelStyle.Grok
        
        self.api_key = os.getenv("GROK_API_KEY")
        self.base_url = os.getenv("GROK_API_BASE_URL", "https://api.x.ai/v1")
        
        print(f"API Base URL: {self.base_url}")
        print(f"API Key present: {'Yes' if self.api_key else 'No'}")
        
        if not self.api_key:
            raise ValueError("GROK_API_KEY is not set in environment variables.")
            
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        print("Successful")
        print("===============================\n")

    def _get_actual_model_name(self, model_name: str) -> str:
        return "grok-beta"

    @retry_with_backoff(RateLimitError)
    def _make_api_call(self, **kwargs):
        start_time = time.time()
        try:
            response = self.client.chat.completions.create(**kwargs)
            latency = time.time() - start_time
            return response, latency
        except Exception as e:
            latency = time.time() - start_time
            raise e

    def decode_ast(self, result, language="Python"):
        if "FC" in self.model_name:
            decoded_output = []
            for invoked_function in result:
                name = list(invoked_function.keys())[0]
                params = json.loads(invoked_function[name])
                decoded_output.append({name: params})
            return decoded_output
        else:
            func = result
            func = func.replace("\\_", "_")
            if not func.startswith("["):
                func = "[" + func
            if not func.endswith("]"):
                func = func + "]"
            decoded_output = ast_parse(func, language)
            return decoded_output

    def decode_execute(self, result):
        if "FC" in self.model_name:
            function_call = convert_to_function_call(result)
            return function_call
        else:
            func = result
            func = func.replace("\\_", "_")
            decode_output = ast_parse(func)
            execution_list = []
            for function_call in decode_output:
                for key, value in function_call.items():
                    execution_list.append(
                        f"{key}({','.join([f'{k}={repr(v)}' for k, v in value.items()])})"
                    )
            return execution_list

    def _query_FC(self, inference_data: dict):
        print("\n=== Starting _query_FC ===")
        message = inference_data["message"]
        tools = inference_data.get("tools", [])
        
        print(f"Messages structure: {json.dumps(message, indent=2)}")
        print(f"Number of tools: {len(tools)}")
        if tools:
            print(f"First tool example: {json.dumps(tools[0], indent=2)}")
        
        actual_model_name = self._get_actual_model_name(self.model_name)
        print(f"Using model name: {actual_model_name}")
        
        try:
            kwargs = {
                "model": actual_model_name,
                "messages": message,
                "temperature": self.temperature,
            }
            if tools:
                kwargs["tools"] = tools
            
            response, latency = self._make_api_call(**kwargs)
            print("API call successful")
            return response, latency
            
        except Exception as e:
            print(f"\nError in query_FC:")
            print(f"Error type: {type(e).__name__}")
            print(f"Error message: {str(e)}")
            if hasattr(e, 'response'):
                print(f"Response status: {e.response.status_code}")
                print(f"Response body: {e.response.text}")
            raise

    def _pre_query_processing_FC(self, inference_data: dict, test_entry: dict) -> dict:
        inference_data["message"] = [
            {"role": "system", "content": "You are a helpful assistant skilled at using the provided tools."}
        ]
        return inference_data

    def _compile_tools(self, inference_data: dict, test_entry: dict) -> dict:
        functions = test_entry["function"]
        test_category = test_entry["id"].rsplit("_", 1)[0]
        functions = func_doc_language_specific_pre_processing(functions, test_category)
        tools = [{"type": "function", "function": f} for f in functions]
        inference_data["tools"] = tools
        return inference_data

    def _parse_query_response_FC(self, api_response: any) -> dict:
        try:
            message = api_response.choices[0].message
            tool_calls = message.tool_calls if hasattr(message, 'tool_calls') else []
            
            model_responses = []
            tool_call_func_names = []
            tool_call_ids = []
            
            if tool_calls:
                for tool_call in tool_calls:
                    model_responses.append({
                        tool_call.function.name: tool_call.function.arguments
                    })
                    tool_call_func_names.append(tool_call.function.name)
                    tool_call_ids.append(tool_call.id)
            else:
                model_responses = message.content
            
            return {
                "model_responses": model_responses,
                "model_responses_message_for_chat_history": message,
                "tool_call_func_names": tool_call_func_names,
                "tool_call_ids": tool_call_ids,
                "input_token": api_response.usage.prompt_tokens,
                "output_token": api_response.usage.completion_tokens,
            }
        except Exception as e:
            print(f"Error parsing response: {e}")
            return {
                "model_responses": [],
                "model_responses_message_for_chat_history": None,
                "tool_call_func_names": [],
                "tool_call_ids": [],
                "input_token": 0,
                "output_token": 0,
            }

    def add_first_turn_message_FC(self, inference_data: dict, first_turn_message: list[dict]) -> dict:
        if "message" not in inference_data:
            inference_data["message"] = []
        inference_data["message"].extend(first_turn_message)
        return inference_data

    def _add_next_turn_user_message_FC(self, inference_data: dict, user_message: list[dict]) -> dict:
        if "message" not in inference_data:
            inference_data["message"] = []
        inference_data["message"].extend(user_message)
        return inference_data

    def _add_assistant_message_FC(self, inference_data: dict, model_response_data: dict) -> dict:
        if "message" not in inference_data:
            inference_data["message"] = []
        inference_data["message"].append(
            model_response_data["model_responses_message_for_chat_history"]
        )
        return inference_data

    def _add_execution_results_FC(
        self, inference_data: dict, execution_results: list[str], model_response_data: dict
    ) -> dict:
        if "message" not in inference_data:
            inference_data["message"] = []
        for execution_result, func_name, tool_call_id in zip(
            execution_results,
            model_response_data["tool_call_func_names"],
            model_response_data["tool_call_ids"],
        ):
            tool_message = {
                "role": "tool",
                "name": func_name,
                "content": str(execution_result),
                "tool_call_id": tool_call_id,
            }
            inference_data["message"].append(tool_message)
        return inference_data

    def _query_prompting(self, inference_data: dict):
        print("\n=== Starting _query_prompting ===")
        message = inference_data["message"]
        print(f"Messages structure: {json.dumps(message, indent=2)}")
        
        actual_model_name = self._get_actual_model_name(self.model_name)
        print(f"Using model name: {actual_model_name}")
        
        try:
            response, latency = self._make_api_call(
                model=actual_model_name,
                messages=message,
                temperature=self.temperature,
            )
            print("API call successful")
            return response, latency
            
        except Exception as e:
            print(f"\nError in _query_prompting:")
            print(f"Error type: {type(e).__name__}")
            print(f"Error message: {str(e)}")
            if hasattr(e, 'response'):
                print(f"Response status: {e.response.status_code}")
                print(f"Response body: {e.response.text}")
            raise

    def _pre_query_processing_prompting(self, test_entry: dict) -> dict:
        functions = test_entry["function"]
        test_category = test_entry["id"].rsplit("_", 1)[0]
        
        functions = func_doc_language_specific_pre_processing(functions, test_category)
        test_entry["question"][0] = system_prompt_pre_processing_chat_model(
            test_entry["question"][0], functions, test_category
        )
        return {"message": []}

    def _parse_query_response_prompting(self, api_response: any) -> dict:
        try:
            return {
                "model_responses": api_response.choices[0].message.content,
                "model_responses_message_for_chat_history": api_response.choices[0].message,
                "input_token": api_response.usage.prompt_tokens,
                "output_token": api_response.usage.completion_tokens,
            }
        except Exception as e:
            print(f"Error parsing prompting response: {e}")
            return {
                "model_responses": "",
                "model_responses_message_for_chat_history": None,
                "input_token": 0,
                "output_token": 0,
            }

    def add_first_turn_message_prompting(self, inference_data: dict, first_turn_message: list[dict]) -> dict:
        if "message" not in inference_data:
            inference_data["message"] = []
        inference_data["message"].extend(first_turn_message)
        return inference_data

    def _add_next_turn_user_message_prompting(self, inference_data: dict, user_message: list[dict]) -> dict:
        if "message" not in inference_data:
            inference_data["message"] = []
        inference_data["message"].extend(user_message)
        return inference_data

    def _add_assistant_message_prompting(self, inference_data: dict, model_response_data: dict) -> dict:
        if "message" not in inference_data:
            inference_data["message"] = []
        inference_data["message"].append(
            model_response_data["model_responses_message_for_chat_history"]
        )
        return inference_data

    def _add_execution_results_prompting(
        self, inference_data: dict, execution_results: list[str], model_response_data: dict
    ) -> dict:
        if "message" not in inference_data:
            inference_data["message"] = []
        formatted_results_message = format_execution_results_prompting(
            inference_data, execution_results, model_response_data
        )
        inference_data["message"].append(
            {"role": "user", "content": formatted_results_message}
        )
        return inference_data