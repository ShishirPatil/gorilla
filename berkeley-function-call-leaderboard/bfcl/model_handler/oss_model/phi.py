from bfcl.model_handler.oss_model.base_oss_handler import OSSHandler

class PhiHandler(OSSHandler):
    def __init__(self, model_name, temperature) -> None:
        super().__init__(model_name, temperature)

    @staticmethod
    def _format_prompt(messages, function):
        """
        "bos_token": "<s>",
        "chat_template": "{% for message in messages %}{% if message['role'] == 'system' and message['content'] %}{{'<|system|>\n' + message['content'] + '<|end|>\n'}}{% elif message['role'] == 'user' %}{{'<|user|>\n' + message['content'] + '<|end|>\n'}}{% elif message['role'] == 'assistant' %}{{'<|assistant|>\n' + message['content'] + '<|end|>\n'}}{% endif %}{% endfor %}{% if add_generation_prompt %}{{ '<|assistant|>\n' }}{% else %}{{ eos_token }}{% endif %}",
        """
        formatted_prompt = ""

        for message in messages:
            formatted_prompt += f"<|{message['role']}|>\n{message['content']}<|end|>\n"

        formatted_prompt += f"<|assistant|>\n"

        return formatted_prompt
