import re
from bfcl.model_handler.local_inference.base_oss_handler import OSSHandler
from bfcl.model_handler.utils import (
    ast_parse,
    convert_to_function_call,
)
from overrides import override


class PhiHandler(OSSHandler):
    def __init__(self, model_name, temperature) -> None:
        super().__init__(model_name, temperature)

    @override
    def decode_ast(self, result, language="Python"):
        result = result.strip()
        if result.startswith("```json"):
            result = result[len("```json") :]
        if result.startswith("```python"):
            result = result[len("```python") :]
        return super().decode_ast(result, language)

    @override
    def decode_execute(self, result):
        funcs = re.findall(r"\[[^\[\]]+\]", result)
        decoded_funcs = []
        for func in funcs:
            decode_output = ast_parse(func, language="Python")
            decoded_funcs.extend(decode_output)

        return convert_to_function_call(decoded_funcs)

    @override
    def _format_prompt(self, messages, function):
        formatted_prompt = ""

        if "Phi-4-mini" in self.model_name:
            # Phi-4-mini
            """
            "chat_template": "{% for message in messages %}{% if message['role'] == 'system' and 'tools' in message and message['tools'] is not none %}{{ '<|' + message['role'] + '|>' + message['content'] + '<|tool|>' + message['tools'] + '<|/tool|>' + '<|end|>' }}{% else %}{{ '<|' + message['role'] + '|>' + message['content'] + '<|end|>' }}{% endif %}{% endfor %}{% if add_generation_prompt %}{{ '<|assistant|>' }}{% else %}{{ eos_token }}{% endif %}"
            """
            for message in messages:
                formatted_prompt += f"<|{message['role']}|>{message['content']}<|end|>"
            formatted_prompt += "<|assistant|>"

        elif "Phi-4" in self.model_name:
            # Phi-4
            """
            "chat_template": "{% for message in messages %}{% if (message['role'] == 'system') %}{{'<|im_start|>system<|im_sep|>' + message['content'] + '<|im_end|>'}}{% elif (message['role'] == 'user') %}{{'<|im_start|>user<|im_sep|>' + message['content'] + '<|im_end|>'}}{% elif (message['role'] == 'assistant') %}{{'<|im_start|>assistant<|im_sep|>' + message['content'] + '<|im_end|>'}}{% endif %}{% endfor %}{% if add_generation_prompt %}{{ '<|im_start|>assistant<|im_sep|>' }}{% endif %}"
            """
            for message in messages:
                formatted_prompt += f"<|im_start|>{message['role']}<|im_sep|>{message['content']}<|im_end|>\n"
            formatted_prompt += "<|im_start|>assistant<|im_sep|>"

        return formatted_prompt
