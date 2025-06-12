import inspect
import json

from bfcl_eval.constants.type_mappings import GORILLA_TO_OPENAPI
from bfcl_eval.model_handler.model_style import ModelStyle
from bfcl_eval.model_handler.local_inference.base_oss_handler import OSSHandler
from bfcl_eval.model_handler.utils import (
    convert_to_tool,
    func_doc_language_specific_pre_processing,
)
from overrides import override


class HermesHandler(OSSHandler):
    def __init__(self, model_name, temperature) -> None:
        super().__init__(model_name, temperature)
        # Only this specific Hermes model uses float16
        if model_name == "NousResearch/Hermes-2-Pro-Llama-3-8B":
            self.dtype = "float16"

    @override
    def _format_prompt(self, messages, function):
        # Hermes use Langchain to OpenAI conversion. It does not use tool call but function call.
        function = convert_to_tool(function, GORILLA_TO_OPENAPI, ModelStyle.OSSMODEL)
        pydantic_format = """{"properties": {"arguments": {"title": "Arguments", "type": "object"}, "name": {"title": "Name", "type": "string"}}, "required": ["arguments", "name"], "title": "FunctionCall", "type": "object"}"""
        tool_call_format = """{"arguments": <args-dict>, "name": <function-name>}"""
        formatted_prompt = inspect.cleandoc(
            """<|im_start|>system
            You are a function calling AI model. You are provided with function signatures within <tools></tools> XML tags. You may call one or more functions to assist with the user query. Don't make assumptions about what values to plug into functions. Here are the available tools:
            <tools>
            {function}
            </tools>
            Use the following pydantic model json schema for each tool call you will make:
            {pydantic_format}
            For each function call return a json object with function name and arguments within <tool_call></tool_call> XML tags as follows:
            <tool_call>
            {tool_call_format}
            </tool_call>
            <|im_end|>
            """
        )

        formatted_prompt = formatted_prompt.format(
            function=function,
            pydantic_format=pydantic_format,
            tool_call_format=tool_call_format,
        )

        for message in messages:
            formatted_prompt += (
                f"<|im_start|>{message['role']}\n{message['content']}<|im_end|>\n"
            )

        formatted_prompt += "<|im_start|>assistant\n"

        return formatted_prompt

    @override
    def decode_ast(self, result, language="Python"):
        lines = result.split("\n")
        flag = False
        func_call = []
        for line in lines:
            if "<tool_call>" == line:
                flag = True
            elif "</tool_call>" == line:
                flag = False
            else:
                if flag:
                    line = line.replace("'", '"')
                    tool_result = json.loads(line)
                    func_call.append({tool_result["name"]: tool_result["arguments"]})
                flag = False
        return func_call

    @override
    def decode_execute(self, result):
        lines = result.split("\n")
        flag = False
        function_call_list = []
        for line in lines:
            if "<tool_call>" == line:
                flag = True
            elif "</tool_call>" == line:
                flag = False
            else:
                if flag:
                    line = line.replace("'", '"')
                    tool_result = json.loads(line)
                    function_call_list.append(
                        {tool_result["name"]: tool_result["arguments"]}
                    )
                flag = False
        execution_list = []
        for function_call in function_call_list:
            for key, value in function_call.items():
                execution_list.append(
                    f"{key}({','.join([f'{k}={repr(v)}' for k,v in value.items()])})"
                )
        return execution_list

    @override
    def _pre_query_processing_prompting(self, test_entry: dict) -> dict:
        functions: list = test_entry["function"]
        test_category: str = test_entry["id"].rsplit("_", 1)[0]

        functions = func_doc_language_specific_pre_processing(functions, test_category)

        # Hermes use its own system prompt

        return {"message": [], "function": functions}

    @override
    def _add_execution_results_prompting(
        self, inference_data: dict, execution_results: list[str], model_response_data: dict
    ) -> dict:
        for execution_result, decoded_model_response in zip(
            execution_results, model_response_data["model_responses_decoded"]
        ):
            hermes_response_object = {
                "name": decoded_model_response,
                "content": execution_result,
            }
            inference_data["message"].append(
                {
                    "role": "tool",
                    "content": f"<tool_response>\n{hermes_response_object}\n</tool_response>\n",
                }
            )

        return inference_data
