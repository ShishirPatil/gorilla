import argparse
import os
from typing import Optional
from fastapi import FastAPI
from pydantic import BaseModel
import torch
import uvicorn
from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer
from copy import deepcopy

app = FastAPI()

model = None
tokenizer = None
custom_generation_func = None

class ExtraBody(BaseModel):
    stop_token_ids: list[int] = None
    skip_special_tokens: bool = None

class Request(BaseModel):
    model: str
    temperature: float
    prompt: str
    max_tokens: int
    extra_body: ExtraBody = None
    timeout: int = 72000

@app.get("/v1/models")
async def list_models():
    return {
        "object": "list",
        "data": [
            {
                "id": "local-model",
                "object": "model",
                "created": 0,
                "owned_by": "local",
            }
        ]
    }

@app.post("/v1/completions")
async def create(request: Request):

    try:
        inputs = tokenizer(request.prompt, return_tensors="pt", add_special_tokens=False)
        inputs = {k: v.to(model.device) for k, v in inputs.items()}
        model.generation_config.temperature = request.temperature
        output = model.generate(
            **inputs, 
            max_length=request.max_tokens, 
            custom_generate=custom_generation_func,
            trust_remote_code=True,
        )
        result = tokenizer.decode(output, skip_special_tokens=False)
        return {
            "choices": [{
                "finish_reason": "stop",
                "index": 0,
                "logprobs": None,
                "text": result
            }],
            "id": "chatcmpl-123",
            "object": "text_completion",
            "model": request.model,
            "usage": {
                "prompt_tokens": len(inputs["input_ids"][0]),
                "completion_tokens": len(output) - len(inputs["input_ids"][0]),
                "total_tokens": len(output),
            }
        }
    except Exception as e:
        result = f"Error during generation: {str(e)}"
        {
            "choices": [{
                "finish_reason": "stop",
                "index": 0,
                "logprobs": None,
                "text": result
            }],
            "id": "chatcmpl-123",
            "object": "text_completion",
            "model": request.model,
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
            }
        }


def setup_model(
    model_path_or_id: str, 
    dtype: str = None,
    tensor_parallel_size: int = 0,
    local_files_only: Optional[bool] = None, 
    trust_remote_code: bool = False,
    custom_generation: Optional[str] = None,
    enable_lora: Optional[bool] = None,
    max_lora_rank: Optional[int] = 0,
    lora_modules: Optional[list[str]] = [],
):
    global model, tokenizer, custom_generation_func

    # Set custom generation function if specified
    if custom_generation is not None:
        custom_generation_func = custom_generation

    # Setup tokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        model_path_or_id, 
        trust_remote_code=trust_remote_code, 
        use_fast=False
    )

    # Setup model
    if tensor_parallel_size == 0:
        device_map = "cpu"
    elif torch.cuda.is_available():
        device_map = "auto"
    else:
        raise ValueError("Tensor parallel size > 0 requires CUDA, but CUDA is not available.")

    if enable_lora:
        # TODO: support LoRA loading with PEFT
        raise NotImplementedError("LoRA loading is not yet implemented for local deployment.")
    else:
        config = AutoConfig.from_pretrained(model_path_or_id, trust_remote_code=trust_remote_code, dtype=dtype)
        model = AutoModelForCausalLM.from_pretrained(
            model_path_or_id,
            dtype=config.dtype,
            device_map=device_map,
            local_files_only=local_files_only, 
            trust_remote_code=trust_remote_code
        )
        
    model.eval()



def main(
    model_path_or_id: str,
    port: int = 8000,
    dtype: str = None,
    tensor_parallel_size: int = 0,
    trust_remote_code: bool = False,
    local_files_only: bool = False,
    custom_generation: str = None,
    enable_lora: bool = False,
    max_lora_rank: Optional[int] = 0,
    lora_modules: Optional[list[str]] = [],
):
    
    # Setup the model and tokenizer
    setup_model(
        model_path_or_id=model_path_or_id, 
        dtype=dtype, 
        tensor_parallel_size=tensor_parallel_size, 
        local_files_only=local_files_only, 
        trust_remote_code=trust_remote_code,
        custom_generation=custom_generation,
        enable_lora=enable_lora,
        max_lora_rank=max_lora_rank,
        lora_modules=lora_modules,
    )
    
    # Start the local server
    uvicorn.run(app, host="localhost", port=port)


def parse_args():
    parser = argparse.ArgumentParser(description="Run the FastAPI server.")
    parser.add_argument("--model-path-or-id", type=str, required=True, help="The model ID to load.")
    parser.add_argument("--port", type=int, default=8000, help="The port to run the server on.")
    parser.add_argument("--dtype", type=str, default=None, help="The dtype to load the model with.")
    parser.add_argument("--tensor-parallel-size", type=int, default=0, help="The tensor parallel size to load the model with. If 0, cpu is selected.")
    parser.add_argument("--trust-remote-code", action="store_true", help="Whether to trust remote code when loading the model.")
    parser.add_argument("--local-files-only", action="store_true", help="Whether to only load local files when loading the model.")
    parser.add_argument("--custom-generation", type=str, default=None, help="The custom generation function to use. If not specified, the default generation function is used.")
    parser.add_argument("--enable-lora", action="store_true", help="Whether to enable LoRA when loading the model.")
    parser.add_argument("--max-lora-rank", type=int, default=0, help="The max LoRA rank to use when loading the model. If 0, no limit is applied.")
    parser.add_argument("--lora-modules", type=str, nargs="*", default=[], help="The LoRA modules to load when loading the model. If empty, all modules are loaded.")
    return vars(parser.parse_args())

if __name__ == "__main__":
    args = parse_args()
    main(**args)