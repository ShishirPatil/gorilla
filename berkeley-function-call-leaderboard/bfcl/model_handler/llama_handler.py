from bfcl.model_handler.oss_handler import OSSHandler
from bfcl.model_handler.utils import ast_parse


class LlamaHandler(OSSHandler):
    def __init__(self, model_name, temperature=0.001, top_p=1, max_tokens=1000) -> None:
        super().__init__(model_name, temperature, top_p, max_tokens)

    def _format_prompt(prompts, function, test_category):

        formatted_prompt = "<|begin_of_text|>"

        for prompt in prompts:
            formatted_prompt += f"<|start_header_id|>{prompt['role']}<|end_header_id|>{prompt['content']}<|eot_id|>"

        formatted_prompt += f"<|start_header_id|>assistant<|end_header_id|>"

        return formatted_prompt

    def inference(
        self,
        test_question,
        num_gpus,
        gpu_memory_utilization,
        format_prompt_func=_format_prompt,
    ):
        return super().inference(
            test_question,
            num_gpus,
            gpu_memory_utilization,
            format_prompt_func=format_prompt_func,
            use_default_system_prompt=True,
            include_default_formatting_prompt=True,
        )

    def decode_ast(self, result, language="Python"):
        func = result
        func = func.replace("\n", "")  # remove new line characters
        if not func.startswith("["):
            func = "[" + func
        if not func.endswith("]"):
            func = func + "]"
        decoded_output = ast_parse(func, language)
        return decoded_output

    def decode_execute(self, result):
        func = result
        func = func.replace("\n", "")  # remove new line characters
        if not func.startswith("["):
            func = "[" + func
        if not func.endswith("]"):
            func = func + "]"
        decode_output = ast_parse(func)
        execution_list = []
        for function_call in decode_output:
            for key, value in function_call.items():
                execution_list.append(
                    f"{key}({','.join([f'{k}={repr(v)}' for k, v in value.items()])})"
                )
        return execution_list
