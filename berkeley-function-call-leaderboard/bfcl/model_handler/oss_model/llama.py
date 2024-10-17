from bfcl.model_handler.oss_model.base_oss_handler import OSSHandler


# Note: This is the handler for the Llama models in prompring mode.
# For function call mode, use LlamaFCHandler instead.
# Llama 3 series are benchmarked in prompting mode while the Llama 3.1 series are benchmarked in function call mode.
class LlamaHandler(OSSHandler):
    def __init__(self, model_name, temperature) -> None:
        super().__init__(model_name, temperature)

    def _format_prompt(self, messages, function):
        formatted_prompt = "<|begin_of_text|>"

        for message in messages:
            formatted_prompt += f"<|start_header_id|>{message['role']}<|end_header_id|>\n\n{message['content'].strip()}<|eot_id|>"

        formatted_prompt += f"<|start_header_id|>assistant<|end_header_id|>\n\n"

        return formatted_prompt
