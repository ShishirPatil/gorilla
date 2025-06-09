import json
import re
from bfcl.model_handler.api_inference.nvidia import NvidiaHandler
from bfcl.model_handler.utils import (
    ast_parse,
    combine_consecutive_user_prompts,
    func_doc_language_specific_pre_processing,
)

class NemotronHandler(NvidiaHandler):
    def __init__(self, model_name, temperature) -> None:
        super().__init__(model_name, temperature)

    def _format_system_prompt(self, functions):
        """Format the system prompt in the Nemotron-specific format."""
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
        functions: list = test_entry["function"]
        test_category: str = test_entry["id"].rsplit("_", 1)[0]

        functions = func_doc_language_specific_pre_processing(functions, test_category)

        # Create system prompt with Nemotron-specific format
        system_prompt = self._format_system_prompt(functions)
        
        # Add system prompt to the first message
        if test_entry["question"][0]["role"] == "system":
            test_entry["question"][0]["content"] = system_prompt
        else:
            test_entry["question"].insert(0, {"role": "system", "content": system_prompt})

        # Combine consecutive user prompts
        for round_idx in range(len(test_entry["question"])):
            test_entry["question"][round_idx] = combine_consecutive_user_prompts(
                test_entry["question"][round_idx]
            )

        return {"message": []}

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