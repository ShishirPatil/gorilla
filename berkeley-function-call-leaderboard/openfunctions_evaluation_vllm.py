import argparse
import torch
import os
import json
from tqdm import tqdm
import shortuuid
import ray
from vllm import LLM, SamplingParams
import random

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
        python openfunctions_evaluation_vllm.py --model-path glaiveai/glaive-function-calling-v1 --model-id glaiveai --question-file eval_data_total.json --answer-file ./result/glaiveai/result.json --num-gpus 4
"""
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

    os.makedirs(os.path.dirname(answer_file), exist_ok=True)
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
        if model_id == "glaiveai":
            SYSTEM_PROMPT = """
                You are an helpful assistant who has access to the following functions to help the user, you can use the functions if needed-
            """
            if isinstance(ques_json["function"], list):
                for idx, func in enumerate(ques_json["function"]):
                    functions += "\n" + str(func)
            else:
                functions += "\n" + str(ques_json["function"])
            prompt = f"SYSTEM: {SYSTEM_PROMPT}\n{functions}\nUSER: {ques_json['question']}\nASSISTANT: "
            prompts.append(prompt)
        else:
            raise Exception('Model not supported yet 🦍')


        ans_id = shortuuid.uuid()
        ans_jsons.append(
                {
                    "answer_id": ans_id,
                    "question": ques_json["question"],
                }
            )

        
    print('start generating: ', len(prompts))
    sampling_params = SamplingParams(temperature=0.0, max_tokens=1024)
    llm = LLM(model=model_path, dtype="float16", trust_remote_code=True)
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