import json
import os
import time

import re
from bfcl_eval.model_handler.model_style import ModelStyle
from bfcl_eval.model_handler.utils import (
    func_doc_language_specific_pre_processing,
    retry_with_backoff,
)
from openai import OpenAI, RateLimitError
from bfcl_eval.model_handler.api_inference.openai import OpenAIHandler

class MiningHandler(OpenAIHandler):
    """
    A handler class for mining and processing function calls from AI model responses. Inherits from OpenAIHandler and specializes in parsing and processing function call outputs.
    """
    def __init__(self, model_name: str, temperature: float) -> None:
        super().__init__(model_name, temperature)
        self.model_style = ModelStyle.OpenAI
        self.client = OpenAI(
            base_url= os.getenv("MINING_BASE_URL"),
            api_key=os.getenv("MINING_API_KEY"),
        )

    def decode_ast(self, result: list[dict[str, Any]], language: str="Python") -> list[dict[str, Any]]:
        """
        Decodes the abstract syntax tree (AST) representation of function calls from the model output.
        
        Args:
            result (`list[dict[str, Any]]`): List of function call dictionaries from model output
            language (`str`, optional): Programming language of the functions (default: 'Python')
        
        Returns:
            `list[dict[str, Any]]`: List of decoded function calls with names and parameters
        """
        decoded_output = []
        for invoked_function in result:
            name = invoked_function["name"]
            params = invoked_function["arguments"]
            decoded_output.append({name: params})
        return decoded_output

    def decode_execute(self, result: list[dict[str, Any]]) -> list[str]:
        """
        Converts function call dictionaries into executable string representations.
        
        Args:
            result (`list[dict[str, Any]]`): List of function call dictionaries
        
        Returns:
            `list[str]`: List of executable function call strings
        """
        too_call_format = []
        for tool_call in result:
            if isinstance(tool_call, dict):
                name = tool_call.get("name", "")
                arguments = tool_call.get("arguments", {})
                args_str = ", ".join(
                    [f"{key}={repr(value)}" for key, value in arguments.items()]
                )
                too_call_format.append(f"{name}({args_str})")
        return too_call_format

    #### Prompting methods ####

    def _pre_query_processing_prompting(self, test_entry: dict) -> dict:
        """
        Pre-processes test entries before querying the model. Prepares function documentation and questions.
        
        Args:
            test_entry (`dict`): Test case entry containing functions and questions
        
        Returns:
            `dict`: Processed test entry with empty message list
        """
        functions: list = test_entry["function"]
        test_category: str = test_entry["id"].rsplit("_", 1)[0]

        functions = func_doc_language_specific_pre_processing(functions, test_category)

        test_entry["question"][0] = self.mining_system_prompt_pre_processing_chat_model(
            test_entry["question"][0], functions, test_category
        )
        return {"message": []}

    def _parse_query_response_prompting(self, api_response: any) -> dict:
        """
        Parses the model's response to extract tool calls and usage metrics.
        
        Args:
            api_response (`any`): Raw response from the API call
        
        Returns:
            `dict`: Parsed response containing tool calls, chat history message, and token usage
        """
        match = re.search(r'<tool_calls>\n(.*?)\n</tool_calls>', api_response.choices[0].message.content, re.DOTALL)
        tool_calls = api_response.choices[0].message.content
        if match:
           tool_calls =  match.group(1).strip()
        try:
            tool_calls = tool_calls.replace("'",'"')
            tool_calls = json.loads(tool_calls)
        except:
            pass
        message = api_response.choices[0].message
        return {
            "model_responses": tool_calls,
            "model_responses_message_for_chat_history": message,
            "input_token": api_response.usage.prompt_tokens,
            "output_token": api_response.usage.completion_tokens,
        }

    def mining_system_prompt_pre_processing_chat_model(self,prompts: list[dict[str, str]], function_docs: str, test_category: str) -> list[dict[str, str]]:
        """
        Constructs the system prompt for function calling models with proper formatting.
        
        Args:
            prompts (`list[dict[str, str]]`): List of prompt messages
            function_docs (`str`): Documentation of available functions
            test_category (`str`): Category of the test case
        
        Returns:
            `list[dict[str, str]]`: Processed prompts with system message
        """
        system_pre="""You are a function calling AI model. 
You are provided with function signatures within <tools></tools> XML tags.
You may call one or more functions to assist with the user query. 
Don't make assumptions about what values to plug into functions.

Here are the available tools:
<tools> 
{}
</tools>
"""
        system_suffix = """

Use the following pydantic model json schema for each tool call you will make: 
{"title": "FunctionCalls", "type": "array", "properties": {"arguments": {"title": "Arguments", "type": "object"}, "name": {"title": "Name", "type": "string"}}, "required": ["arguments", "name"]}

At each turn, you should try your best to complete the tasks requested by the user within the current turn. Continue to output functions to call until you have fulfilled the user's request to the best of your ability. Once you have no more functions to call, the system will consider the current turn complete and proceed to the next turn or task.

# Output Format
If you find suitable function, for each function call return a json object with function name and arguments within <tool_calls></tool_calls> XML tags as follows:
<think>
{reasoning process here}
</think>
<tool_calls>
{[tool_call]}
</tool_calls>

If no suitable function is found, just respond with XML tags as follows:
<think>
{reasoning process here}
</think>
<tool_calls>
[]
</tool_calls>"""
        assert type(prompts) == list

        system_prompt = system_pre.format(function_docs)+system_suffix

        # System prompt must be in the first position
        # If the question comes with a system prompt, append its content at the end of the chat template.
        if prompts[0]["role"] == "system":
            prompts[0]["content"] = system_prompt + "\n\n" + prompts[0]["content"]
        # Otherwise, use the system prompt template to create a new system prompt.
        else:
            prompts.insert(
                0,
                {"role": "system", "content": system_prompt},
            )

        return prompts
