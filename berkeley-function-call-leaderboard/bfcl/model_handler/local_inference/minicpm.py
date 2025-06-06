from typing import Optional
from bfcl.model_handler.local_inference.base_oss_handler import OSSHandler
from overrides import override


class MiniCPMHandler(OSSHandler):
    """
    A handler class for MiniCPM model that formats chat messages into the specific prompt format required by the model.
    
    Args:
        model_name (`str`):
            Name of the MiniCPM model to be used.
        temperature (`float`):
            Temperature parameter for controlling randomness in generation.
    
    Methods:
        _format_prompt(messages: list[dict[str, str]], function: Optional[dict[str, Any]]) -> str:
            Formats chat messages into MiniCPM's specific prompt format with special tokens.
    """
    def __init__(self, model_name: str, temperature: float) -> None:
        super().__init__(model_name, temperature)

    @override
    def _format_prompt(self, messages: list[dict[str, str]], function: Optional[dict[str, Any]]) -> str:
        """
        "chat_template": "{% for message in messages %}{{'<|im_start|>' + message['role'] + '\n' + message['content'] + '<|im_end|>' + '\n'}}{% endfor %}{% if add_generation_prompt %}{{ '<|im_start|>assistant\n' }}{% endif %}"
        """
        formatted_prompt = ""

        for message in messages:
            formatted_prompt += (
                f"<|im_start|>{message['role']}\n{message['content']}<|im_end|>\n"
            )

        formatted_prompt += f"<|im_start|>assistant\n"

        return formatted_prompt
