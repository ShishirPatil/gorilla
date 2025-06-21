from typing import Optional, Any
from bfcl_eval.model_handler.local_inference.base_oss_handler import OSSHandler
from overrides import override


class MiniCPMHandler(OSSHandler):
    """
    A handler class for the MiniCPM model that formats chat messages into the model's expected prompt format.
    
    Args:
        model_name (`str`):
            The name of the MiniCPM model to use.
        temperature (`float`):
            The temperature parameter for generation, controlling randomness.
    
    Methods:
        _format_prompt(messages: list[dict[str, str]], function: Optional[Any]): Formats chat messages into MiniCPM's specific prompt format with role tags.
    """
    def __init__(self, model_name: str, temperature: float) -> None:
        super().__init__(model_name, temperature)

    @override
    def _format_prompt(self, messages: list[dict[str, str]], function: Optional[Any]) -> str:
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