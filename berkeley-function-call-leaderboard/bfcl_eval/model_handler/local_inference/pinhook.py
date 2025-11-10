import json
import re
from typing import Any

from bfcl_eval.model_handler.local_inference.base_oss_handler import OSSHandler
from bfcl_eval.model_handler.utils import convert_to_function_call
from overrides import override


class PinHookHandler(OSSHandler):
    def __init__(self, model_name, temperature = 0.3) -> None:
        super().__init__(model_name, temperature)
        self.temperature = 0.3
        self.is_fc_model = True
        self.stop_token_ids = [151937, 151645]
        self.skip_special_tokens = False
        
    @override
    def decode_ast(self, result, language, has_tool_call_tag):
        function_call_list = self._extract_tool_calls(result)
        return function_call_list

    @override
    def decode_execute(self, result, has_tool_call_tag):
        function_call_list = self._extract_tool_calls(result)
        execution_list = []
        for function_call in function_call_list:
            for key, value in function_call.items():
                if type(value) == str:
                    value = json.loads(value)
                execution_list.append(
                    f"{key}({','.join([f'{k}={repr(v)}' for k,v in value.items()])})"
                )

        return execution_list
    @override
    def _format_prompt(self, messages, function):
        SYSTEM_PROMPT = """You are a professional function calling assistant.
You are provided with function signatures within <reference_api_start><reference_api_end> tags.

##API 
<reference_api_start>
{}
<reference_api_end>

##Task
You will receive a **user query** which is a natural language query from the user

Your job is to:
1. **Strictly** identify and understand the user’s intent from the query.
2. **Strictly follow the API documentation** to determine:
   - The exact `api_name` (function name) exactly as given in the documentation.
   - The required and optional parameters, using parameter names exactly as defined in the documentation.
3. Generate **one or more complete and executable function calls** using the correct function name and all required parameters.  
   - Do **not** create parameters or functions not present in the documentation.  
   - Ensure parameter keys are spelled exactly as in the API documentation.

## Output Format
Only return the complete function call(s), wrapped using the following format:

<function>[API_CALL]{{function_name}}[PARAM_CALL]{{"{{parameter_key}}": "{{value}}", ...}}[API_CALL]{{function_name}}[PARAM_CALL]{{"{{parameter_key}}": "{{value}}", ...}}</function>

### Tag Definitions:
- `[API_CALL]`: A special marker indicating that the following token sequence is the name of the function to be called. It helps group potentially multi-token function names as a single semantic unit.
- `[PARAM_CALL]`: A special marker indicating the beginning of the parameter list. This allows the model to distinguish between the function name and its arguments.
- `<function>...</function>`: Encloses the complete function call or multiple function calls.
- `<response>...</response>`: Encloses the execution results of function call or multiple function calls.

"""
        def convert_api_doc(api: dict) -> str:
            
            if "Note that the provided function is in" in api["description"]:
                api["description"] = api["description"].rsplit("Note that the provided function", 1)[0]

            params = []
            props = api["parameters"].get("properties", {})
            required = set(api["parameters"].get("required", []))

            for pname, pinfo in props.items():
                ptype = pinfo.get("type", "unknown")
                desc = pinfo.get("description", "")
                if ptype == "array":
                    item_type = pinfo.get("items", {}).get("type", "any")
                    enum_vals = pinfo.get("items", {}).get("enum")
                    if enum_vals:
                        desc += f" (Allowed values: {', '.join(enum_vals)})"
                    ptype = f"array[{item_type}]"

                params.append({
                    "parameter_name": pname,
                    "parameter_type": ptype,
                    "parameter_description": desc,
                    "is_required": pname in required
                })
            
            api_repr = (
                f"## API: `bfcl.{api['name']}`\n\n"
                f"**Description:** {api['description']}\n\n"
                f"### Parameters:\n"
                + "\n".join(
                    f"- **{p['parameter_name']}**\n"
                    f"  - Type: `{p['parameter_type']}`\n"
                    f"  - Description: {p['parameter_description']}\n"
                    f"  - Required: {p['is_required']}\n"
                    for p in params
                )
            )
            return api_repr

        assert isinstance(function, list)
        json_docs = []
        for func in function:
            json_doc = convert_api_doc(func)
            json_docs.append(json_doc)
        api_doc = ",".join(json_docs)
        
        formatted_prompt = "<|im_start|>system\n"
        if messages[0]["role"] == "system":
            formatted_prompt += messages[0]["content"] + "\n\n"
        formatted_prompt +=  SYSTEM_PROMPT.format(api_doc) + "<|im_end|>\n"
    
        for i in range(len(messages)):
            sentence_value = ""
            sentence = messages[i]
            sentence_role = sentence["role"].lower()
            
            if sentence_role == 'user':
                sentence_value = f'<|im_start|>user\n{sentence["content"]}<|im_end|>\n'
                sentence_value += f'<|im_start|>assistant\n'
            if sentence_role == 'assistant':
                sentence_value = f'<function>{sentence["content"]}</function>'
            if sentence_role == 'tool':
                sentence_value = f'<response>{sentence["content"]}</response>'
                if i+1 < len(messages) and messages[i+1]["role"] == "user":
                    sentence_value += "<|im_end|>"

            formatted_prompt += sentence_value
                
        return formatted_prompt

    @override
    def _pre_query_processing_prompting(self, test_entry: dict) -> dict:
        functions: list = test_entry["function"]

        # FC models use its own system prompt, so no need to add any message

        return {"message": [], "function": functions}

    @override
    def _parse_query_response_prompting(self, api_response: Any) -> dict:

        model_response = api_response.choices[0].text 
        model_response = model_response.split("<function>")[-1]
        return {
                "model_responses": model_response,
                "input_token": api_response.usage.prompt_tokens,
                "output_token": api_response.usage.completion_tokens,
            }

    @override
    def _add_assistant_message_prompting(
        self, inference_data: dict, model_response_data: dict
    ) -> dict:
        if model_response_data["model_responses"] == "":
            return inference_data
        inference_data["message"].append(
            {
                "role":"assistant", 
                "content":model_response_data["model_responses"]
            }
        )
        return inference_data

    @override
    def _add_execution_results_prompting(
        self, inference_data: dict, execution_results: list[str], model_response_data: dict
    ) -> dict:
        all_execution_result = json.dumps(execution_results, ensure_ascii = False)
        inference_data["message"].append(
            {
                "role": "tool",
                "content": all_execution_result
            }
        )

        return inference_data
    @staticmethod
    def _extract_tool_calls(input_string):
        pred_assis = input_string
        if pred_assis == "" or pred_assis == "<|im_end|>":
            return []

        pred_func_string = pred_assis.split("<function>")[-1].split("</function>")[0]
        pred_func_results = []
        
        if "[API_CALL]" in pred_func_string:
            pred_func_results = pred_func_string.split("[API_CALL]")[1:] 
        
        actions = []
        for pred_func in pred_func_results:
            func_name = pred_func.split("[PARAM_CALL]")[0].strip()
            params = pred_func.split("[PARAM_CALL]")[1].strip()
            try:
                params = json.loads(params.strip())
            except:
                params = params
            func_name = func_name.split("bfcl.", 1)[-1]
            actions.append({func_name:params})
        return actions
