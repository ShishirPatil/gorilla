from model_handler.handler import BaseHandler
from model_handler.model_style import ModelStyle
from model_handler.utils import (
    ast_parse,
    system_prompt_pre_processing_chat_model,
    func_doc_language_specific_pre_processing,
)
from model_handler.constant import DEFAULT_SYSTEM_PROMPT


class OSSHandler(BaseHandler):
    def __init__(
        self, model_name, temperature=0.001, top_p=1, max_tokens=1000, dtype="bfloat16"
    ) -> None:
        super().__init__(model_name, temperature, top_p, max_tokens)
        self.model_style = ModelStyle.OSSMODEL
        self.dtype = dtype

    def _format_prompt(prompts, function, test_category):
        prompt_string = ""
        for prompt in prompts:
            prompt_string += f"## {prompt['role']}:\n{prompt['content']}\n\n"
        return prompt_string

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
            gpu_memory_utilization=gpu_memory_utilization,
        )
        outputs = llm.generate(test_question, sampling_params)

        final_ans_jsons = []
        for output in outputs:
            text = output.outputs[0].text
            final_ans_jsons.append(text)

        return final_ans_jsons

    @staticmethod
    def process_input(
        test_question,
        format_prompt_func,
        include_system_prompt=True,
    ):
        prompts = []
        for question in test_question:
            test_category = question["id"].rsplit("_", 1)[0]
            functions = func_doc_language_specific_pre_processing(
                question["function"], test_category
            )
            # Only the chat model needs the system prompt; also some require special formatting
            if include_system_prompt:
                question["question"] = system_prompt_pre_processing_chat_model(
                    question["question"], DEFAULT_SYSTEM_PROMPT, functions
                )

            prompts.append(format_prompt_func(question["question"], functions, test_category))

        return prompts

    def inference(
        self,
        test_question,
        num_gpus,
        gpu_memory_utilization,
        format_prompt_func=_format_prompt,
        stop_token_ids=None,
        max_model_len=None,
        include_system_prompt=True,
    ):
        test_question = self.process_input(
            test_question,
            format_prompt_func,
            include_system_prompt=include_system_prompt,
        )

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
        decoded_output = ast_parse(result)
        execution_list = []
        for function_call in decoded_output:
            for key, value in function_call.items():
                execution_list.append(
                    f"{key}({','.join([f'{k}={repr(v)}' for k, v in value.items()])})"
                )
        return execution_list
