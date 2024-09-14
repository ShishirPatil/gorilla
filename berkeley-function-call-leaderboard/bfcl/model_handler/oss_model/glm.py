from bfcl.model_handler.oss_model.base_oss_handler import OSSHandler
from bfcl.model_handler.utils import convert_to_function_call
import json


class GLMHandler(OSSHandler):
    def __init__(self, model_name, temperature=0.001, top_p=1, max_tokens=1000) -> None:
        super().__init__(model_name, temperature, top_p, max_tokens)
        self.max_model_len = 4096
        self.stop_token_ids = [151329, 151336, 151338]

    def apply_chat_template(self, prompts, function, test_category):
        return self.tokenizer.apply_chat_template(
            prompts, tokenize=False, add_generation_prompt=True
        )

    def inference(self, test_question, num_gpus, gpu_memory_utilization):
        from transformers import AutoTokenizer

        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name, trust_remote_code=True
        )

        return super().inference(
            test_question,
            num_gpus,
            gpu_memory_utilization,
            format_prompt_func=self.apply_chat_template,
            stop_token_ids=self.stop_token_ids,
            max_model_len=self.max_model_len,
            include_system_prompt=False,  # they have special formatting
        )

    def decode_ast(self, result, language="Python"):
        args = result.split("\n")
        if len(args) == 1:
            func = [args[0]]
        elif len(args) >= 2:
            func = [{args[0]: json.loads(args[1])}]
        return func

    def decode_execute(self, result):
        args = result.split("\n")
        if len(args) == 1:
            func = args[0]
        elif len(args) >= 2:
            func = [{args[0]: args[1]}]

        return convert_to_function_call(func)
