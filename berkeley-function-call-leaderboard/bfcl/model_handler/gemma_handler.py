from bfcl.model_handler.oss_handler import OSSHandler
from bfcl.model_handler.utils import ast_parse
import re


class GemmaHandler(OSSHandler):
    def __init__(self, model_name, temperature=0.7, top_p=1, max_tokens=1000) -> None:
        super().__init__(model_name, temperature, top_p, max_tokens)

    def _format_prompt(prompt, function, test_category):
        formatted_prompt = """
            <bos><start_of_turn>user\n
            You are an helpful assistant who has access to the following functions to help the user, you can use the functions if needed-\n
            {function}\n
            Here is the questions you need to answer:\n
            {prompt}\n
            Your job is to solve the above question using ONLY and strictly ONE line of python code given the above functions. If you think no function should be invoked return "[]".\n
            If you think one or more function should be invoked, return the function call in the format of [func1(params_name=params_value, params_name2=params_value2...), func2(params)] wrapped in python code"
            <end_of_turn>\n
            <start_of_turn>model\n
        """
        return formatted_prompt.format(function=function, prompt=prompt)

    def inference(
        self, test_question, num_gpus, gpu_memory_utilization, format_prompt_func=_format_prompt
    ):
        return super().inference(
            test_question, num_gpus, gpu_memory_utilization, format_prompt_func=format_prompt_func
        )

    def decode_ast(self, result, language="Python"):
        pattern = r"\[(.*)\]"

        # Searching for the pattern in the input text
        match = re.search(pattern, result, re.DOTALL)
        raw_input = match.group(1)
        func = "[" + raw_input + "]"
        decoded_output = ast_parse(func, language=language)
        return decoded_output

    def decode_execute(self, result):
        pattern = r"\[(.*)\]"

        # Searching for the pattern in the input text
        match = re.search(pattern, result, re.DOTALL)
        raw_input = match.group(1)
        func = "[" + raw_input + "]"
        decoded_output = ast_parse(func)
        execution_list = []
        for function_call in decoded_output:
            for key, value in function_call.items():
                execution_list.append(
                    f"{key}({','.join([f'{k}={repr(v)}' for k, v in value.items()])})"
                )
        return execution_list
