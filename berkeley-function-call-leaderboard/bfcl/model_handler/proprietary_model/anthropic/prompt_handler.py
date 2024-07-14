import os
import time

from anthropic import Anthropic

from bfcl.model_handler import utils
from bfcl.model_handler import constants
from bfcl.model_handler.base import BaseHandler, ModelStyle


class AnthropicPromptHandler(BaseHandler):
    model_style = ModelStyle.ANTHROPIC_PROMPT
    
    def __init__(self, model_name, temperature=0.7, top_p=1, max_tokens=1000) -> None:
        super().__init__(model_name, temperature, top_p, max_tokens)
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    @classmethod
    def supported_models(cls):
        return [
            'claude-instant-1.2',
            'claude-2.1',
            'claude-3-opus-20240229',
            'claude-3-sonnet-20240229',
            'claude-3-5-sonnet-20240620',
            'claude-3-haiku-20240307',
        ]

    def inference(self, prompt, functions, test_category):
        prompt = utils.augment_prompt_by_languge(prompt, test_category)
        if "FC" in self.model_name:
            functions = utils.language_specific_pre_processing(functions, test_category, True)
            result, metadata = self._get_claude_function_calling_response(
                prompt, functions, test_category
            )
            return result, metadata
        else:
            start = time.time()
            functions = utils.language_specific_pre_processing(functions, test_category, False)
            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                top_p=self.top_p,
                system=constants.SYSTEM_PROMPT_FOR_CHAT_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": constants.USER_PROMPT_FOR_CHAT_MODEL.format(user_prompt=prompt, 
                                                                               functions=str(functions)),
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

    def decode_ast(self, result, language="python"):
        if "FC" in self.model_name:
            if language.lower() == "python":
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
            decode_output = utils.ast_parse(func, language)
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
            decode_output = utils.ast_parse(func)
            execution_list = []
            for function_call in decode_output:
                for key, value in function_call.items():
                    execution_list.append(
                        f"{key}({','.join([f'{k}={repr(v)}' for k, v in value.items()])})"
                    )
            return execution_list

    def _get_claude_function_calling_response(self, prompt, functions, test_category):
        input_tool = utils.convert_to_tool(
            functions, constants.GORILLA_TO_PYTHON, self.model_style, test_category, True
        )
        system_prompt = utils.construct_tool_use_system_prompt(input_tool)
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
        out = utils.function_calls_valid_format_and_invoke_extraction(response.content[0].text)
        if "invokes" not in out.keys():
            return "Error", {"input_tokens": 0, "output_tokens": 0, "latency": latency}
        for invoked_function in out["invokes"]:
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
                param_value = utils.convert_value(param_value, param_type)
                param_dict[param_name] = param_value
            result.append({name: param_dict})
        metadata = {}
        metadata["input_tokens"] = response.usage.input_tokens
        metadata["output_tokens"] = response.usage.output_tokens
        metadata["latency"] = latency
        return result, metadata
