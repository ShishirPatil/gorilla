from bfcl_eval.model_handler.local_inference.base_oss_handler import OSSHandler
from overrides import override


class DeepseekHandler(OSSHandler):
    """
    This is the handler for the Deepseek model. Deepseek-Coder models should use the DeepseekCoderHandler instead.
    """
    def __init__(self, model_name, temperature) -> None:
        super().__init__(model_name, temperature)

    @override
    def decode_ast(self, result, language="Python"):
        result = result.strip()
        if result.startswith("```json"):
            result = result[len("```json"):]
        if result.startswith("```python"):
            result = result[len("```python"):]
        return super().decode_ast(result, language)

    @override
    def decode_execute(self, result):
        if result.startswith("```json"):
            result = result[len("```json"):]
        if result.startswith("```python"):
            result = result[len("```python"):]
        return super().decode_execute(result)

    @override
    def _format_prompt(self, messages, function):
        """
        "bos_token": {
            "__type": "AddedToken",
            "content": "<｜begin▁of▁sentence｜>",
            "lstrip": false,
            "normalized": true,
            "rstrip": false,
            "single_word": false
        },
        "eos_token": {
            "__type": "AddedToken",
            "content": "<｜end▁of▁sentence｜>",
            "lstrip": false,
            "normalized": true,
            "rstrip": false,
            "single_word": false
        },
        "chat_template": "{% if not add_generation_prompt is defined %}{% set add_generation_prompt = false %}{% endif %}{{ bos_token }}{% for message in messages %}{% if message['role'] == 'user' %}{{ 'User: ' + message['content'] + '\n\n' }}{% elif message['role'] == 'assistant' %}{{ 'Assistant: ' + message['content'] + eos_token }}{% elif message['role'] == 'system' %}{{ message['content'] + '\n\n' }}{% endif %}{% endfor %}{% if add_generation_prompt %}{{ 'Assistant:' }}{% endif %}"
        """
        formatted_prompt = "<｜begin▁of▁sentence｜>"

        for message in messages:
            if message["role"] == "user":
                formatted_prompt += f"User: {message['content']}\n\n"
            elif message["role"] == "assistant":
                formatted_prompt += f"Assistant: {message['content']}<｜end▁of▁sentence｜>"
            elif message["role"] == "system":
                formatted_prompt += f"{message['content']}\n\n"

        formatted_prompt += "Assistant:"

        return formatted_prompt

    @override
    def _add_execution_results_prompting(
        self, inference_data: dict, execution_results: list[str], model_response_data: dict
    ) -> dict:
        # Deepseek don't take the tool role; so we use the user role to send the tool output
        tool_message = {
            "role": "user",
            "content": [],
        }
        for execution_result, decoded_model_response in zip(
            execution_results, model_response_data["model_responses_decoded"]
        ):
            tool_message["content"].append(
                {
                    "role": "tool",
                    "name": decoded_model_response,
                    "content": execution_result,
                }
            )

        inference_data["message"].append(tool_message)

        return inference_data
