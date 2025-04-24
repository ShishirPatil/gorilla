import re
from bfcl.model_handler.local_inference.base_oss_handler import OSSHandler
from bfcl.model_handler.utils import (
    ast_parse,
    convert_to_function_call,
    func_doc_language_specific_pre_processing,
    system_prompt_pre_processing_chat_model,
)
from overrides import override


class PhiHandler(OSSHandler):
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
        funcs = re.findall(r"\[[^\[\]]+\]", result)
        decoded_funcs = []
        for func in funcs:
            decode_output = ast_parse(func, language="Python")
            decoded_funcs.extend(decode_output)

        return convert_to_function_call(decoded_funcs)

    @override
    def _format_prompt(self, messages, function):
        '''
        Phi-4 input format:
        <|im_start|>system<|im_sep|>
        You are a medieval knight and must provide explanations to modern people.<|im_end|>
        <|im_start|>user<|im_sep|>
        How should I explain the Internet?<|im_end|>
        <|im_start|>assistant<|im_sep|>
        '''
        formatted_prompt = ""
        for message in messages:
            formatted_prompt += f"<|im_start|>{message['role']}<|im_sep|>\n{message['content']}<|im_end|>\n"
        formatted_prompt += "<|im_start|>assistant<|im_sep|>\n"
        return formatted_prompt

    @override
    def _pre_query_processing_prompting(self, test_entry: dict) -> dict:
        functions: list = test_entry["function"]
        test_category: str = test_entry["id"].rsplit("_", 1)[0]

        functions = func_doc_language_specific_pre_processing(functions, test_category)

        test_entry["question"][0] = system_prompt_pre_processing_chat_model(
            test_entry["question"][0], functions, test_category
        )

        return {"message": [], "function": functions}
