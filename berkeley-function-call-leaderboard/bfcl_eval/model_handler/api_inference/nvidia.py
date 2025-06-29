from typing import Any
import os

from bfcl_eval.model_handler.model_style import ModelStyle
from bfcl_eval.model_handler.api_inference.openai import OpenAIHandler
from bfcl_eval.model_handler.utils import (
    ast_parse,
    combine_consecutive_user_prompts,
    func_doc_language_specific_pre_processing,
    system_prompt_pre_processing_chat_model,
)
from openai import OpenAI


class NvidiaHandler(OpenAIHandler):
    """
    A handler class for interacting with NVIDIA's API for model inference. Inherits from OpenAIHandler and provides additional functionality specific to NVIDIA's API.
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
        Parses and decodes the AST (Abstract Syntax Tree) from the model's output string for a given programming language.
        
        Args:
            result (`str`): The raw output string from the model
            language (`str`, optional): The programming language of the output (default: 'Python')
        
        Returns:
            The parsed AST output
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
        Parses the model's output string and generates executable function calls for a given programming language.
        
        Args:
            result (`str`): The raw output string from the model
            language (`str`, optional): The programming language of the output (default: 'Python')
        
        Returns:
            `list[str]`: A list of executable function call strings
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
        Pre-processes the test entry for querying the model, including function documentation processing and prompt combination.
        
        Args:
            test_entry (`dict`): The test case entry containing questions and functions
        
        Returns:
            `dict`: Processed message dictionary ready for model input
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
