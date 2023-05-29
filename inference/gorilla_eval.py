import json
import argparse
import os
from tqdm import tqdm
import torch
from transformers import (
    AutoConfig,
    AutoModel,
    AutoModelForCausalLM,
    AutoModelForSeq2SeqLM,
    AutoTokenizer,
    LlamaTokenizer,
    LlamaForCausalLM,
    T5Tokenizer,
)

# Load Gorilla Model from HF
def load_model(
        model_path: str,
        device: str,
        num_gpus: int,
        max_gpu_memory: str = None,
        load_8bit: bool = False,
        cpu_offloading: bool = False,
    ):
 
    if device == "cpu":
        kwargs = {"torch_dtype": torch.float32}
    elif device == "cuda":
        kwargs = {"torch_dtype": torch.float16}
        if num_gpus != 1:
            kwargs["device_map"] = "auto"
            if max_gpu_memory is None:
                kwargs[
                    "device_map"
                ] = "sequential"  # This is important for not the same VRAM sizes
                available_gpu_memory = get_gpu_memory(num_gpus)
                kwargs["max_memory"] = {
                    i: str(int(available_gpu_memory[i] * 0.85)) + "GiB"
                    for i in range(num_gpus)
                }
            else:
                kwargs["max_memory"] = {i: max_gpu_memory for i in range(num_gpus)}
    else:
        raise ValueError(f"Invalid device: {device}")

    if cpu_offloading:
        # raises an error on incompatible platforms
        from transformers import BitsAndBytesConfig

        if "max_memory" in kwargs:
            kwargs["max_memory"]["cpu"] = (
                str(math.floor(psutil.virtual_memory().available / 2**20)) + "Mib"
            )
        kwargs["quantization_config"] = BitsAndBytesConfig(
            load_in_8bit_fp32_cpu_offload=cpu_offloading
        )
        kwargs["load_in_8bit"] = load_8bit
    elif load_8bit:
        if num_gpus != 1:
            warnings.warn(
                "8-bit quantization is not supported for multi-gpu inference."
            )
        else:
            return load_compress_model(
                model_path=model_path, device=device, torch_dtype=kwargs["torch_dtype"]
            )
  
    tokenizer = AutoTokenizer.from_pretrained(model_path, use_fast=False)
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        low_cpu_mem_usage=True,
        **kwargs,
    )

    return model, tokenizer

def get_questions(question_file):
 
    # Load questions file
    question_jsons = []
    with open(question_file, "r") as ques_file:
        for line in ques_file:
            question_jsons.append(line)

    return question_jsons

def run_eval(args, question_jsons):
    # Evaluate the model for answers
    model, tokenizer = load_model(
        args.model_path, args.device, args.num_gpus, args.max_gpu_memory, args.load_8bit, args.cpu_offloading
    )
    if (args.device == "cuda" and args.num_gpus == 1 and not args.cpu_offloading) or args.device == "mps":
        model.to(args.device)
    # model = model.to(args.device)

    ans_jsons = []
    for i, line in enumerate(tqdm(question_jsons)):
        ques_json = json.loads(line)
        idx = ques_json["question_id"]
        prompt = ques_json["text"]
        prompt = "###USER: " + prompt + "###ASSISTANT: "
        input_ids = tokenizer([prompt]).input_ids
        output_ids = model.generate(
            torch.as_tensor(input_ids).to(args.device),
            do_sample=True,
            temperature=0.7,
            max_new_tokens=2048,
        )
        output_ids = output_ids[0][len(input_ids[0]) :]
        outputs = tokenizer.decode(output_ids, skip_special_tokens=True).strip()
        ans_jsons.append(
            {
                "question_id": idx,
                "questions": prompt,
                "response": outputs,
            }
        )

    # Write output to file
    with open(args.answer_file, "w") as ans_file:
        for line in ans_jsons:
            ans_file.write(json.dumps(line) + "\n")

    return ans_jsons

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model-path", 
        type=str, 
        required=True)
    parser.add_argument(
        "--question-file", 
        type=str, 
        required=True)
    parser.add_argument(
        "--device", 
        type=str,
        choices=["cpu", "cuda", "mps"],
        default="cuda",
        help="The device type",
    )
    parser.add_argument(
        "--max-gpu-memory",
        type=str,
        help="The maximum memory per gpu. A string like '13Gib'",
    )
    parser.add_argument(
        "--load-8bit", 
        action="store_true", 
        help="Use 8-bit quantization"
    )
    parser.add_argument(
        "--cpu-offloading",
        action="store_true",
        help="Only when using 8-bit quantization: Offload excess weights to the CPU that don't fit on the GPU",
    )
    parser.add_argument(
        "--answer-file", 
        type=str, 
        default="answer.jsonl"
    )
    parser.add_argument(
        "--num-gpus", 
        type=int, 
        default=1
    )
    args = parser.parse_args()

    questions_json = get_questions(args.question_file)
    run_eval(
        args,
        questions_json
    )
 
