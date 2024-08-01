from bfcl.model_handler.oss_handler import OSSHandler
from bfcl.model_handler.utils import convert_to_function_call, ast_parse
import re


class DeepseekHandler(OSSHandler):
    def __init__(self, model_name, temperature=0.7, top_p=1, max_tokens=1000) -> None:
        super().__init__(model_name, temperature, top_p, max_tokens)

    def _format_prompt(prompt, function, test_category):
        formatted_prompt = """
            You are an AI programming assistant, utilizing the DeepSeek Coder model, developed by DeepSeek Company, and you only answer questions related to computer science. For politically sensitive questions, security and privacy issues, and other non-computer science questions, you will refuse to answer.\n
            ### Instruction:\n
            You are an helpful assistant who has access to the following functions to help the user, you can use the functions if needed-\n
            {function}\n
            Here is the question: {prompt}\n
            Your job is to solve the above question using ONLY and strictly ONE line of python code given the above functions. If you think no function should be invoked return "[]".\n
            If you think one or more function should be invoked, return the function call in the format of [func1(params_name=params_value, params_name2=params_value2...), func2(params)] wrapped in python code"
            ### Response:\n
        """
        return formatted_prompt.format(function=function, prompt=prompt)

    def inference(
        self, test_question, num_gpus, gpu_memory_utilization, format_prompt_func=_format_prompt
    ):
        return super().inference(
            test_question, num_gpus, gpu_memory_utilization, format_prompt_func=format_prompt_func
        )

    def decode_ast(self, result, language="Python"):
        function_call = result.split("```")[1]
        matches = re.findall(r"\[[^\]]*\]", function_call)
        decoded_output = ast_parse(matches[0], language)
        return decoded_output

    def decode_execute(self, result):
        function_call = result.split("```")[1]
        matches = re.findall(r"\[[^\]]*\]", function_call)
        decoded_output = ast_parse(matches[0])
        execution_list = []
        for function_call in decoded_output:
            for key, value in function_call.items():
                execution_list.append(
                    f"{key}({','.join([f'{k}={repr(v)}' for k, v in value.items()])})"
                )
        return execution_list
