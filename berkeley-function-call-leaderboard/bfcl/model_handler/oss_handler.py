import json
import os

from bfcl.model_handler.handler import BaseHandler
from bfcl.model_handler.model_style import ModelStyle
from bfcl.model_handler.utils import (
    ast_parse,
    augment_prompt_by_languge,
    language_specific_pre_processing,
)


class OSSHandler(BaseHandler):
    def __init__(self, model_name, temperature=0.7, top_p=1, max_tokens=1000, dtype="float16") -> None:
        super().__init__(model_name, temperature, top_p, max_tokens)
        self.model_style = ModelStyle.OSSMODEL
        self.dtype = dtype

    def _format_prompt(prompt, function, test_category):
        SYSTEM_PROMPT = """
            You are an helpful assistant who has access to the following functions to help the user, you can use the functions if needed-
        """
        functions = ""
        if isinstance(function, list):
            for idx, func in enumerate(function):
                functions += "\n" + str(func)
        else:
            functions += "\n" + str(function)
        return f"SYSTEM: {SYSTEM_PROMPT}\n{functions}\nUSER: {prompt}\nASSISTANT: "

    @staticmethod
    def _batch_generate(
        test_question,
        model_path,
        temperature,
        max_tokens,
        top_p,
        dtype,
        stop_token_ids=None,
        max_model_len=None,
        num_gpus=8,
        gpu_memory_utilization=0.9,
    ):
        from vllm import LLM, SamplingParams

        print("start generating, test question length: ", len(test_question))

        sampling_params = SamplingParams(
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            stop_token_ids=stop_token_ids,
        )
        llm = LLM(
            model=model_path,
            dtype=dtype,
            trust_remote_code=True,
            disable_custom_all_reduce=True,
            max_model_len=max_model_len,
            tensor_parallel_size=num_gpus,
            gpu_memory_utilization=gpu_memory_utilization
        )
        outputs = llm.generate(test_question, sampling_params)

        final_ans_jsons = []
        for output in outputs:
            text = output.outputs[0].text
            final_ans_jsons.append(text)

        return final_ans_jsons

    @staticmethod
    def process_input(test_question, format_prompt_func=_format_prompt):
        prompts = []
        for question in test_question:
            test_category = question["id"].rsplit("_", 1)[0]
            prompt = augment_prompt_by_languge(question["question"], test_category)
            functions = language_specific_pre_processing(
                question["function"], test_category
            )
            prompts.append(format_prompt_func(prompt, functions, test_category))

        return prompts

    def inference(
        self,
        test_question,
        num_gpus,
        gpu_memory_utilization,
        format_prompt_func=_format_prompt,
        stop_token_ids=None,
        max_model_len=None,
    ):
        test_question = self.process_input(test_question, format_prompt_func)

        ans_jsons = self._batch_generate(
            test_question=test_question,
            model_path=self.model_name,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            top_p=self.top_p,
            dtype=self.dtype,
            stop_token_ids=stop_token_ids,
            max_model_len=max_model_len,
            num_gpus=num_gpus,
            gpu_memory_utilization=gpu_memory_utilization,
        )

        return ans_jsons, {"input_tokens": 0, "output_tokens": 0, "latency": 0}

    def decode_ast(self, result, language="Python"):
        func = result
        if " " == func[0]:
            func = func[1:]
        if not func.startswith("["):
            func = "[" + func
        if not func.endswith("]"):
            func = func + "]"
        decode_output = ast_parse(func, language)
        return decode_output

    def decode_execute(self, result):
        return result
