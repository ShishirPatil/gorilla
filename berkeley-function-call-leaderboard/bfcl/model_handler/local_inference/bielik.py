from typing import Optional, Any
from bfcl.model_handler.local_inference.base_oss_handler import OSSHandler
from overrides import override

# Note: This is the handler for the Bielik in prompting mode. This model does not support function calls.


class BielikHandler(OSSHandler):
    """
    Handler for the Bielik model in prompting mode. This model does not support function calls.
    
    Args:
        model_name (`str`):
            Name of the model to use
        temperature (`float`):
            Temperature parameter for generation
    
    Methods:
        _format_prompt(messages: list[dict[str, str]], function: Optional[Any]): Formats chat messages into the Bielik-specific prompt format
    """
    def __init__(self, model_name: str, temperature: float) -> None:
        super().__init__(model_name, temperature)

    @override
    def _format_prompt(self, messages: list[dict[str, str]], function: Optional[Any]) -> str:
        """
        "bos_token": "<s>",
        "chat_template": "{{bos_token}}{% for message in messages %}{{'<|im_start|>' + message['role'] + '\n' + message['content'] + '<|im_end|>' + '\n'}}{% endfor %}{% if add_generation_prompt %}{{ '<|im_start|>assistant\n' }}{% endif %}",
        """

        formatted_prompt = "<s>"

        for message in messages:
            formatted_prompt += f"<|im_start|>{message['role']}\n{message['content']}<|im_end|>\n"

        formatted_prompt += f"<|im_start|>assistant\n"
        
        return formatted_prompt