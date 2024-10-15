from bfcl.model_handler.oss_model.base_oss_handler import OSSHandler



class DeepseekV2Handler(OSSHandler):
    def __init__(self, model_name, temperature) -> None:
        super().__init__(model_name, temperature)

    def _format_prompt(self, messages, function):
        
        formatted_prompt = "<｜begin▁of▁sentence｜>"

        if "DeepSeek-V2-Chat-0628" in self.model_name:
            #DeepSeek-V2-Chat-0628
            """
            "bos_token": {
                "__type": "AddedToken",
                "content": "<｜begin▁of▁sentence｜>",
                "lstrip": false,
                "normalized": true,
                "rstrip": false,
                "single_word": false
            }
            "chat_template": "{% if not add_generation_prompt is defined %}{% set add_generation_prompt = false %}{% endif %}{{ bos_token }}{% for message in messages %}{% if message['role'] == 'user' %}{{ '<｜User｜>' + message['content'] }}{% elif message['role'] == 'assistant' %}{{ '<｜Assistant｜>' + message['content'] + eos_token }}{% elif message['role'] == 'system' %}{{ message['content'] + '\n\n' }}{% endif %}{% endfor %}{% if add_generation_prompt %}{{ '<｜Assistant｜>' }}{% endif %}"
            """
            for message in messages:
                if message["role"] == "user":
                    formatted_prompt += f"<｜User｜>{message['content']}"
                elif message["role"] == "assistant":
                    formatted_prompt += f"<｜Assistant｜>{message['content']}<|EOT|>"
                elif message["role"] == "system":
                    formatted_prompt += f"{message['content']}\n\n"

                if add_generation_prompt:
                    formatted_prompt += "<｜Assistant｜>"
        else:
            #DeepSeek-V2-Chat, DeepSeek-V2, DeepSeek-V2-Lite, DeepSeek-v2-Lite-Chat
            """
            "bos_token": {
                "__type": "AddedToken",
                "content": "<｜begin▁of▁sentence｜>",
                "lstrip": false,
                "normalized": true,
                "rstrip": false,
                "single_word": false
            }
            "chat_template": "{% if not add_generation_prompt is defined %}{% set add_generation_prompt = false %}{% endif %}{{ bos_token }}{% for message in messages %}{% if message['role'] == 'user' %}{{ 'User: ' + message['content'] + '\n\n' }}{% elif message['role'] == 'assistant' %}{{ 'Assistant: ' + message['content'] + eos_token }}{% elif message['role'] == 'system' %}{{ message['content'] + '\n\n' }}{% endif %}{% endfor %}{% if add_generation_prompt %}{{ 'Assistant:' }}{% endif %}"
            """

            for message in messages:
                if message["role"] == "user":
                    formatted_prompt += f"User: {message['content']}\n\n"
                elif message["role"] == "assistant":
                    formatted_prompt += f"Assistant: {message['content']}<|EOT|>"
                elif message["role"] == "system":
                    formatted_prompt += f"{message['content']}\n\n"

                if add_generation_prompt:
                    formatted_prompt += "Assistant:"

        return formatted_prompt
    

