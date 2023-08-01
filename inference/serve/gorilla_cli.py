"""
Chat with a model with command line interface.

Usage:
python3 gorilla_cli.py --model-path path/to/gorilla-7b-hf-v0

Thanks to LMSYS for the template of this code.
"""
import argparse
import gc
import os
import re
import sys
import abc
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
from transformers.generation.logits_process import (
    LogitsProcessorList,
    RepetitionPenaltyLogitsProcessor,
    TemperatureLogitsWarper,
    TopKLogitsWarper,
    TopPLogitsWarper,
)

from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import InMemoryHistory
from conv_template import get_conv_template

import warnings
warnings.filterwarnings('ignore')

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
    elif device == "mps":
        kwargs = {"torch_dtype": torch.float16}
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
  
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        trust_remote_code=True,
        low_cpu_mem_usage=True,
        **kwargs,
    )

    return model, tokenizer

def prepare_logits_processor(
    temperature: float, repetition_penalty: float, top_p: float, top_k: int
):
    processor_list = LogitsProcessorList()

    if temperature >= 1e-5 and temperature != 1.0:
        processor_list.append(TemperatureLogitsWarper(temperature))
    if repetition_penalty > 1.0:
        processor_list.append(RepetitionPenaltyLogitsProcessor(repetition_penalty))
    if 1e-8 <= top_p < 1.0:
        processor_list.append(TopPLogitsWarper(top_p))
    if top_k > 0:
        processor_list.append(TopKLogitsWarper(top_k))
    return processor_list

@torch.inference_mode()
def get_response(prompt, model, tokenizer, device):

    logits_processor = prepare_logits_processor(
        0.1, 0.0, 1.0, -1
    )

    context_len = 2048
    max_new_tokens = 1024
    stream_interval=2
    input_ids = tokenizer(prompt).input_ids
    input_echo_len = len(input_ids)
    output_ids = list(input_ids)
    max_src_len = context_len - max_new_tokens - 8
    input_ids = input_ids[-max_src_len:]
    stop_token_ids = [tokenizer.eos_token_id]
    
    past_key_values = out = None
    for i in range(max_new_tokens):
        if i == 0:
            out = model(torch.as_tensor([input_ids], device=device),
                use_cache=True)
            logits = out.logits
            past_key_values = out.past_key_values
        else:
            out = model(
                input_ids=torch.as_tensor([[token]], device=device),
                use_cache=True,
                past_key_values=past_key_values,
            )
            logits = out.logits
            past_key_values = out.past_key_values

        tmp_output_ids = None
        last_token_logits = logits_processor(tmp_output_ids, logits[:, -1, :])[0]
        probs = torch.softmax(last_token_logits, dim=-1)
        token = int(torch.multinomial(probs, num_samples=1))
        output_ids.append(token)

        if token in stop_token_ids:
            stopped = True
        else:
            stopped = False

        if i % stream_interval == 0 or i == max_new_tokens - 1 or stopped:
            tmp_output_ids = output_ids[input_echo_len:]
            rfind_start = 0

            output = tokenizer.decode(
                tmp_output_ids,
                skip_special_tokens=True,
                spaces_between_special_tokens=False,
            )

            yield {
                "text": output
            }

        if stopped:
            break

    yield {"text": output}

    # clean
    del past_key_values, out
    gc.collect()
    torch.cuda.empty_cache()

class SimpleChatIO(abc.ABC):
    def prompt_for_input(self, role) -> str:
        return input(f"{role}: ")

    def prompt_for_output(self, role: str):
        print(f"{role}: ", end="", flush=True)

    def stream_output(self, output_stream):
        pre = 0
        for outputs in output_stream:
            output_text = outputs["text"]
            output_text = output_text.strip().split(" ")
            now = len(output_text) - 1
            if now > pre:
                print(" ".join(output_text[pre:now]), end=" ", flush=True)
                pre = now
        print(" ".join(output_text[pre:]), flush=True)
        return " ".join(output_text)

def chat_loop(
    model_path: str,
    device: str,
    num_gpus: int,
    max_gpu_memory: str,
    load_8bit: bool,
    cpu_offloading: bool,
    chatio: abc.ABC,
):
    # Model
    model, tokenizer = load_model(
        model_path, device, num_gpus, max_gpu_memory, load_8bit, cpu_offloading
    )
    if (args.device == "cuda" and args.num_gpus == 1 and not args.cpu_offloading) or args.device == "mps":
        model.to(args.device)

    while True:
        # Chat
        if "mpt" in model_path:
            conv = get_conv_template("mpt")
        elif "gorilla" in model_path:
            conv = get_conv_template("gorilla_v0")
        try:
            inp = chatio.prompt_for_input(conv.roles[0])
        except EOFError:
            inp = ""
        if not inp:
            print("exit...")
            break

        conv.append_message(conv.roles[0], inp)
        conv.append_message(conv.roles[1], None)
        prompt = conv.get_prompt()

        chatio.prompt_for_output(conv.roles[1])
        output_stream = get_response(prompt, model, tokenizer, device)
        outputs = chatio.stream_output(output_stream)
        conv.update_last_message(outputs.strip())

def main(args):
    if args.gpus:
        if len(args.gpus.split(",")) < args.num_gpus:
            raise ValueError(
                f"Larger --num-gpus ({args.num_gpus}) than --gpus {args.gpus}!"
            )
        os.environ["CUDA_VISIBLE_DEVICES"] = args.gpus

    chatio = SimpleChatIO()
    
    try:
        chat_loop(
            args.model_path,
            args.device,
            args.num_gpus,
            args.max_gpu_memory,
            args.load_8bit,
            args.cpu_offloading,
            chatio,
        )
    except KeyboardInterrupt:
        print("exit...")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--model-path", type=str, default=None, 
        help="Model path to the pretrained model."
    )
    parser.add_argument(
        "--gpus", type=str, default=None,
        help="A single GPU like 1 or multiple GPUs like 0,2."
    )
    parser.add_argument(
        "--num-gpus", 
        type=int, 
        default=1)
    parser.add_argument(
        "--device", type=str, default='cuda',
        help="Which device to use."
    )
    parser.add_argument(
        "--max-gpu-memory",
        type=str,
        help="The maximum memory per gpu. Use a string like '13Gib'",
    )
    parser.add_argument(
        "--load-8bit", action="store_true", help="Use 8-bit quantization"
    )
    parser.add_argument(
        "--cpu-offloading",
        action="store_true",
        help="Only when using 8-bit quantization: Offload excess weights to the CPU that don't fit on the GPU",
    )

    args = parser.parse_args()
    main(args)
