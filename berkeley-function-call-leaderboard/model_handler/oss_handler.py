from model_handler.handler import BaseHandler
from model_handler.model_style import ModelStyle
from model_handler.constant import MODEL_ID_DICT
from model_handler.utils import (
    ast_parse,
    augment_prompt_by_languge,
    language_specific_pre_processing,
)
from tqdm import tqdm
import shortuuid, ray, os, json, torch


class OSSHandler(BaseHandler):
    def __init__(self, model_name, temperature=0.7, top_p=1, max_tokens=1000) -> None:
        super().__init__(model_name, temperature, top_p, max_tokens)
        self.model_style = ModelStyle.OSSMODEL
        self._init_model()

    def _init_model(self):
        ray.init(ignore_reinit_error=True, num_cpus=8)

    def _format_prompt(prompt, function):
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

    @ray.remote(num_gpus=1)
    @torch.inference_mode()
    def _batch_generate(
        question_jsons,
        test_category,
        model_path,
        temperature,
        max_tokens,
        top_p,
        format_prompt_func,
    ):
        from vllm import LLM, SamplingParams

        prompts = []
        ans_jsons = []
        for line in question_jsons:
            ques_json = line
            prompt = augment_prompt_by_languge(ques_json["question"], test_category)
            functions = language_specific_pre_processing(
                ques_json["function"], test_category, False
            )
            prompts.append(format_prompt_func(prompt, functions, test_category))
            ans_id = shortuuid.uuid()
            ans_jsons.append(
                {
                    "answer_id": ans_id,
                    "question": ques_json["question"],
                }
            )

        print("start generating: ", len(prompts))
        sampling_params = SamplingParams(
            temperature=temperature, max_tokens=max_tokens, top_p=top_p
        )
        llm = LLM(model=model_path, dtype="float16", trust_remote_code=True)
        outputs = llm.generate(prompts, sampling_params)
        final_ans_jsons = []
        for output, ans_json in zip(outputs, ans_jsons):
            text = output.outputs[0].text
            ans_json["text"] = text
            final_ans_jsons.append(ans_json)
        return final_ans_jsons

    def inference(
        self, question_file, test_category, num_gpus, format_prompt_func=_format_prompt
    ):

        ques_jsons = []
        with open(question_file, "r") as ques_file:
            for line in ques_file:
                ques_jsons.append(json.loads(line))

        chunk_size = len(ques_jsons) // num_gpus
        ans_handles = []
        for i in range(0, len(ques_jsons), chunk_size):
            ans_handles.append(
                self._batch_generate.remote(
                    ques_jsons[i : i + chunk_size],
                    test_category,
                    self.model_name,
                    self.temperature,
                    self.max_tokens,
                    self.top_p,
                    format_prompt_func,
                )
            )
        ans_jsons = []
        for ans_handle in ans_handles:
            ans_jsons.extend(ray.get(ans_handle))

        return ans_jsons, {"input_tokens": 0, "output_tokens": 0, "latency": 0}

    def decode_ast(self, result, language="Python"):
        func = result.replace('", "', ",").replace('["', "[").replace('"]', "]")
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

    def write(self, result, file_to_open):
        if not os.path.exists("./result"):
            os.mkdir("./result")
        if not os.path.exists("./result/" + self.model_name.replace("/", "_")):
            os.mkdir("./result/" + self.model_name.replace("/", "_"))
        with open(
            "./result/" + self.model_name.replace("/", "_") + "/" + file_to_open, "a+"
        ) as f:
            f.write(json.dumps(result) + "\n")

    def load_result(self, test_category):
        eval_data = []
        with open("./eval_data_total.json") as f:
            for line in f:
                eval_data.append(json.loads(line))
        result_list = []
        idx = 0
        with open(f"./result/{self.model_name}/result.json") as f:
            for line in f:
                if eval_data[idx]["test_category"] == test_category:
                    result_list.append(json.loads(line))
                idx += 1
        return result_list
