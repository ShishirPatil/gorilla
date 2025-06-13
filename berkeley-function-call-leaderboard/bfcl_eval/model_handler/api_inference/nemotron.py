import json
import re
from bfcl.model_handler.api_inference.nvidia import NvidiaHandler
from bfcl.model_handler.utils import (
    ast_parse,
    func_doc_language_specific_pre_processing,
)

class NemotronHandler(NvidiaHandler):
    """Handler for the LLaMA 3.1 Nemotron Ultra 253B v1 model.
    
    This handler extends NvidiaHandler to support the Nemotron model's XML-based
    function calling format. The model expects:
    - <TOOLCALL>[function_calls]</TOOLCALL> for function calls
    - <AVAILABLE_TOOLS>{functions}</AVAILABLE_TOOLS> for function documentation
    """

    def _format_system_prompt(self, functions):
        """Format the system prompt in the Nemotron-specific XML format."""
        system_prompt = """You are an expert in composing functions. You are given a question and a set of possible functions.
Based on the question, you will need to make one or more function/tool calls to achieve the purpose.
If none of the function can be used, point it out. If the given question lacks the parameters required by the function,
also point it out. You should only return the function call in tools call sections.

If you decide to invoke any of the function(s), you MUST put it in the format of <TOOLCALL>[func_name1(params_name1=params_value1, params_name2=params_value2...), func_name2(params)]</TOOLCALL>

You SHOULD NOT include any other text in the response.

Here is a list of functions in JSON format that you can invoke.

<AVAILABLE_TOOLS>{functions}</AVAILABLE_TOOLS>"""
        return system_prompt.format(functions=json.dumps(functions, indent=2))

    def _pre_query_processing_prompting(self, test_entry: dict) -> dict:
        """Process the input query and format it for the Nemotron model."""
        functions: list = test_entry["function"]
        test_category: str = test_entry["id"].rsplit("_", 1)[0]

        # Pre-process functions based on language
        functions = func_doc_language_specific_pre_processing(functions, test_category)

        # Create system prompt with Nemotron-specific format
        system_prompt = self._format_system_prompt(functions)
        
        # Return empty message list - messages will be added incrementally
        return {"message": [], "system_prompt": system_prompt}

    def add_first_turn_message_prompting(
        self, inference_data: dict, first_turn_message: list[dict]
    ) -> dict:
        """Add the first turn message to the inference data."""
        if "message" not in inference_data:
            inference_data["message"] = []
        
        # Add our custom system prompt first
        if "system_prompt" in inference_data:
            inference_data["message"].append({
                "role": "system",
                "content": inference_data["system_prompt"]
            })
            del inference_data["system_prompt"]
        
        # Add all other messages
        for msg in first_turn_message:
            if msg["role"] != "system":  # Skip system messages as we've already added ours
                inference_data["message"].append(msg)
        
        return inference_data

    def decode_ast(self, result, language="Python"):
        """Extract function calls from the Nemotron XML format."""
        # Extract content between TOOLCALL tags
        toolcall_match = re.search(r'<TOOLCALL>(.*?)</TOOLCALL>', result, re.DOTALL)
        if not toolcall_match:
            return []
        
        # Get the function call string
        func_call_str = toolcall_match.group(1).strip()
        
        # Parse the function calls
        if not func_call_str.startswith("["):
            func_call_str = "[" + func_call_str
        if not func_call_str.endswith("]"):
            func_call_str = func_call_str + "]"
            
        return ast_parse(func_call_str, language)

    def decode_execute(self, result, language="Python"):
        """Convert Nemotron response to executable function calls."""
        decoded_output = self.decode_ast(result, language)
        execution_list = []
        for function_call in decoded_output:
            for key, value in function_call.items():
                execution_list.append(
                    f"{key}({','.join([f'{k}={repr(v)}' for k, v in value.items()])})"
                )
        return execution_list 