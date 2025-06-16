from bfcl_eval.model_handler.local_inference.base_oss_handler import OSSHandler
from overrides import override

# Note: This is the handler for the Bielik in prompting mode. This model does not support function calls.


class BielikHandler(OSSHandler):
    def __init__(self, model_name, temperature) -> None:
        super().__init__(model_name, temperature)

    @override
    def _format_prompt(self, messages, function):
        """
        "bos_token": "<s>",
        "chat_template": "{{bos_token}}{% for message in messages %}{{'<|im_start|>' + message['role'] + '\n' + message['content'] + '<|im_end|>' + '\n'}}{% endfor %}{% if add_generation_prompt %}{{ '<|im_start|>assistant\n' }}{% endif %}",
        """

        formatted_prompt = "<s>"

        for message in messages:
            formatted_prompt += f"<|im_start|>{message['role']}\n{message['content']}<|im_end|>\n"

        formatted_prompt += f"<|im_start|>assistant\n"
        
        return formatted_prompt
