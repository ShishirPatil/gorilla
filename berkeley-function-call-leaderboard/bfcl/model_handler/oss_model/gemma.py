from bfcl.model_handler.oss_model.base_oss_handler import OSSHandler
from bfcl.model_handler.utils import (
    func_doc_language_specific_pre_processing,
    system_prompt_pre_processing_chat_model,
    convert_system_prompt_into_user_prompt,
    combine_consecutive_user_prompts,
)


class GemmaHandler(OSSHandler):
    def __init__(self, model_name, temperature) -> None:
        super().__init__(model_name, temperature)

    def _format_prompt(self, messages, function):
        """
        "bos_token": "<bos>",
        "chat_template": "{{ bos_token }}{% if messages[0]['role'] == 'system' %}{{ raise_exception('System role not supported') }}{% endif %}{% for message in messages %}{% if (message['role'] == 'user') != (loop.index0 % 2 == 0) %}{{ raise_exception('Conversation roles must alternate user/assistant/user/assistant/...') }}{% endif %}{% if (message['role'] == 'assistant') %}{% set role = 'model' %}{% else %}{% set role = message['role'] %}{% endif %}{{ '<start_of_turn>' + role + '\n' + message['content'] | trim + '<end_of_turn>\n' }}{% endfor %}{% if add_generation_prompt %}{{'<start_of_turn>model\n'}}{% endif %}",
        """
        formatted_prompt = "<bos>"

        for message in messages:
            formatted_prompt += f"<start_of_turn>{message['role']}\n{message['content'].strip()}<end_of_turn>\n"

        formatted_prompt += f"<start_of_turn>model\n"

        return formatted_prompt

    def _pre_query_processing_prompting(self, test_entry: dict) -> dict:
        functions: list = test_entry["function"]
        test_category: str = test_entry["id"].rsplit("_", 1)[0]

        functions = func_doc_language_specific_pre_processing(functions, test_category)

        test_entry["question"][0] = system_prompt_pre_processing_chat_model(
            test_entry["question"][0], functions, test_category
        )

        for round_idx in range(len(test_entry["question"])):
            test_entry["question"][round_idx] = convert_system_prompt_into_user_prompt(
                test_entry["question"][round_idx]
            )
            test_entry["question"][round_idx] = combine_consecutive_user_prompts(
                test_entry["question"][round_idx]
            )
            test_entry["question"][round_idx] = self._substitute_prompt_role(
                test_entry["question"][round_idx]
            )

        return {"message": [], "function": functions}

    @staticmethod
    def _substitute_prompt_role(prompts: list[dict]) -> list[dict]:
        for prompt in prompts:
            if prompt["role"] == "assistant":
                prompt["role"] = "model"

        return prompts
