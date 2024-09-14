from bfcl.model_handler.oss_model.base_oss_handler import OSSHandler
from bfcl.model_handler.utils import ast_parse


class Phi3Handler(OSSHandler):
    def __init__(self, model_name, temperature=0.001, top_p=1, max_tokens=1000) -> None:
        super().__init__(model_name, temperature, top_p, max_tokens)

    def _format_prompt(self, prompts, function, test_category):
        formatted_prompt = ""
        for prompt in prompts:
            role_token = f"<|{prompt['role']}|>" if prompt['role'] in ['system', 'user', 'assistant'] else "<|system|>"
            formatted_prompt += f"{role_token}{prompt['content']}<|end|>\n"
        formatted_prompt += "<|assistant|>\n"
        return formatted_prompt

    def inference(
        self,
        test_question,
        num_gpus,
        gpu_memory_utilization,
        format_prompt_func=None,
    ):
        if format_prompt_func == None:
            format_prompt_func = self._format_prompt

        return super().inference(
            test_question,
            num_gpus,
            gpu_memory_utilization,
            format_prompt_func=format_prompt_func,
            include_system_prompt=True,
        )
    def decode_ast(self, result, language="Python"):
        func = result
        if " " == func[0] or "\n" == func[0]:
            func = func[1:]
        if not func.startswith("["):
            func = "[" + func
        if not func.endswith("]"):
            func = func + "]"
        decode_output = ast_parse(func, language)
        return decode_output

    def decode_execute(self, result):
        func = result
        if " " == func[0] or "\n" == func[0]:
            func = func[1:]
        if not func.startswith("["):
            func = "[" + func
        if not func.endswith("]"):
            func = func + "]"
        return super().decode_execute(func)