import argparse
import json

from model_handler.oss_handler import OSSHandler
from model_handler.utils import ast_parse

FN_CALL_DELIMITER = "<<function>>"


def strip_function_calls(content: str) -> list[str]:
    """
    Split the content by the function call delimiter and remove empty strings
    """
    return [element.strip() for element in content.split(FN_CALL_DELIMITER)[1:] if element.strip()]


class OpenfunctionsHandler(OSSHandler):

    def __init__(self, model_name, temperature=0.7, top_p=1, max_tokens=1000) -> None:
        super().__init__(model_name, temperature, top_p, max_tokens)

    def _format_prompt(user_query: str, functions: list, test_category: str) -> str:
        """
        Generates a conversation prompt based on the user's query and a list of functions.

        Parameters:
        - user_query (str): The user's query.
        - functions (list): A list of functions to include in the prompt.
        - test_category (str): selected test category


        Returns:
        - str: The formatted conversation prompt.
        """
        system = "You are an AI programming assistant, utilizing the Gorilla LLM model, developed by Gorilla LLM, and you only answer questions related to computer science. For politically sensitive questions, security and privacy issues, and other non-computer science questions, you will refuse to answer."
        if len(functions) == 0:
            return f"{system}\n### Instruction: <<question>> {user_query}\n### Response: "
        functions_string = json.dumps(functions)
        return f"{system}\n### Instruction: <<function>>{functions_string}\n<<question>>{user_query}\n### Response: "

    def decode_ast(self, result, language="Python"):
        extracted_funcs = strip_function_calls(result)
        func = "[" + ",".join(extracted_funcs) + "]"
        decoded_output = ast_parse(func, language)
        return decoded_output

    def decode_execute(self, result):
        result = strip_function_calls(result)[0]
        func = "[" + result + "]"
        decoded_output = ast_parse(func)
        execution_list = []
        for function_call in decoded_output:
            for key, value in function_call.items():
                execution_list.append(
                    f"{key}({','.join([f'{k}={repr(v)}' for k, v in value.items()])})"
                )
        return execution_list

    def inference(
        self, question_file, test_category, num_gpus, format_prompt_func=_format_prompt
    ):
        return super().inference(
            question_file, test_category, num_gpus, format_prompt_func
        )
