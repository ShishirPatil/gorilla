from typing import Any
import os
import re
import time

from bfcl_eval.model_handler.api_inference.openai import OpenAIHandler
from bfcl_eval.model_handler.model_style import ModelStyle
from bfcl_eval.model_handler.utils import (
    ast_parse,
    combine_consecutive_user_prompts,
    func_doc_language_specific_pre_processing,
    system_prompt_pre_processing_chat_model,
)
from openai import OpenAI


class DatabricksHandler(OpenAIHandler):
    """
    A handler class for interacting with Databricks models through the OpenAI API interface. This class extends OpenAIHandler and provides specific implementations for Databricks model interactions.
    """
    def __init__(self, model_name: str, temperature: float) -> None:
        super().__init__(model_name, temperature)
        self.model_style = ModelStyle.OpenAI

        # NOTE: To run the Databricks model, you need to provide your own Databricks API key and your own Azure endpoint URL.
        self.client = OpenAI(
            api_key=os.getenv("DATABRICKS_API_KEY"),
            base_url=os.getenv("DATABRICKS_AZURE_ENDPOINT_URL"),
        )

    def decode_ast(self, result: str, language: str="Python"):
        """
        Parse and decode the AST (Abstract Syntax Tree) from the model's output string.
        
        Args:
            result (`str`):
                The raw string output from the model to be parsed
            language (`str`, optional):
                The programming language of the output (default: 'Python')
        
        Returns:
            The parsed AST output
        """
        func = re.sub(r"'([^']*)'", r"\1", result)
        func = func.replace("\n    ", "")
        if not func.startswith("["):
            func = "[" + func
        if not func.endswith("]"):
            func = func + "]"
        if func.startswith("['"):
            func = func.replace("['", "[")
        try:
            decode_output = ast_parse(func, language)
        except:
            decode_output = ast_parse(result, language)
        return decode_output

    def decode_execute(self, result: str, language: str="Python") -> list[str]:
        """
        Parse the model output into executable function calls.
        
        Args:
            result (`str`):
                The raw string output from the model
            language (`str`, optional):
                The programming language of the output (default: 'Python')
        
        Returns:
            `list[str]`: A list of executable function call strings
        """
        func = re.sub(r"'([^']*)'", r"\1", result)
        func = func.replace("\n    ", "")
        if not func.startswith("["):
            func = "[" + func
        if not func.endswith("]"):
            func = func + "]"
        if func.startswith("['"):
            func = func.replace("['", "[")
        try:
            decode_output = ast_parse(func, language)
        except:
            decode_output = ast_parse(result, language)
        execution_list = []
        for function_call in decode_output:
            for key, value in function_call.items():
                execution_list.append(
                    f"{key}({','.join([f'{k}={repr(v)}' for k, v in value.items()])})"
                )
        return execution_list

    #### Prompting methods ####

    def _query_prompting(self, inference_data: dict) -> tuple[Any, float]:
        """
        Send a query to the Databricks model and measure response time.
        
        Args:
            inference_data (`dict`):
                Dictionary containing the message to send to the model
        
        Returns:
            `tuple[Any, float]`: The API response and the time taken for the request
        """
        message = inference_data["message"]
        inference_data["inference_input_log"] = {"message": repr(inference_data["message"])}

        start_time = time.time()
        api_response = self.client.chat.completions.create(
            messages=message,
            model=self.model_name,
            temperature=self.temperature,
        )
        end_time = time.time()

        return api_response, end_time - start_time

    def _pre_query_processing_prompting(self, test_entry: dict) -> dict:
        """
        Pre-process test entries before sending to the Databricks model.
        
        Args:
            test_entry (`dict`):
                Dictionary containing test information and questions
        
        Returns:
            `dict`: Processed message dictionary ready for model input
        """
        functions: list = test_entry["function"]
        test_category: str = test_entry["id"].rsplit("_", 1)[0]

        functions = func_doc_language_specific_pre_processing(functions, test_category)

        test_entry["question"][0] = system_prompt_pre_processing_chat_model(
            test_entry["question"][0], functions, test_category
        )

        # Databricks doesn't allow consecutive user prompts, so we need to combine them
        for round_idx in range(len(test_entry["question"])):
            test_entry["question"][round_idx] = combine_consecutive_user_prompts(
                test_entry["question"][round_idx]
            )

        return {"message": []}
