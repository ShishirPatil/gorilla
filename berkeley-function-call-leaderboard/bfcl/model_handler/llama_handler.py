from bfcl.model_handler.oss_handler import OSSHandler
from bfcl.model_handler.utils import ast_parse
from bfcl.model_handler.constant import (
    SYSTEM_PROMPT_FOR_CHAT_MODEL,
    USER_PROMPT_FOR_CHAT_MODEL,
)


class LlamaHandler(OSSHandler):
    def __init__(self, model_name, temperature=0.7, top_p=1, max_tokens=1000) -> None:
        super().__init__(model_name, temperature, top_p, max_tokens)

    def _format_prompt(prompt, function, test_category):
        conversations = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>{SYSTEM_PROMPT_FOR_CHAT_MODEL}<|eot_id|><|start_header_id|>user<|end_header_id|>{USER_PROMPT_FOR_CHAT_MODEL.format(user_prompt=prompt, functions=str(function))}<|eot_id|><|start_header_id|>assistant<|end_header_id|>"""
        return conversations

    def inference(
        self, test_question, num_gpus, gpu_memory_utilization, format_prompt_func=_format_prompt
    ):
        return super().inference(
            test_question, num_gpus, gpu_memory_utilization, format_prompt_func=format_prompt_func
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
