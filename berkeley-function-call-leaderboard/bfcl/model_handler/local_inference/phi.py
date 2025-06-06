from typing import Any
from bfcl.model_handler.local_inference.base_oss_handler import OSSHandler
from overrides import override


class PhiHandler(OSSHandler):
    """
    A handler class for Phi models that extends the base OSSHandler to provide model-specific implementations for prompt formatting and response decoding.
    """
    def __init__(self, model_name: str, temperature: float) -> None:
        super().__init__(model_name, temperature)

    @override
    def decode_ast(self, result: str, language: str="Python"):
        """
        Processes and decodes the AST (Abstract Syntax Tree) from the model's response by cleaning up code block markers.
        
        Args:
            result (str): The raw model output containing potential code blocks
            language (str): The programming language of the code (default: 'Python')
        
        Returns:
            The decoded AST after removing code block markers
        """
        result = result.strip()
        if result.startswith("```json"):
            result = result[len("```json") :]
        if result.startswith("```python"):
            result = result[len("```python") :]
        return super().decode_ast(result, language)

    @override
    def decode_execute(self, result: str):
        """
        Processes and decodes executable code from the model's response by cleaning up code block markers.
        
        Args:
            result (str): The raw model output containing potential code blocks
        
        Returns:
            The executable code after removing code block markers
        """
        if result.startswith("```json"):
            result = result[len("```json") :]
        if result.startswith("```python"):
            result = result[len("```python") :]
        return super().decode_execute(result)

    @override
    def _format_prompt(self, messages: list[dict[str, str]], function) -> str:
        """
        Formats chat messages into the specific prompt format required by different Phi model variants.
        
        Args:
            messages (list[dict[str, str]]): List of message dictionaries with 'role' and 'content' keys
            function: Unused parameter (maintained for interface compatibility)
        
        Returns:
            str: The formatted prompt string with appropriate role tags and separators
        
        Note:
            Implements different formatting for Phi-4-mini and Phi-4 models based on their chat templates
        """
        formatted_prompt = ""

        if "Phi-4-mini" in self.model_name:
            # Phi-4-mini
            """
            "chat_template": "{% for message in messages %}{% if message['role'] == 'system' and 'tools' in message and message['tools'] is not none %}{{ '<|' + message['role'] + '|>' + message['content'] + '<|tool|>' + message['tools'] + '<|/tool|>' + '<|end|>' }}{% else %}{{ '<|' + message['role'] + '|>' + message['content'] + '<|end|>' }}{% endif %}{% endfor %}{% if add_generation_prompt %}{{ '<|assistant|>' }}{% else %}{{ eos_token }}{% endif %}"
            """
            for message in messages:
                formatted_prompt += f"<|{message['role']}|>{message['content']}<|end|>"
            formatted_prompt += "<|assistant|>"

        else:
            # Phi-4
            """
            "chat_template": "{% for message in messages %}{% if (message['role'] == 'system') %}{{'<|im_start|>system<|im_sep|>' + message['content'] + '<|im_end|>'}}{% elif (message['role'] == 'user') %}{{'<|im_start|>user<|im_sep|>' + message['content'] + '<|im_end|>'}}{% elif (message['role'] == 'assistant') %}{{'<|im_start|>assistant<|im_sep|>' + message['content'] + '<|im_end|>'}}{% endif %}{% endfor %}{% if add_generation_prompt %}{{ '<|im_start|>assistant<|im_sep|>' }}{% endif %}"
            """
            for message in messages:
                formatted_prompt += f"<|im_start|>{message['role']}<|im_sep|>{message['content']}<|im_end|>\n"
            formatted_prompt += "<|im_start|>assistant<|im_sep|>"

        return formatted_prompt
