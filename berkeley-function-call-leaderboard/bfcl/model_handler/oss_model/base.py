import json

import ray
import torch
from vllm import LLM, SamplingParams

from bfcl.model_handler import utils
from bfcl.model_handler.base import BaseHandler, ModelStyle


class OssModelHandler(BaseHandler):
    model_style = ModelStyle.OSS_MODEL
    system_message = 'You are a helpful assistant with access to the following functions. Use them if required -'
    prompt_template = 'SYSTEM: {system_message}\n{functions}\nUSER: {user_input}\nASSISTANT: '

    def __init__(self, model_name, temperature=0.7, top_p=1, max_tokens=1000) -> None:
        super().__init__(model_name, temperature, top_p, max_tokens)
        self.sampling_params = SamplingParams(
            temperature=self.temperature, 
            max_tokens=self.max_tokens, 
            top_p=self.top_p
        )
        self._init_model()

    @classmethod
    def supported_models(cls):
        raise NotImplementedError

    def _init_model(self) -> None:
        ray.init(ignore_reinit_error=True, num_cpus=8)

    def get_prompt(self, user_input, functions, test_category) -> str:
        if isinstance(functions, list):
            functions = json.dumps(functions)
        return self.prompt_template.format(
            system_message=self.system_message, 
            functions=functions, 
            user_input=user_input,
        )

    def inference(self, inputs, num_gpus):
        chunk_size = len(inputs) // num_gpus
        futures = []
        for i in range(0, len(inputs), chunk_size):
            futures.append(
                self._batch_generate.remote(
                    inputs[i: i + chunk_size],
                    self.model_name,
                    self.sampling_params,
                    get_prompt_func=self.get_prompt,
                )
            )
        responses = []
        for future in futures:
            responses.extend(ray.get(future))
        return responses

    def decode_ast(self, result, language="python"):
        func = result
        if " " == func[0]:
            func = func[1:]
        if not func.startswith("["):
            func = "[" + func
        if not func.endswith("]"):
            func = func + "]"
        decode_output = utils.ast_parse(func, language)
        return decode_output

    def decode_execute(self, result):
        return result

    @ray.remote(num_gpus=1)
    @torch.inference_mode()
    def _batch_generate(
        inputs,
        model_path,
        sampling_params: SamplingParams,
        get_prompt_func
    ):
        prompts = []
        for _input in inputs:
            test_category = _input["test_category"]
            prompt = utils.augment_prompt_by_languge(_input["question"], test_category)
            functions = utils.language_specific_pre_processing(_input["function"], test_category, False)
            prompts.append(get_prompt_func(prompt, functions, test_category))

        print(f'Getting responses for {len(prompts)} samples...')
        llm = LLM(model=model_path, dtype="float16", trust_remote_code=True)
        outputs = llm.generate(prompts, sampling_params)
        responses = [
            dict(id=_input['id'], response=output.outputs[0].text)
            for output, _input in zip(outputs, inputs)
        ]
        return responses
