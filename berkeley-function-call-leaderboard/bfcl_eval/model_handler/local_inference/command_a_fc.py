import json
import re
import ast
from bfcl_eval.model_handler.local_inference.base_oss_handler import OSSHandler
from bfcl_eval.model_handler.utils import func_doc_language_specific_pre_processing, convert_to_tool
from bfcl_eval.constants.type_mappings import GORILLA_TO_OPENAPI
from bfcl_eval.model_handler.model_style import ModelStyle
from overrides import override

class CommandAFCHandler(OSSHandler):
    """
    Handler for CohereLabs/c4ai-command-a-03-2025 model in function calling mode.
    
    This model uses a specific chat template for tool use that includes:
    - Tool definitions in the conversation
    - Tool calls in JSON format
    - Tool results in the conversation flow
    
    For more details, see the model card:
    https://huggingface.co/CohereLabs/c4ai-command-a-03-2025
    """
    
    def __init__(self, model_name, temperature) -> None:
        super().__init__(model_name, temperature)
        self.model_name_huggingface = model_name.replace("-FC", "") if "-FC" in model_name else model_name 

    @override
    def _format_prompt(self, messages, function):
        """
        Format the prompt to match the CohereLabs/c4ai-command-a-03-2025 tool_use chat template exactly.
        """
        tools = convert_to_tool(function, GORILLA_TO_OPENAPI, ModelStyle.COHERE)
        tokenizer = self.tokenizer
        formatted_prompt = tokenizer.apply_chat_template(
            messages,
            tools=tools,
            tokenize=False,
            add_generation_prompt=True
        )
        return formatted_prompt
    
    def _convert_to_tool_calls(self, tool_calls: list[dict]) -> list[dict]:
        tools = []
        for tool_call in tool_calls:
            tools.append(
                {
                    "id": tool_call["tool_call_id"],
                    "type": "function",
                    "function": {"name": tool_call["tool_name"], "arguments": tool_call["parameters"]}
                }
            )
        return tools
    
    
    @override
    def _parse_query_response_prompting(self, api_response: any) -> dict:
        model_response = api_response.choices[0].text 
        
        # Set regex patterns and extract tool_calls and tool_plan
        tool_calls_pattern = r"<\|START_ACTION\|>(.*?)<\|END_ACTION\|>"
        tool_plan_pattern = r"<\|START_THINKING\|>(.*?)<\|END_THINKING\|>"
        
        tool_calls = []
        tool_calls_match = re.search(tool_calls_pattern, model_response, re.DOTALL)
        if tool_calls_match:
            tool_calls = tool_calls_match.group(1).strip()
            tool_calls = json.loads(tool_calls)
        
        tool_plan = ""
        cleaned_response = model_response   
        tool_plan_match = re.search(tool_plan_pattern, model_response, re.DOTALL)
        if tool_plan_match:
            tool_plan = tool_plan_match.group(1).strip()
            cleaned_response = re.sub(tool_plan_pattern, "", model_response, flags=re.DOTALL)
        
        if len(tool_calls):
            chat_history = {
                "role": "assistant",
                "tool_calls": self._convert_to_tool_calls(tool_calls),
                "tool_plan": tool_plan
            }
        else:
            chat_history = {
                "role": "assistant",
                "content": cleaned_response,
            }
        
        return {
            "model_responses": cleaned_response,
            "tool_calls": tool_calls,
            "tool_plan": tool_plan,
            "chat_history": chat_history,
            "input_token": api_response.usage.prompt_tokens,
            "output_token": api_response.usage.completion_tokens,
        }
    
    @override
    def _add_assistant_message_prompting(
        self, inference_data: dict, model_response_data: dict
    ) -> dict:
        inference_data["message"].append(
            model_response_data["chat_history"]
        )
        return inference_data
    
    @override
    def _add_execution_results_prompting(
        self, inference_data: dict, execution_results: list[str], model_response_data: dict
    ) -> dict:
        tool_call_messages = []
        for tool_call, execution_result in zip(
            inference_data["message"][-1]["tool_calls"], execution_results
        ):
            tool_call_messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": execution_result,
                }
            )
        inference_data["message"].extend(tool_call_messages)
        return inference_data
        

    @override
    def decode_ast(self, result, language="Python"):
        """
        Decode the model's response into AST format.
        
        The response format is:
        '<|START_THINKING|>...<|END_THINKING|><|START_ACTION|>[{"tool_call_id": "0", "tool_name": "func_name", "parameters": {...}}]<|END_ACTION|>'
        """
        try:
            # Extract the JSON array from between START_ACTION and END_ACTION tags
            action_match = re.search(r"<\|START_ACTION\|>(.*?)<\|END_ACTION\|>", result, re.DOTALL)
            if not action_match:
                return []
            
            tool_calls_str = action_match.group(1).strip()
            tool_calls = json.loads(tool_calls_str)
            
            # Ensure tool_calls is a list
            if not isinstance(tool_calls, list):
                tool_calls = [tool_calls]
            
            # Convert to required format: [{func_name: parameters}]
            decoded_output = []
            for tool_call in tool_calls:
                name = tool_call["tool_name"]
                params = tool_call["parameters"]
                decoded_output.append({name: params})
            
            return decoded_output
        except (json.JSONDecodeError, KeyError, IndexError):
            return []

    @override
    def decode_execute(self, result):
        """
        Convert the model's response into executable function calls.
        
        The response format is:
        '<|START_THINKING|>...<|END_THINKING|><|START_ACTION|>[{"tool_call_id": "0", "tool_name": "func_name", "parameters": {...}}]<|END_ACTION|>'
        """
        try:
            # Extract the JSON array from between START_ACTION and END_ACTION tags
            action_match = re.search(r"<\|START_ACTION\|>(.*?)<\|END_ACTION\|>", result, re.DOTALL)
            if not action_match:
                return []
            
            tool_calls_str = action_match.group(1).strip()
            tool_calls = json.loads(tool_calls_str)
            
            # Ensure tool_calls is a list
            if not isinstance(tool_calls, list):
                tool_calls = [tool_calls]
            
            # Convert to executable function calls
            execution_list = []
            for tool_call in tool_calls:
                name = tool_call["tool_name"]
                params = tool_call["parameters"]
                param_str = ",".join([f"{k}={repr(v)}" for k, v in params.items()])
                execution_list.append(f"{name}({param_str})")
            
            return execution_list
        except (json.JSONDecodeError, KeyError, IndexError):
            return []

    @override
    def _pre_query_processing_prompting(self, test_entry: dict) -> dict:
        """
        Pre-process the test entry for Cohere Command A.
        """
        functions: list = test_entry["function"]
        test_category: str = test_entry["id"].rsplit("_", 1)[0]

        functions = func_doc_language_specific_pre_processing(functions, test_category)

        return {"message": [], "function": functions} 