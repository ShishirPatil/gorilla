import json
import random
import string

from bfcl.model_handler.local_inference.base_oss_handler import OSSHandler
from bfcl.model_handler.utils import (
    convert_to_function_call,
    func_doc_language_specific_pre_processing,
)
from overrides import override


class PhiFCHandler(OSSHandler):
    def __init__(self, model_name, temperature) -> None:
        super().__init__(model_name, temperature)
        # Strip the -FC suffix when initializing the actual model
        if model_name.endswith("-FC"):
            self.model_name_huggingface = model_name[:-3]
        else:
            self.model_name_huggingface = model_name
            
        # Store the original model name for reference
        self.original_model_name = model_name

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

    @staticmethod
    def _construct_tool_doc(functions):
        """
        Constructs the tool documentation in the format expected by Phi-4-mini-instruct
        """
        tool_docs = []
        for function in functions:
            tool_doc = {
                "name": function["name"],
                "description": function["description"],
                "parameters": function["parameters"]
            }
            tool_docs.append(tool_doc)
        
        return json.dumps(tool_docs)

    @override
    def _format_prompt(self, messages, function):
        """
        Format the prompt according to Phi-4-mini-instruct's expectations
        
        Chat format:
        <|system|>Insert System Message<|end|><|user|>Insert User Message<|end|><|assistant|>
        
        Function calling format:
        <|system|>You are a helpful assistant with some tools.<|tool|>[{...}]<|/tool|><|end|><|user|>...<|end|><|assistant|>
        """
        formatted_prompt = ""
        
        # Handle system message and tool specification
        system_content = ""
        has_system = False
        
        if messages and messages[0]["role"] == "system":
            system_content = messages[0]["content"]
            has_system = True
            messages = messages[1:]  # Remove system message from the list
        
        # Add system message with tools if functions are provided
        if has_system or function:
            formatted_prompt += "<|system|>"
            if system_content:
                formatted_prompt += system_content
            
            # Add tool documentation if functions are provided
            if function:
                formatted_prompt += "<|tool|>" + self._construct_tool_doc(function) + "<|/tool|>"
            
            formatted_prompt += "<|end|>"
        
        # Add the rest of the messages
        for message in messages:
            if message["role"] == "user":
                formatted_prompt += f"<|user|>{message['content']}<|end|>"
            elif message["role"] == "assistant":
                formatted_prompt += f"<|assistant|>{message['content']}<|end|>"
            elif message["role"] == "tool":
                # Format tool response
                formatted_prompt += f"<|tool_response|>{message['content']}<|end|>"
        
        # Add the final assistant prompt
        formatted_prompt += "<|assistant|>"
        
        return formatted_prompt

    @override
    def _pre_query_processing_prompting(self, test_entry: dict) -> dict:
        functions: list = test_entry["function"]
        test_category: str = test_entry["id"].rsplit("_", 1)[0]

        functions = func_doc_language_specific_pre_processing(functions, test_category)

        return {"message": [], "function": functions}

    @staticmethod
    def generate_random_string() -> str:
        """Generates a random string of alphanumeric characters of length 9."""
        characters = string.ascii_letters + string.digits
        random_string = "".join(random.choices(characters, k=9))
        return random_string

    @override
    def _parse_query_response_prompting(self, api_response: any) -> dict:
        model_responses = api_response.choices[0].text
        tool_call_ids = []
        
        try:
            # Try to parse the response as JSON for function calls
            model_responses = json.loads(model_responses)
            for model_response in model_responses:
                tool_call_id = self.generate_random_string()
                if "id" not in model_response:
                    model_response["id"] = tool_call_id
                tool_call_ids.append(tool_call_id)

            # Prepare the model responses for chat history
            model_responses_message_for_chat_history = json.dumps(model_responses)
            
            # Convert to the expected format
            model_responses = [
                {item["name"]: item["parameters"]} for item in model_responses
            ]
        except json.JSONDecodeError:
            # If not a valid JSON, treat as regular text response
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
        inference_data["message"].append(
            {
                "role": "assistant",
                "content": model_response_data["model_responses_message_for_chat_history"],
            }
        )
        return inference_data

    @override
    def _add_execution_results_prompting(
        self, inference_data: dict, execution_results: list[str], model_response_data: dict
    ) -> dict:
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
