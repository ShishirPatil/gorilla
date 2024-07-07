from model_handler.oss_handler import OSSHandler
from model_handler.utils import ast_parse
from model_handler.constant import (
    SYSTEM_PROMPT_FOR_CHAT_MODEL,
    USER_PROMPT_FOR_CHAT_MODEL,
)
from model_handler.model_style import ModelStyle
from model_handler.utils import (
    convert_to_tool,
    augment_prompt_by_languge,
    language_specific_pre_processing,
    convert_to_function_call,
)
from model_handler.constant import GORILLA_TO_OPENAPI
import shortuuid
import json

from eval_checker.eval_checker_constant import FILENAME_INDEX_MAPPING


class GLMHandler(OSSHandler):
    def __init__(self, model_name, temperature=0.7, top_p=1, max_tokens=1000) -> None:
        super().__init__(model_name, temperature, top_p, max_tokens)
        self.tensor_parallel_size = 8

    def apply_chat_template(self, prompt, function, test_category):
        oai_tool = convert_to_tool(
            function, GORILLA_TO_OPENAPI, ModelStyle.OpenAI, test_category, True
        )
        conversation = [{"role": "user", "content": prompt, "tools": oai_tool}]
        return self.tokenizer.apply_chat_template(
            conversation, tokenize=False, add_generation_prompt=True
        )

    def _batch_generate(
        self,
        question_jsons,
        test_category,
        model_path,
        temperature,
        max_tokens,
        top_p,
        index,
        llm,
    ):
        from vllm import SamplingParams

        prompts = []
        ans_jsons = []
        for line in question_jsons:
            for key, value in FILENAME_INDEX_MAPPING.items():
                start, end = value
                if index >= start and index < end:
                    test_category = key
                    break
            prompts.append(line)
            ans_id = shortuuid.uuid()
            ans_jsons.append(
                {
                    "answer_id": ans_id,
                    "question": line,
                }
            )

        print("start generating: ", len(prompts))
        stop_token_ids = [151329, 151336, 151338]
        sampling_params = SamplingParams(
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            stop_token_ids=stop_token_ids,
        )
        outputs = llm.generate(prompts, sampling_params)
        final_ans_jsons = []
        for output, ans_json in zip(outputs, ans_jsons):
            text = output.outputs[0].text
            ans_json["text"] = text
            final_ans_jsons.append(ans_json)
        return final_ans_jsons

    def inference(self, question_file, test_category, num_gpus):
        from transformers import AutoTokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name, trust_remote_code=True
        )
        
        ques_jsons = []
        with open(question_file, "r") as ques_file:
            for line in ques_file:
                ques_jsons.append(json.loads(line))
        chat_template_ques_jsons = []
        for line in ques_jsons:
            prompt = augment_prompt_by_languge(line["question"], test_category)
            function = language_specific_pre_processing(
                line["function"], test_category, False
            )
            chat_template_ques_jsons.append(
                self.apply_chat_template(prompt, function, test_category)
            )

        chunk_size = len(ques_jsons) // num_gpus
        from vllm import LLM

        llm = LLM(
            model=self.model_name,
            dtype="float16",
            trust_remote_code=True,
            tensor_parallel_size=self.tensor_parallel_size,
            max_model_len=4096,
        )
        ans_jsons = []
        for i in range(0, len(ques_jsons), chunk_size):
            output = self._batch_generate(
                chat_template_ques_jsons[i : i + chunk_size],
                test_category,
                self.model_name,
                self.temperature,
                self.max_tokens,
                self.top_p,
                i,
                llm,
            )
            ans_jsons.extend(output)

        return ans_jsons, {"input_tokens": 0, "output_tokens": 0, "latency": 0}

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
