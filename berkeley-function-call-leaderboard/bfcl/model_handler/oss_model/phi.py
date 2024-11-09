from bfcl.model_handler.oss_model.base_oss_handler import OSSHandler
from bfcl.model_handler.utils import (
    combine_consecutive_user_prompts,
    convert_system_prompt_into_user_prompt,
    func_doc_language_specific_pre_processing,
    system_prompt_pre_processing_chat_model,
)


class PhiHandler(OSSHandler):
    def __init__(self, model_name, temperature) -> None:
        super().__init__(model_name, temperature)

    def _format_prompt(self, messages, function):
        if "Phi-3-small" in self.model_name:
            # Phi-3-small
            """
            "bos_token": "<|endoftext|>",
            "chat_template": "{{ bos_token }}{% for message in messages %}{{'<|' + message['role'] + '|>' + '\n' + message['content'] + '<|end|>\n' }}{% endfor %}{% if add_generation_prompt %}{{ '<|assistant|>\n' }}{% else %}{{ eos_token }}{% endif %}",
            "eos_token": "<|endoftext|>",
            """
            formatted_prompt = "<|endoftext|>"
        else:
            # Phi-3.5-mini, Phi-3-medium, Phi-3-mini
            """
            "bos_token": "<s>",
            "chat_template": "{% for message in messages %}{% if message['role'] == 'system' and message['content'] %}{{'<|system|>\n' + message['content'] + '<|end|>\n'}}{% elif message['role'] == 'user' %}{{'<|user|>\n' + message['content'] + '<|end|>\n'}}{% elif message['role'] == 'assistant' %}{{'<|assistant|>\n' + message['content'] + '<|end|>\n'}}{% endif %}{% endfor %}{% if add_generation_prompt %}{{ '<|assistant|>\n' }}{% else %}{{ eos_token }}{% endif %}",
            """
            formatted_prompt = ""

        for message in messages:
            formatted_prompt += f"<|{message['role']}|>\n{message['content']}<|end|>\n"

        formatted_prompt += f"<|assistant|>\n"

        return formatted_prompt

    def _pre_query_processing_prompting(self, test_entry: dict) -> dict:
        functions: list = test_entry["function"]
        test_category: str = test_entry["id"].rsplit("_", 1)[0]

        functions = func_doc_language_specific_pre_processing(functions, test_category)

        test_entry["question"][0] = system_prompt_pre_processing_chat_model(
            test_entry["question"][0], functions, test_category
        )

        if "Phi-3-small" in self.model_name:
            # Phi-3-small doesn't allow system role
            for round_idx in range(len(test_entry["question"])):
                test_entry["question"][round_idx] = convert_system_prompt_into_user_prompt(
                    test_entry["question"][round_idx]
                )
                test_entry["question"][round_idx] = combine_consecutive_user_prompts(
                    test_entry["question"][round_idx]
                )

        return {"message": [], "function": functions}
