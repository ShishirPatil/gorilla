from bfcl.model_handler.huggingface_handler import HuggingFaceHandler


class PhiHandler(HuggingFaceHandler):
    def __init__(self, model_name, temperature=0, top_p=1, max_tokens=1000, add_generation_prompt=False, system_prompt_support=True, attn_implementation="flash_attention_2") -> None:
        super().__init__(model_name, temperature, top_p, max_tokens, add_generation_prompt, system_prompt_support, attn_implementation)

    def inference(
        self,
        test_question,
        num_gpus,
        gpu_memory_utilization,
        stop_token_ids=None,
        max_model_len=None,
        include_system_prompt=True,
    ):
        return super().inference(
            test_question=test_question,
            num_gpus=num_gpus,
            gpu_memory_utilization=gpu_memory_utilization,
            include_system_prompt=include_system_prompt,
        )
    
