import argparse
import torch
import os
import json
from tqdm import tqdm
import shortuuid
import ray
from vllm import LLM, SamplingParams
import random
from fastchat.model import get_conversation_template

"""
    This script is used to evaluate the OSS model using the VLLM model.
    Inputs:
        - model_path: The path to the VLLM model
        - model_id: The model id of the VLLM model
        - question_file: The file containing the questions to be evaluated
        - answer_file: The file to save the answers
        - num_gpus: The number of gpus to use for evaluation
    Outputs:
        - answer_file: The file containing the answers
    Example usage:
        python openfunctions/openfunctions_evaluation_vllm.py \
            --model-path "./model/gorilla-openfunctions-v2/" \
            --model-id "gorilla-openfunctions-v2" \
            --question-file "eval_data_total.json" \
            --answer-file "./result/gorilla-openfunctions-v2/result.json" \
            --num-gpus 1
"""
N_DOCS = 100
N_SAMPLES = 3
def run_eval(model_path, model_id, question_file, answer_file, num_gpus):
    # split question file into num_gpus files
    ques_jsons = []
    with open(os.path.expanduser(question_file), "r") as ques_file:
        for line in ques_file:
            ques_jsons.append(line)
   
    retriever = None

    chunk_size = len(ques_jsons) // num_gpus
    ans_handles = []
    for i in range(0, len(ques_jsons), chunk_size):
        ans_handles.append(
            get_model_answers.remote(
                model_path, model_id, ques_jsons[i : i + chunk_size]
            )
        )

    ans_jsons = []
    for ans_handle in ans_handles:
        ans_jsons.extend(ray.get(ans_handle))

    with open(os.path.expanduser(answer_file), "w") as ans_file:
        for line in ans_jsons:
            ans_file.write(json.dumps(line) + "\n")


@ray.remote(num_gpus=1)
@torch.inference_mode()
def get_model_answers(model_path, model_id, question_jsons):
    model_path = os.path.expanduser(model_path)
    # tokenizer = AutoTokenizer.from_pretrained(model_path, use_fast=False)

    ans_jsons = []
    prompts = []
    for i, line in enumerate(question_jsons):
        ques_json = json.loads(line)
        functions = ""
        SYSTEM_PROMPT_FOR_CHAT_MODEL = """"
            You are an expert in composing functions. You are given a question and a set of possible functions. 
            Based on the question, you will need to make one or more function/tool calls to achieve the purpose. 
            If none of the function can be used, point it out. If the given question lacks the parameters required by the function,
            also point it out. You should only return the function call in tools call sections.
            Put it in the format of [func1(params_name=params_value, params_name2=params_value2...), func2(params)]
            """
        if isinstance(ques_json["function"], list):
            for idx, func in enumerate(ques_json["function"]):
                functions += "\n<<function" + str(idx) + ">> " + str(func)
        else:
            functions += "\n<<function0>>" + str(ques_json["function"])
        prompt = f"{SYSTEM_PROMPT_FOR_CHAT_MODEL}\n### Instruction: <<function>>{functions}\n<<question>>{ques_json["question"]}\n### Response: "
        conv = get_conversation_template(model_id)
        conv.append_message(conv.roles[0], prompt)
        conv.append_message(conv.roles[1], None)
        prompt = conv.get_prompt()
        prompts.append(prompt)

        ans_id = shortuuid.uuid()
        ans_jsons.append(
                {
                    "answer_id": ans_id,
                    "question": ques_json["question"],
                }
            )

        '''
        if "human_eval_answer" in ques_json.keys():
            ans_jsons.append(
                {
                    "answer_id": ans_id,
                    "question": ques_json["question"],
                    "function": ques_json['function'],
                    "ground_truth": ques_json["human_eval_answer"]
                }
            )
        else:
            ans_jsons.append(
                {
                    "answer_id": ans_id,
                    "question": ques_json["question"],
                    "function": ques_json['function'],
                    "ground_truth": ques_json["answer"]
                }
            )
        '''

    print('start generating: ', len(prompts))
    sampling_params = SamplingParams(temperature=0.0, max_tokens=1024)
    llm = LLM(model=model_path, dtype="float16")
    outputs = llm.generate(prompts, sampling_params)
    final_ans_jsons = []
    for output, ans_json in zip(outputs, ans_jsons):
        text = output.outputs[0].text
        ans_json["text"] = text
        final_ans_jsons.append(ans_json)
    return final_ans_jsons


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-path", type=str, required=True)
    parser.add_argument("--model-id", type=str, required=True)
    parser.add_argument("--question-file", type=str, required=True)
    parser.add_argument("--answer-file", type=str, default="answer.jsonl")
    parser.add_argument("--num-gpus", type=int, default=1)
    args = parser.parse_args()

    ray.init(ignore_reinit_error=True, num_cpus=8)
    run_eval(
        args.model_path,
        args.model_id,
        args.question_file,
        args.answer_file,
        args.num_gpus,
    )
