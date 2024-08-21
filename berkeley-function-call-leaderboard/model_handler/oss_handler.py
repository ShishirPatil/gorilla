from model_handler.handler import BaseHandler
from model_handler.model_style import ModelStyle
from model_handler.utils import (
    ast_parse,
    system_prompt_pre_processing,
    user_prompt_pre_processing_chat_model,
    func_doc_language_specific_pre_processing,
)
from model_handler.constant import DEFAULT_SYSTEM_PROMPT, USER_PROMPT_FOR_CHAT_MODEL


class OSSHandler(BaseHandler):
    def __init__(
        self,
        model_name,
        temperature=0.001,
        top_p=1,
        max_tokens=1000,
        dtype="bfloat16",
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
    def _batch_generate_vllm(
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
    def _batch_generate_sglang(
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
        import sglang as sgl

        import torch

        num_sms = torch.cuda.get_device_properties(0).multi_processor_count
        if num_sms >= 80:
            disable_flashinfer = False
            assert (
                sgl.__version__ >= "0.2.13"
            ), "Please upgrade sglang to version 0.2.13 or higher"

            try:
                import flashinfer
            except ImportError:
                print(
                    "Please install flashinfer to use sglang: "
                    "https://docs.flashinfer.ai/installation.html"
                )
                raise
        else:
            disable_flashinfer = True

        runtime = sgl.Runtime(
            model_path=model_path,
            dtype=dtype,
            trust_remote_code=True,
            context_length=max_model_len,
            tp_size=num_gpus,
            mem_fraction_static=gpu_memory_utilization,
            enable_p2p_check=True,
            disable_flashinfer=disable_flashinfer,
        )

        sgl.set_default_backend(runtime)

        @sgl.function
        def _sglang_gen(s, prompt):
            s += prompt
            s += sgl.gen("res")

        arguments = [{"prompt": prompt} for prompt in test_question]

        if stop_token_ids is None:
            stop_token_ids = []

        rets = _sglang_gen.run_batch(
            arguments,
            temperature=temperature,
            max_new_tokens=max_tokens,
            top_p=top_p,
            stop_token_ids=stop_token_ids,
            progress_bar=True,
        )

        rets = [ret["res"] for ret in rets]
        
        runtime.shutdown()

        return rets

    @staticmethod
    def _batch_generate_sglang(
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
        import sglang as sgl

        assert (
            sgl.__version__ >= "0.2.13"
        ), "Please upgrade sglang to version 0.2.13 or higher"

        try:
            import flashinfer
        except ImportError:
            print(
                "Please install flashinfer to use sglang: "
                "https://docs.flashinfer.ai/installation.html"
            )
            raise

        runtime = sgl.Runtime(
            model_path=model_path,
            dtype=dtype,
            trust_remote_code=True,
            context_length=max_model_len,
            tp_size=num_gpus,
            mem_fraction_static=gpu_memory_utilization,
            enable_p2p_check=True,
        )

        sgl.set_default_backend(runtime)

        @sgl.function
        def _sglang_gen(s, prompt):
            s += prompt
            s += sgl.gen("res")

        arguments = [{"prompt": prompt} for prompt in test_question]

        if stop_token_ids is None:
            stop_token_ids = []

        rets = _sglang_gen.run_batch(
            arguments,
            temperature=temperature,
            max_new_tokens=max_tokens,
            top_p=top_p,
            stop_token_ids=stop_token_ids,
            progress_bar=True,
        )

        rets = [ret["res"] for ret in rets]
        
        runtime.shutdown()

        return rets

    @staticmethod
    def process_input(
        test_question,
        format_prompt_func,
        use_default_system_prompt,
        include_default_formatting_prompt,
    ):
        prompts = []
        for question in test_question:
            test_category = question["id"].rsplit("_", 1)[0]
            functions = func_doc_language_specific_pre_processing(
                question["function"], test_category
            )
            # prompt here is a list of dictionaries, one representing a role and content
            if use_default_system_prompt:
                question["question"] = system_prompt_pre_processing(
                    question["question"], DEFAULT_SYSTEM_PROMPT
                )
            if include_default_formatting_prompt:
                question["question"] = user_prompt_pre_processing_chat_model(
                    question["question"], USER_PROMPT_FOR_CHAT_MODEL, test_category, functions
                )

            prompts.append(format_prompt_func(question["question"], functions, test_category))

        return prompts

    def inference(
        self,
        test_question,
        num_gpus,
        gpu_memory_utilization,
        backend,
        format_prompt_func=_format_prompt,
        stop_token_ids=None,
        max_model_len=None,
        use_default_system_prompt=True,
        include_default_formatting_prompt=True,
    ):
        test_question = self.process_input(
            test_question,
            format_prompt_func,
            use_default_system_prompt,
            include_default_formatting_prompt,
        )

        if backend == "sglang":
            ans_jsons = self._batch_generate_sglang(
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
        else:
            ans_jsons = self._batch_generate_vllm(
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
