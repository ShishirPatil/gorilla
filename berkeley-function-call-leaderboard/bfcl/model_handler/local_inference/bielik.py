from bfcl.model_handler.local_inference.base_oss_handler import OSSHandler
from overrides import override
from transformers import AutoTokenizer

# Note: This is the handler for the Bielik in prompting mode. This model does not support function calls.

class BielikHandler(OSSHandler):
    def __init__(self, model_name, temperature) -> None:
        super().__init__(model_name, temperature)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)

    @override
    def _format_prompt(self, messages, function):
        
        formatted_prompt = self.tokenizer.apply_chat_template(messages, add_generation_prompt=True, tokenize=False)

        return formatted_prompt