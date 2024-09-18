from bfcl.model_handler.oss_model.base_oss_handler import OSSHandler

class QwenHandler(OSSHandler):
    def __init__(self, model_name, temperature=0.001, top_p=1, max_tokens=1000) -> None:
        super().__init__(model_name, temperature, top_p, max_tokens)

    def apply_chat_template(self, prompts, function, test_category):
        formatted_prompt = ""
        for prompt in prompts:
            formatted_prompt += f"<|im_start|>{prompt['role']}\n{prompt['content']}<|im_end|>\n"
        formatted_prompt += "<|im_start|>assistant\n"
        return formatted_prompt

    def inference(self, test_question, num_gpus, gpu_memory_utilization):
        return super().inference(
            test_question,
            num_gpus,
            gpu_memory_utilization,
            format_prompt_func=self.apply_chat_template,
        )