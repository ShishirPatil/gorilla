import json
from bfcl.model_handler.oss_handler import OSSHandler
from bfcl.model_handler.utils import ast_parse
from bfcl.model_handler.utils import (
    ast_parse,
    _get_language_specific_hint
)


SYSTEM_PROMPT = """You are an expert in composing functions. You are given a question and a set of possible functions. 
Based on the question, you will need to make one or more function/tool calls to achieve the purpose. 
If none of the function can be used, point it out. If the given question lacks the parameters required by the function,
also point it out.
"""

TOOL_PROMPT = """Here is a list of functions in JSON format that you can invoke:\n{functions}.
Should you decide to return the function call(s). \nPut it in the format of [func1(params_name=params_value, params_name2=params_value2...), func2(params)]\n
NO other text MUST be included.
"""

class ToolACEHandler(OSSHandler):
    def __init__(self, model_name, temperature=0.001, top_p=1, max_tokens=1024) -> None:
        super().__init__(model_name, temperature, top_p, max_tokens)

    def _format_prompt(prompts, function, test_category):

        formatted_prompt = "<|begin_of_text|>"

        for prompt in prompts:
            formatted_prompt += f"<|start_header_id|>{prompt['role']}<|end_header_id|>\n\n{prompt['content']}<|eot_id|>"

        formatted_prompt += f"<|start_header_id|>assistant<|end_header_id|>\n\n"

        return formatted_prompt


    @staticmethod
    def system_prompt_pre_processing(prompts, system_prompt_template, function_docs):
        assert type(prompts) == list

        system_prompt = system_prompt_template.format(functions=function_docs)

        # System prompt must be in the first position
        # If the question comes with a system prompt, append its content at the end of the chat template.
        if prompts[0]["role"] == "system":
            prompts[0]["content"] = system_prompt + prompts[0]["content"]
        # Otherwise, use the system prompt template to create a new system prompt.
        else:
            prompts.insert(
                0,
                {"role": "system", "content": system_prompt},
            )

        return prompts


    @staticmethod
    def func_doc_language_specific_pre_processing(function, test_category):
        if len(function) == 0:
            return function

        assert type(function) == list
        for item in function:
            # Add language specific hints to the function description
            item["description"] = item["description"]
            # Process the parameters
            properties = item["parameters"]["properties"]
            if test_category == "java":
                for key, value in properties.items():
                    if value["type"] == "any":
                        properties[key]["description"] += (
                            " This parameter can be of any type of Java object in string representation."
                        )
                    else:
                        value["description"] += (
                            f" This is Java {value['type']} type parameter in string representation."
                        )
                    if value["type"] == "ArrayList" or value["type"] == "Array":
                        value["description"] += (
                            f" The list elements are of type {value['items']['type']}; they are not in string representation."
                        )
                        del value["items"]
                        
                    value["type"] = "string"
                    
            elif test_category == "javascript":
                for key, value in properties.items():
                    if value["type"] == "any":
                        properties[key]["description"] += (
                            " This parameter can be of any type of JavaScript object in string representation."
                        )
                    else:
                        value["description"] += (
                            f" This is JavaScript {value['type']} type parameter in string representation."
                        )
                    if value["type"] == "array":
                        value["description"] += (
                            f" The list elements are of type {value['items']['type']}; they are not in string representation."
                        )
                        del value["items"]
                    
                    if value["type"] == "dict":
                        if "properties" in value:    # not every dict has properties
                            value["description"] += (
                                f" The dictionary entries have the following schema; they are not in string representation. {json.dumps(value['properties'])}"
                            )
                            del value["properties"]

                    value["type"] = "string"
                    
        return function
    
    @staticmethod
    def process_input(
        test_question,
        format_prompt_func,
        include_system_prompt=True
    ):
        prompts = []
        for question in test_question:
            test_category = question["id"].rsplit("_", 1)[0]
            functions = ToolACEHandler.func_doc_language_specific_pre_processing(
                question["function"], test_category
            )
            # prompt here is a list of dictionaries, one representing a role and content
            if include_system_prompt:
                question["question"] = ToolACEHandler.system_prompt_pre_processing(
                    question["question"], 
                    f"{SYSTEM_PROMPT}\n{TOOL_PROMPT}",
                    function_docs=functions
                )

            language_hint = _get_language_specific_hint(test_category)
            question["question"][-1]["content"] += f"\n{language_hint}"

            prompts.append(format_prompt_func(question["question"], functions, test_category))
        return prompts

    def inference(
        self,
        test_question,
        num_gpus,
        gpu_memory_utilization,
        format_prompt_func=_format_prompt,
        max_model_len=None,
        include_system_prompt=True
    ):
        return super().inference(
            test_question,
            num_gpus,
            gpu_memory_utilization=0.7,
            format_prompt_func=format_prompt_func,
            include_system_prompt=include_system_prompt,
            max_model_len=max_model_len
        )

    def decode_ast(self, result, language="Python"):
        func = result
        func = func.replace("\n", "")  # remove new line characters
        if not func.startswith("["):
            func = "[" + func
        if not func.endswith("]"):
            func = func + "]"
        decoded_output = ast_parse(func, language)
        return decoded_output

    def decode_execute(self, result):
        func = result
        func = func.replace("\n", "")  # remove new line characters
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
