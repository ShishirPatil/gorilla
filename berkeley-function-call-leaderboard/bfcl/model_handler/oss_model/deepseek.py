from bfcl.model_handler.oss_model.base_oss_handler import OSSHandler



class DeepseekHandler(OSSHandler):
    def __init__(self, model_name, temperature) -> None:
        super().__init__(model_name, temperature)

    def _format_prompt(self, messages, function):

        #DeepSeek-Coder-V2-Instruct
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
        
        #prev deepseek-coder-6.7b-instruct
        """
        "bos_token": {
            "__type": "AddedToken",
            "content": "<｜begin▁of▁sentence｜>",
            "lstrip": false,
            "normalized": true,
            "rstrip": false,
            "single_word": false
        }
        "chat_template": "{% if not add_generation_prompt is defined %}\n{% set add_generation_prompt = false %}\n{% endif %}\n{%- set ns = namespace(found=false) -%}\n{%- for message in messages -%}\n    {%- if message['role'] == 'system' -%}\n        {%- set ns.found = true -%}\n    {%- endif -%}\n{%- endfor -%}\n{{bos_token}}{%- if not ns.found -%}\n{{'You are an AI programming assistant, utilizing the Deepseek Coder model, developed by Deepseek Company, and you only answer questions related to computer science. For politically sensitive questions, security and privacy issues, and other non-computer science questions, you will refuse to answer\\n'}}\n{%- endif %}\n{%- for message in messages %}\n    {%- if message['role'] == 'system' %}\n{{ message['content'] }}\n    {%- else %}\n        {%- if message['role'] == 'user' %}\n{{'### Instruction:\\n' + message['content'] + '\\n'}}\n        {%- else %}\n{{'### Response:\\n' + message['content'] + '\\n<|EOT|>\\n'}}\n        {%- endif %}\n    {%- endif %}\n{%- endfor %}\n{% if add_generation_prompt %}\n{{'### Response:'}}\n{% endif %}"
        """
        """
        formatted_prompt = "<｜begin▁of▁sentence｜>"

        for message in messages:
            formatted_prompt += "\n    "
            if message["role"] == "system":
                formatted_prompt += f"\n{message['content']}\n    "
            else:
                formatted_prompt += "\n        "
                if message["role"] == "user":
                    formatted_prompt += (
                        f"\n### Instruction:\\n{message['content']}\\n\n        "
                    )
                else:
                    formatted_prompt += (
                        f"\n### Response:\\n{message['content']}\\n<|EOT|>\\n\n        "
                    )
                formatted_prompt += "\n    "
            formatted_prompt += "\n"

        formatted_prompt += "\n### Response:\n"

        return formatted_prompt
        """

