import os
import time

import vertexai
from bfcl_eval.constants.type_mappings import GORILLA_TO_OPENAPI
from bfcl_eval.model_handler.base_handler import BaseHandler
from bfcl_eval.model_handler.model_style import ModelStyle
from bfcl_eval.model_handler.utils import (
    convert_to_tool,
    default_decode_ast_prompting,
    default_decode_execute_prompting,
    extract_system_prompt,
    format_execution_results_prompting,
    func_doc_language_specific_pre_processing,
    retry_with_backoff,
    system_prompt_pre_processing_chat_model,
)
from google.api_core.exceptions import ResourceExhausted, TooManyRequests
from vertexai.generative_models import (
    Content,
    FunctionDeclaration,
    GenerationConfig,
    GenerativeModel,
    Part,
    Tool,
)


class GeminiHandler(BaseHandler):
    """
    A handler class for interacting with Google's Gemini models, providing functionality for both function calling and standard prompting approaches. Inherits from BaseHandler.
    """
    def __init__(self, model_name: str, temperature: float) -> None:
        super().__init__(model_name, temperature)
        self.model_style = ModelStyle.Google
        # Initialize Vertex AI
        vertexai.init(
            project=os.getenv("VERTEX_AI_PROJECT_ID"),
            location=os.getenv("VERTEX_AI_LOCATION"),
        )
        self.client = GenerativeModel(self.model_name.replace("-FC", ""))

    @staticmethod
    def _substitute_prompt_role(prompts: list[dict]) -> list[dict]:
        """
        Converts standard chat roles (user/assistant/tool) to Gemini-specific roles (user/model/function).
        
        Args:
            prompts (list[dict]): List of prompt dictionaries with 'role' and 'content' keys
        
        Returns:
            list[dict]: Modified prompts with Gemini-compatible roles
        """
        # Allowed roles: user, model, function
        for prompt in prompts:
            if prompt["role"] == "user":
                prompt["role"] = "user"
            elif prompt["role"] == "assistant":
                prompt["role"] = "model"
            elif prompt["role"] == "tool":
                prompt["role"] = "function"

        return prompts

    def decode_ast(self, result: str, language: str="Python") -> list[dict] | str:
        """
        Decodes the abstract syntax tree from model output for function calling.
        
        Args:
            result (str): Raw model output
            language (str): Programming language of the output (default: 'Python')
        
        Returns:
            list[dict] | str: Parsed function calls or raw text output
        """
        if "FC" not in self.model_name:
            result = result.replace("```tool_code\n", "").replace("\n```", "")
            return default_decode_ast_prompting(result, language)
        else:
            if type(result) is not list:
                result = [result]
            return result

    def decode_execute(self, result: str | list[dict]) -> list[str]:
        """
        Decodes executable function calls from model output.
        
        Args:
            result (str | list[dict]): Raw model output or parsed function calls
        
        Returns:
            list[str]: Executable function call strings
        """
        if "FC" not in self.model_name:
            result = result.replace("```tool_code\n", "").replace("\n```", "")
            return default_decode_execute_prompting(result)
        else:
            func_call_list = []
            for function_call in result:
                for func_name, func_args in function_call.items():
                    func_call_list.append(
                        f"{func_name}({','.join([f'{k}={repr(v)}' for k, v in func_args.items()])})"
                    )
            return func_call_list

    @retry_with_backoff(error_type=[ResourceExhausted, TooManyRequests])
    def generate_with_backoff(self, client: GenerativeModel, **kwargs) -> tuple[any, float]:
        """
        Wrapper for model generation with exponential backoff on rate limits.
        
        Args:
            client (GenerativeModel): Gemini client instance
            **kwargs: Generation parameters
        
        Returns:
            tuple[any, float]: API response and execution time
        """
        start_time = time.time()
        api_response = client.generate_content(**kwargs)
        end_time = time.time()

        return api_response, end_time - start_time

    #### FC methods ####

    def _query_FC(self, inference_data: dict) -> dict:
        """
        Executes a function calling query against the Gemini API.
        
        Args:
            inference_data (dict): Contains messages, tools, and system prompt
        
        Returns:
            dict: API response containing function calls or text
        """
        # Gemini models needs to first conver the function doc to FunctionDeclaration and Tools objects.
        # We do it here to avoid json serialization issues.
        func_declarations = []
        for function in inference_data["tools"]:
            func_declarations.append(
                FunctionDeclaration(
                    name=function["name"],
                    description=function["description"],
                    parameters=function["parameters"],
                )
            )

        if func_declarations:
            tools = [Tool(function_declarations=func_declarations)]
        else:
            tools = None

        inference_data["inference_input_log"] = {
            "message": repr(inference_data["message"]),
            "tools": inference_data["tools"],
            "system_prompt": inference_data.get("system_prompt", None),
        }

        # messages are already converted to Content object
        if "system_prompt" in inference_data:
            # We re-instantiate the GenerativeModel object with the system prompt
            # We cannot reassign the self.client object as it will affect other entries
            client = GenerativeModel(
                self.model_name.replace("-FC", ""),
                system_instruction=inference_data["system_prompt"],
            )
        else:
            client = self.client

        return self.generate_with_backoff(
            client=client,
            contents=inference_data["message"],
            generation_config=GenerationConfig(
                temperature=self.temperature,
            ),
            tools=tools,
        )

    def _pre_query_processing_FC(self, inference_data: dict, test_entry: dict) -> dict:
        """
        Preprocesses test entries for function calling queries.
        
        Args:
            inference_data (dict): Data structure for the inference
            test_entry (dict): Raw test case data
        
        Returns:
            dict: Processed inference data
        """

        for round_idx in range(len(test_entry["question"])):
            test_entry["question"][round_idx] = self._substitute_prompt_role(
                test_entry["question"][round_idx]
            )

        inference_data["message"] = []

        system_prompt = extract_system_prompt(test_entry["question"][0])
        if system_prompt:
            inference_data["system_prompt"] = system_prompt
        return inference_data

    def _compile_tools(self, inference_data: dict, test_entry: dict) -> dict:
        """
        Compiles function documentation into Gemini-compatible tool declarations.
        
        Args:
            inference_data (dict): Data structure for the inference
            test_entry (dict): Raw test case data
        
        Returns:
            dict: Inference data with compiled tools
        """
        functions: list = test_entry["function"]
        test_category: str = test_entry["id"].rsplit("_", 1)[0]

        functions = func_doc_language_specific_pre_processing(functions, test_category)
        tools = convert_to_tool(functions, GORILLA_TO_OPENAPI, self.model_style)

        inference_data["tools"] = tools

        return inference_data

    def _parse_query_response_FC(self, api_response: any) -> dict:
        """
        Parses Gemini's function calling API response.
        
        Args:
            api_response (any): Raw API response
        
        Returns:
            dict: Structured response data with function calls and token counts
        """
        tool_call_func_names = []
        fc_parts = []
        text_parts = []

        if (
            len(api_response.candidates) > 0
            and len(api_response.candidates[0].content.parts) > 0
        ):
            response_function_call_content = api_response.candidates[0].content

            for part in api_response.candidates[0].content.parts:
                # part.function_call is a FunctionCall object, so it will always be True even if it contains no function call
                # So we need to check if the function name is empty `""` to determine if Gemini returned a function call
                if part.function_call and part.function_call.name:
                    part_func_name = part.function_call.name
                    part_func_args = part.function_call.args
                    part_func_args_dict = {k: v for k, v in part_func_args.items()}

                    fc_parts.append({part_func_name: part_func_args_dict})
                    tool_call_func_names.append(part_func_name)
                else:
                    text_parts.append(part.text)
        else:
            response_function_call_content = Content(
                role="model",
                parts=[
                    Part.from_text("The model did not return any response."),
                ],
            )

        model_responses = fc_parts if fc_parts else text_parts

        return {
            "model_responses": model_responses,
            "model_responses_message_for_chat_history": response_function_call_content,
            "tool_call_func_names": tool_call_func_names,
            "input_token": api_response.usage_metadata.prompt_token_count,
            "output_token": api_response.usage_metadata.candidates_token_count,
        }

    def add_first_turn_message_FC(
        self, inference_data: dict, first_turn_message: list[dict]
    ) -> dict:
        """
        Adds initial messages to function calling conversation.
        
        Args:
            inference_data (dict): Conversation state
            first_turn_message (list[dict]): Initial messages
        
        Returns:
            dict: Updated conversation state
        """
        for message in first_turn_message:
            inference_data["message"].append(
                Content(
                    role=message["role"],
                    parts=[
                        Part.from_text(message["content"]),
                    ],
                )
            )
        return inference_data

    def _add_next_turn_user_message_FC(
        self, inference_data: dict, user_message: list[dict]
    ) -> dict:
        """
        Adds user messages to ongoing function calling conversation.
        
        Args:
            inference_data (dict): Conversation state
            user_message (list[dict]): User messages to add
        
        Returns:
            dict: Updated conversation state
        """
        return self.add_first_turn_message_FC(inference_data, user_message)

    def _add_assistant_message_FC(
        self, inference_data: dict, model_response_data: dict
    ) -> dict:
        """
        Adds model responses to function calling conversation.
        
        Args:
            inference_data (dict): Conversation state
            model_response_data (dict): Model response data
        
        Returns:
            dict: Updated conversation state
        """
        inference_data["message"].append(
            model_response_data["model_responses_message_for_chat_history"]
        )
        return inference_data

    def _add_execution_results_FC(
        self,
        inference_data: dict,
        execution_results: list[str],
        model_response_data: dict,
    ) -> dict:
        """
        Adds function execution results to conversation.
        
        Args:
            inference_data (dict): Conversation state
            execution_results (list[str]): Function execution outputs
            model_response_data (dict): Original model response data
        
        Returns:
            dict: Updated conversation state
        """
        # Tool response needs to be converted to Content object as well.
        # One Content object for all tool responses.
        tool_response_parts = []
        for execution_result, tool_call_func_name in zip(
            execution_results, model_response_data["tool_call_func_names"]
        ):
            tool_response_parts.append(
                Part.from_function_response(
                    name=tool_call_func_name,
                    response={
                        "content": execution_result,
                    },
                )
            )

        tool_response_content = Content(parts=tool_response_parts)
        inference_data["message"].append(tool_response_content)

        return inference_data

    #### Prompting methods ####

    def _query_prompting(self, inference_data: dict) -> dict:
        """
        Executes a standard prompting query against the Gemini API.
        
        Args:
            inference_data (dict): Contains messages and system prompt
        
        Returns:
            dict: API response containing text output
        """
        inference_data["inference_input_log"] = {
            "message": repr(inference_data["message"]),
            "system_prompt": inference_data.get("system_prompt", None),
        }

        # messages are already converted to Content object
        if "system_prompt" in inference_data:
            client = GenerativeModel(
                self.model_name.replace("-FC", ""),
                system_instruction=inference_data["system_prompt"],
            )
        else:
            client = self.client
        api_response = self.generate_with_backoff(
            client=client,
            contents=inference_data["message"],
            generation_config=GenerationConfig(
                temperature=self.temperature,
            ),
        )
        return api_response

    def _pre_query_processing_prompting(self, test_entry: dict) -> dict:
        """
        Preprocesses test entries for standard prompting queries.
        
        Args:
            test_entry (dict): Raw test case data
        
        Returns:
            dict: Processed inference data
        """
        functions: list = test_entry["function"]
        test_category: str = test_entry["id"].rsplit("_", 1)[0]

        functions = func_doc_language_specific_pre_processing(functions, test_category)

        for round_idx in range(len(test_entry["question"])):
            test_entry["question"][round_idx] = self._substitute_prompt_role(
                test_entry["question"][round_idx]
            )

        test_entry["question"][0] = system_prompt_pre_processing_chat_model(
            test_entry["question"][0], functions, test_category
        )
        # Gemini has system prompt in a specific field
        system_prompt = extract_system_prompt(test_entry["question"][0])

        if system_prompt:
            return {"message": [], "system_prompt": system_prompt}
        else:
            return {"message": []}

    def _parse_query_response_prompting(self, api_response: any) -> dict:
        """
        Parses Gemini's standard API response.
        
        Args:
            api_response (any): Raw API response
        
        Returns:
            dict: Structured response data with text output and token counts
        """
        if (
            len(api_response.candidates) > 0
            and len(api_response.candidates[0].content.parts) > 0
        ):
            model_responses = api_response.text
        else:
            model_responses = "The model did not return any response."
        return {
            "model_responses": model_responses,
            "input_token": api_response.usage_metadata.prompt_token_count,
            "output_token": api_response.usage_metadata.candidates_token_count,
        }

    def add_first_turn_message_prompting(
        self, inference_data: dict, first_turn_message: list[dict]
    ) -> dict:
        """
        Adds initial messages to standard conversation.
        
        Args:
            inference_data (dict): Conversation state
            first_turn_message (list[dict]): Initial messages
        
        Returns:
            dict: Updated conversation state
        """
        for message in first_turn_message:
            inference_data["message"].append(
                Content(
                    role=message["role"],
                    parts=[
                        Part.from_text(message["content"]),
                    ],
                )
            )
        return inference_data

    def _add_next_turn_user_message_prompting(
        self, inference_data: dict, user_message: list[dict]
    ) -> dict:
        """
        Adds user messages to ongoing standard conversation.
        
        Args:
            inference_data (dict): Conversation state
            user_message (list[dict]): User messages to add
        
        Returns:
            dict: Updated conversation state
        """
        return self.add_first_turn_message_prompting(inference_data, user_message)

    def _add_assistant_message_prompting(
        self, inference_data: dict, model_response_data: dict
    ) -> dict:
        """
        Adds model responses to standard conversation.
        
        Args:
            inference_data (dict): Conversation state
            model_response_data (dict): Model response data
        
        Returns:
            dict: Updated conversation state
        """
        inference_data["message"].append(
            Content(
                role="model",
                parts=[
                    Part.from_text(model_response_data["model_responses"]),
                ],
            )
        )
        return inference_data

    def _add_execution_results_prompting(
        self, inference_data: dict, execution_results: list[str], model_response_data: dict
    ) -> dict:
        """
        Adds execution results to standard conversation.
        
        Args:
            inference_data (dict): Conversation state
            execution_results (list[str]): Execution outputs
            model_response_data (dict): Original model response data
        
        Returns:
            dict: Updated conversation state
        """
        formatted_results_message = format_execution_results_prompting(
            inference_data, execution_results, model_response_data
        )
        tool_message = Content(
            role="user",
            parts=[
                Part.from_text(formatted_results_message),
            ],
        )
        inference_data["message"].append(tool_message)
        return inference_data
