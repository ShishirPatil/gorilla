from typing import Any
import os

from bfcl.model_handler.model_style import ModelStyle
from bfcl.model_handler.api_inference.openai import OpenAIHandler
from bfcl.model_handler.utils import (
    ast_parse,
    combine_consecutive_user_prompts,
    func_doc_language_specific_pre_processing,
    system_prompt_pre_processing_chat_model,
)
from openai import OpenAI


class NvidiaHandler(OpenAIHandler):
    """
    A handler for NVIDIA's API that extends OpenAIHandler to provide specific functionality for NVIDIA's API endpoints. This class handles model interactions, AST parsing, and query processing for NVIDIA's API.
    """
    def __init__(self, model_name: str, temperature: float) -> None:
        super().__init__(model_name, temperature)
        self.model_style = ModelStyle.OpenAI
        self.client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=os.getenv("NVIDIA_API_KEY"),
        )

    def decode_ast(self, result: str, language: str="Python"):
        """
        Parses the given result string into an abstract syntax tree (AST) representation for the specified programming language. The method performs string manipulation to ensure the result is in a valid format before parsing.
        
        Args:
            result (str): The string result to parse into an AST
            language (str, optional): The programming language of the result. Defaults to "Python".
        
        Returns:
            The parsed AST representation of the result
        """
        result = result.replace("\n", "")
        if not result.startswith("["):
            result = "[" + result
        if not result.endswith("]"):
            result = result + "]"
        if result.startswith("['"):
            result = result.replace("['", "[")
            result = result.replace("', '", ", ")
            result = result.replace("','", ", ")
        if result.endswith("']"):
            result = result.replace("']", "]")
        decode_output = ast_parse(result, language)
        return decode_output

    def decode_execute(self, result: str, language: str="Python") -> list[str]:
        """
        Parses the given result string into executable function calls for the specified programming language. Similar to decode_ast but returns executable strings rather than the AST representation.
        
        Args:
            result (str): The string result to parse into executable calls
            language (str, optional): The programming language of the result. Defaults to "Python".
        
        Returns:
            list[str]: A list of executable function call strings
        """
        result = result.replace("\n", "")
        if not result.startswith("["):
            result = "[" + result
        if not result.endswith("]"):
            result = result + "]"
        if result.startswith("['"):
            result = result.replace("['", "[")
            result = result.replace("', '", ", ")
            result = result.replace("','", ", ")
        if result.endswith("']"):
            result = result.replace("']", "]")
        decode_output = ast_parse(result, language)
        execution_list = []
        for function_call in decode_output:
            for key, value in function_call.items():
                execution_list.append(
                    f"{key}({','.join([f'{k}={repr(v)}' for k, v in value.items()])})"
                )
        return execution_list

    #### Prompting methods ####

    def _pre_query_processing_prompting(self, test_entry: dict) -> dict:
        """
        Pre-processes test queries before sending them to the model. Handles function documentation processing and combines consecutive user prompts.
        
        Args:
            test_entry (dict): The test entry containing questions and functions to process
        
        Returns:
            dict: A dictionary containing processed messages (currently returns empty message list)
        """
        functions: list = test_entry["function"]
        test_category: str = test_entry["id"].rsplit("_", 1)[0]

        functions = func_doc_language_specific_pre_processing(functions, test_category)

        test_entry["question"][0] = system_prompt_pre_processing_chat_model(
            test_entry["question"][0], functions, test_category
        )

        for round_idx in range(len(test_entry["question"])):
            test_entry["question"][round_idx] = combine_consecutive_user_prompts(
                test_entry["question"][round_idx]
            )

        return {"message": []}
