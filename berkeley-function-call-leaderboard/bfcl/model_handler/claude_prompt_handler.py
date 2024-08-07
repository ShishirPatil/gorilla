from bfcl.model_handler.handler import BaseHandler
from bfcl.model_handler.model_style import ModelStyle
from bfcl.model_handler.utils import (
    convert_to_tool,
    ast_parse,
    augment_prompt_by_languge,
    language_specific_pre_processing,
    construct_tool_use_system_prompt,
    _function_calls_valid_format_and_invoke_extraction,
    _convert_value,
)
from bfcl.model_handler.constant import (
    SYSTEM_PROMPT_FOR_CHAT_MODEL,
    USER_PROMPT_FOR_CHAT_MODEL,
    GORILLA_TO_PYTHON,
)
import os, time
from anthropic import Anthropic


class ClaudePromptingHandler(BaseHandler):
    def __init__(self, model_name, temperature=0.7, top_p=1, max_tokens=1000) -> None:
        super().__init__(model_name, temperature, top_p, max_tokens)
        self.model_style = ModelStyle.Anthropic_Prompt

        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    def _get_claude_function_calling_response(self, prompt, functions, test_category):
        input_tool = convert_to_tool(
            functions, GORILLA_TO_PYTHON, self.model_style, test_category
        )
        system_prompt = construct_tool_use_system_prompt(input_tool)
        start = time.time()
        response = self.client.messages.create(
            model=self.model_name.strip("-FC"),
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            top_p=self.top_p,
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}],
        )
        latency = time.time() - start
        result = []
        if (
            "invokes"
            not in _function_calls_valid_format_and_invoke_extraction(
                response.content[0].text
            ).keys()
        ):
            return "Error", {"input_tokens": 0, "output_tokens": 0, "latency": latency}
        for invoked_function in _function_calls_valid_format_and_invoke_extraction(
            response.content[0].text
        )["invokes"]:
            name = invoked_function["tool_name"]
            select_func = None
            for func in input_tool:
                if func["name"] == name:
                    select_func = func
                    break
            if select_func is None:
                result.append({})
                continue
            param_dict = {}
            for param in invoked_function["parameters_with_values"]:
                param_name = param[0]
                param_value = param[1]
                try:
                    param_type = select_func["parameters"]["properties"][param_name][
                        "type"
                    ]
                except:
                    param_type = "str"
                param_value = _convert_value(param_value, param_type)
                param_dict[param_name] = param_value
            result.append({name: param_dict})
        metadata = {}
        metadata["input_tokens"] = response.usage.input_tokens
        metadata["output_tokens"] = response.usage.output_tokens
        metadata["latency"] = latency
        return result, metadata

    def inference(self, prompt, functions, test_category):
        prompt = augment_prompt_by_languge(prompt, test_category)
        if "FC" in self.model_name:
            functions = language_specific_pre_processing(functions, test_category)
            result, metadata = self._get_claude_function_calling_response(
                prompt, functions, test_category
            )
            return result, metadata
        else:
            start = time.time()
            functions = language_specific_pre_processing(
                functions, test_category
            )
            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                top_p=self.top_p,
                system=SYSTEM_PROMPT_FOR_CHAT_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": USER_PROMPT_FOR_CHAT_MODEL.format(
                            user_prompt=prompt, functions=str(functions)
                        ),
                    }
                ],
            )
            latency = time.time() - start
            metadata = {}
            metadata["input_tokens"] = response.usage.input_tokens
            metadata["output_tokens"] = response.usage.output_tokens
            metadata["latency"] = latency
            result = response.content[0].text
        return result, metadata

    def decode_ast(self, result, language="Python"):
        if "FC" in self.model_name:
            if language == "Python":
                return result
            else:
                # result is a list of dictionaries, make sure each value of dictionary is string
                for function_call in result:
                    for key, value in function_call.items():
                        for k, v in value.items():
                            value[k] = str(v)
                return result
        else:
            func = result
            if " " == func[0]:
                func = func[1:]
            if not func.startswith("["):
                func = "[" + func
            if not func.endswith("]"):
                func = func + "]"
            decode_output = ast_parse(func, language)
            return decode_output

    def decode_execute(self, result):
        if "FC" in self.model_name:
            if type(result) == dict:
                function_call_list = [result]
            else:
                function_call_list = result
            execution_list = []
            for function_call in function_call_list:
                for key, value in function_call.items():
                    execution_list.append(
                        f"{key}({','.join([f'{k}={repr(v)}' for k,v in value.items()])})"
                    )
            return execution_list
        else:
            func = result
            if " " == func[0]:
                func = func[1:]
            if not func.startswith("["):
                func = "[" + func
            if not func.endswith("]"):
                func = func + "]"
            decode_output = ast_parse(func)
            execution_list = []
            for function_call in decode_output:
                for key, value in function_call.items():
                    execution_list.append(
                        f"{key}({','.join([f'{k}={repr(v)}' for k, v in value.items()])})"
                    )
            return execution_list
