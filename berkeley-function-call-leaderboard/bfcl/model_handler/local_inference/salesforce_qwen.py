import json

from bfcl.model_handler.local_inference.base_oss_handler import OSSHandler
from bfcl.model_handler.utils import func_doc_language_specific_pre_processing
from overrides import override


class SalesforceQwenHandler(OSSHandler):
    """
    A handler class for Salesforce's Qwen model that extends the base OSSHandler. This class provides specific implementations for prompt formatting, AST decoding, execution decoding, and pre-query processing for the Qwen model.
    """
    def __init__(self, model_name: str, temperature: float) -> None:
        super().__init__(model_name, temperature)

    @override
    def _format_prompt(self, messages: list[dict[str, str]], function: list[dict[str, Any]]) -> str:
        """
        Formats the prompt for the Qwen model with system instructions and conversation history.
        
        Args:
            messages (`list[dict[str, str]]`):
                List of message dictionaries containing 'role' and 'content' keys.
            function (`list[dict[str, Any]]`):
                List of function/tool definitions to include in the prompt.
        
        Returns:
            `str`: The formatted prompt string ready for model input.
        """
        formatted_prompt = ""

        system_message = "You are a helpful assistant that can use tools. You are developed by Salesforce xLAM team."
        remaining_messages = messages
        if messages[0]["role"] == "system":
            system_message = messages[0]["content"].strip()
            remaining_messages = messages[1:]

        # Format system message with tool instructions
        formatted_prompt += "<|im_start|>system\n"
        formatted_prompt += system_message + "\n"
        formatted_prompt += "You have access to a set of tools. When using tools, make calls in a single JSON array: \n\n"
        formatted_prompt += '[{"name": "tool_call_name", "arguments": {"arg1": "value1", "arg2": "value2"}}, ... (additional parallel tool calls as needed)]\n\n'
        formatted_prompt += "If no tool is suitable, state that explicitly. If the user's input lacks required parameters, ask for clarification. "
        formatted_prompt += "Do not interpret or respond until tool results are returned. Once they are available, process them or make additional calls if needed. "
        formatted_prompt += "For tasks that don't require tools, such as casual conversation or general advice, respond directly in plain text. The available tools are:\n\n"

        for func in function:
            formatted_prompt += json.dumps(func, indent=4) + "\n\n"
        formatted_prompt += "<|im_end|>"

        # Format conversation messages
        for message in remaining_messages:
            if message["role"] == "tool":
                formatted_prompt += "<|im_start|>tool\n"
                if isinstance(message["content"], (dict, list)):
                    formatted_prompt += json.dumps(message["content"])
                else:
                    formatted_prompt += message["content"]
                formatted_prompt += "<|im_end|>"
            elif "tool_calls" in message and message["tool_calls"]:
                formatted_prompt += "<|im_start|>assistant\n"
                tool_calls = []
                for tool_call in message["tool_calls"]:
                    tool_calls.append(
                        {
                            "name": tool_call["function"]["name"],
                            "arguments": json.loads(tool_call["function"]["arguments"]),
                        }
                    )
                formatted_prompt += json.dumps(tool_calls) + "<|im_end|>"
            else:
                formatted_prompt += (
                    f"<|im_start|>{message['role']}\n{message['content'].strip()}<|im_end|>"
                )

        formatted_prompt += "<|im_start|>assistant\n"
        return formatted_prompt

    @override
    def decode_ast(self, result: str, language: str="Python") -> list[dict[str, dict[str, Any]]]:
        """
        Decodes the model's output into an abstract syntax tree (AST) representation of function calls.
        
        Args:
            result (`str`):
                The raw model output string to decode.
            language (`str`, optional):
                The programming language of the output (defaults to 'Python').
        
        Returns:
            `list[dict[str, dict[str, Any]]]`: A list of decoded function calls with their arguments.
        """
        # result = result.replace("<|python_tag|>", "")
        try:
            # Parse the JSON array of function calls
            function_calls = json.loads(result)
            if not isinstance(function_calls, list):
                function_calls = [function_calls]
        except json.JSONDecodeError:
            # Fallback for semicolon-separated format
            function_calls = [json.loads(call.strip()) for call in result.split(";")]

        decoded_output = []
        for func_call in function_calls:
            name = func_call["name"]
            arguments = func_call["arguments"]
            decoded_output.append({name: arguments})

        return decoded_output

    @override
    def decode_execute(self, result: str) -> list[str]:
        """
        Decodes the model's output into executable function call strings.
        
        Args:
            result (`str`):
                The raw model output string to decode.
        
        Returns:
            `list[str]`: A list of executable function call strings.
        """
        try:
            function_calls = json.loads(result)
            if not isinstance(function_calls, list):
                function_calls = [function_calls]
        except json.JSONDecodeError:
            function_calls = [json.loads(call.strip()) for call in result.split(";")]

        execution_list = []
        for func_call in function_calls:
            name = func_call["name"]
            arguments = func_call["arguments"]
            execution_list.append(
                f"{name}({','.join([f'{k}={repr(v)}' for k,v in arguments.items()])})"
            )

        return execution_list

    @override
    def _pre_query_processing_prompting(self, test_entry: dict) -> dict:
        """
        Pre-processes test entries before querying the model.
        
        Args:
            test_entry (`dict`):
                The test entry containing function definitions and metadata.
        
        Returns:
            `dict`: The processed test entry with language-specific function documentation.
        """
        functions: list = test_entry["function"]
        test_category: str = test_entry["id"].rsplit("_", 1)[0]
        functions = func_doc_language_specific_pre_processing(functions, test_category)
        # override the default bfcl system prompt, xLAM uses its own system prompt
        return {"message": [], "function": functions}
