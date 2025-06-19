import os
import subprocess
import threading
import time
import warnings
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, List, Union

import requests
from bfcl_eval.constants.eval_config import RESULT_PATH
from bfcl_eval.model_handler.local_inference.base_oss_handler import OSSHandler
from overrides import override
from tqdm import tqdm


class ConfigStatus(Enum):
    WORKING = "working"
    BROKEN = "broken"
    UNTESTED = "untested"


@dataclass(frozen=True)
class TensorParallelConfig:
    tensor_parallel_size: int
    memory_per_gpu_gb: float
    total_memory_gb: float
    supported_gpus: List[str]
    expected_speedup: float
    status: ConfigStatus
    limitations: List[str]
    
    def __post_init__(self):
        phi4_kv_heads = 8
        if phi4_kv_heads % self.tensor_parallel_size != 0:
            raise ValueError(
                f"tensor_parallel_size={self.tensor_parallel_size} incompatible with "
                f"Phi-4's {phi4_kv_heads} KV heads"
            )


@dataclass
class PerformanceMetrics:
    request_latency_ms: float
    gpu_utilization_avg: float
    gpu_memory_used_gb: float
    gpu_memory_total_gb: float
    tensor_parallel_efficiency: float
    kv_cache_utilization: float
    timestamp: float


class TensorParallelPresets:
    SINGLE_GPU = TensorParallelConfig(
        tensor_parallel_size=1,
        memory_per_gpu_gb=16.0,
        total_memory_gb=16.0,
        supported_gpus=["RTX 4090", "A6000", "A40", "A100-40GB", "A100-80GB"],
        expected_speedup=1.0,
        status=ConfigStatus.WORKING,
        limitations=[]
    )
    DUAL_GPU = TensorParallelConfig(
        tensor_parallel_size=2,
        memory_per_gpu_gb=9.0,
        total_memory_gb=18.0,
        supported_gpus=["RTX 3090", "RTX 4080", "A5000", "A40"],
        expected_speedup=1.8,
        status=ConfigStatus.WORKING,
        limitations=[]
    )
    QUAD_GPU = TensorParallelConfig(
        tensor_parallel_size=4,
        memory_per_gpu_gb=5.5,
        total_memory_gb=22.0,
        supported_gpus=["RTX 3070", "RTX 4070", "A10G"],
        expected_speedup=3.2,
        status=ConfigStatus.BROKEN,
        limitations=["vLLM Issue #16021: assert self.total_num_kv_heads % tp_size == 0"]
    )
    OCTA_GPU = TensorParallelConfig(
        tensor_parallel_size=8,
        memory_per_gpu_gb=3.8,
        total_memory_gb=30.4,
        supported_gpus=["RTX 3060", "A10", "T4"],
        expected_speedup=5.5,
        status=ConfigStatus.UNTESTED,
        limitations=["Requires vLLM fix", "Cross-GPU communication overhead"]
    )
    @classmethod
    def get_all_configs(cls) -> Dict[int, TensorParallelConfig]:
        return {
            1: cls.SINGLE_GPU,
            2: cls.DUAL_GPU,
            4: cls.QUAD_GPU,
            8: cls.OCTA_GPU,
        }
    @classmethod
    def get_working_configs(cls) -> Dict[int, TensorParallelConfig]:
        all_configs = cls.get_all_configs()
        return {
            tp_size: config for tp_size, config in all_configs.items()
            if config.status == ConfigStatus.WORKING
        }
    @classmethod
    def get_optimal_config(
        cls, 
        available_gpus: int, 
        memory_per_gpu_gb: float,
        allow_broken: bool = False
    ) -> Optional[TensorParallelConfig]:
        configs = cls.get_all_configs() if allow_broken else cls.get_working_configs()
        suitable_configs = []
        for tp_size, config in configs.items():
            if (tp_size <= available_gpus and 
                config.memory_per_gpu_gb <= memory_per_gpu_gb):
                suitable_configs.append((tp_size, config))
        if not suitable_configs:
            return None
        best_tp_size, best_config = max(suitable_configs, key=lambda x: x[1].expected_speedup)
        return best_config


class Phi4VllmHandler(OSSHandler):
    """
    vLLM-optimized handler for Microsoft Phi-4 models.
    
    Supports tensor-parallel configurations and vLLM-specific optimizations
    for Phi-4's GQA architecture with 8 KV heads.
    """

    def __init__(
        self,
        model_name: str,
        temperature: float,
        tensor_parallel_size: int = 1,
        max_model_len: Optional[int] = None,
        gpu_memory_utilization: float = 0.9,
        dtype: str = "bfloat16",
        auto_config: bool = False,
        available_gpus: Optional[int] = None,
        memory_per_gpu_gb: Optional[float] = None,
        enable_phi4_optimizations: bool = True,
        kv_cache_dtype: str = "auto",
        enable_prefix_caching: bool = True,
        max_num_seqs: Optional[int] = None,
        enforce_eager: bool = False
    ) -> None:
        super().__init__(model_name, temperature, dtype)
        if auto_config:
            self.tp_config = self._auto_select_config(available_gpus, memory_per_gpu_gb)
            self.tensor_parallel_size = self.tp_config.tensor_parallel_size
        else:
            self.tensor_parallel_size = tensor_parallel_size
            self.tp_config = self._get_config_for_tp_size(tensor_parallel_size)
        self.max_model_len = max_model_len
        self.gpu_memory_utilization = gpu_memory_utilization
        self.enable_phi4_optimizations = enable_phi4_optimizations
        self.kv_cache_dtype = kv_cache_dtype
        self.enable_prefix_caching = enable_prefix_caching
        self.max_num_seqs = max_num_seqs
        self.enforce_eager = enforce_eager
        self._setup_phi4_optimizations()
        self._validate_configuration()
        self._init_performance_monitoring()
        print(f"✅ Phi-4 vLLM Handler initialized:")
        print(f"  - Tensor Parallel: {self.tensor_parallel_size} GPUs")
        print(f"  - Status: {self.tp_config.status.value}")
        print(f"  - Expected Speedup: {self.tp_config.expected_speedup}x")
        if self.tp_config.limitations:
            print(f"  - ⚠️ Limitations: {', '.join(self.tp_config.limitations)}")

    def _setup_phi4_optimizations(self) -> None:
        if not self.enable_phi4_optimizations:
            return
        self.is_phi4_mini = "mini" in self.model_name.lower()
        if self.max_model_len is None:
            self.max_model_len = 8192 if self.tensor_parallel_size > 1 else 16384
        if self.max_num_seqs is None:
            if self.tensor_parallel_size == 1:
                self.max_num_seqs = 256
            elif self.tensor_parallel_size == 2:
                self.max_num_seqs = 128
            else:
                self.max_num_seqs = 64
        if self.tp_config.tensor_parallel_size > 1:
            self.gpu_memory_utilization = min(self.gpu_memory_utilization, 0.85)
        self._setup_prompt_optimizations()

    def _setup_prompt_optimizations(self) -> None:
        if self.is_phi4_mini:
            self.system_template = "<|system|>{content}<|end|>"
            self.user_template = "<|user|>{content}<|end|>"
            self.assistant_template = "<|assistant|>{content}<|end|>"
            self.assistant_start = "<|assistant|>"
        else:
            self.system_template = "<|im_start|>system<|im_sep|>{content}<|im_end|>"
            self.user_template = "<|im_start|>user<|im_sep|>{content}<|im_end|>"
            self.assistant_template = "<|im_start|>assistant<|im_sep|>{content}<|im_end|>"
            self.assistant_start = "<|im_start|>assistant<|im_sep|>"
        self._prompt_cache = {}
        self._tokenizer_cache = None
        self._max_prompt_tokens = int(self.max_model_len * 0.85)

    def _validate_configuration(self) -> None:
        self._validate_tensor_parallel_config()
        if not any(phi_variant in self.model_name.lower() for phi_variant in ["phi-4", "phi4"]):
            warnings.warn(
                f"Model name '{self.model_name}' does not appear to be Phi-4. "
                f"This handler is optimized specifically for Phi-4 models.",
                UserWarning
            )
        supported_dtypes = ["bfloat16", "float16", "float32"]
        if self.dtype not in supported_dtypes:
            raise ValueError(
                f"Unsupported dtype '{self.dtype}'. Supported: {supported_dtypes}"
            )
        if not 0.1 <= self.gpu_memory_utilization <= 1.0:
            raise ValueError(
                f"gpu_memory_utilization must be between 0.1 and 1.0, got {self.gpu_memory_utilization}"
            )
        if self.max_model_len is not None and self.max_model_len > 32768:
            warnings.warn(
                f"max_model_len={self.max_model_len} is very large for Phi-4. "
                f"Consider using 16384 or less for optimal performance.",
                UserWarning
            )
        if self.tp_config.status == ConfigStatus.BROKEN:
            raise ValueError(
                f"tensor_parallel_size={self.tensor_parallel_size} is currently broken in vLLM. "
                f"Limitations: {', '.join(self.tp_config.limitations)}. "
                f"Please use a working configuration: {list(TensorParallelPresets.get_working_configs().keys())}"
            )

    def get_vllm_server_args(self, backend: str = "vllm") -> List[str]:
        if backend not in ["vllm", "sglang"]:
            raise ValueError(f"Unsupported backend: {backend}")
        if backend == "vllm":
            args = [
                "vllm", "serve", str(self.model_path_or_id),
                "--port", str(self.vllm_port),
                "--dtype", str(self.dtype),
                "--tensor-parallel-size", str(self.tensor_parallel_size),
                "--gpu-memory-utilization", str(self.gpu_memory_utilization),
                "--trust-remote-code",
                "--kv-cache-dtype", self.kv_cache_dtype,
                "--max-model-len", str(self.max_model_len),
                "--max-num-seqs", str(self.max_num_seqs),
            ]
            if self.enable_phi4_optimizations:
                args.extend([
                    "--enable-chunked-prefill",
                    "--max-num-batched-tokens", str(self.max_model_len * 2),
                ])
                if self.enable_prefix_caching:
                    args.append("--enable-prefix-caching")
                if self.enforce_eager:
                    args.append("--enforce-eager")
                args.extend([
                    "--num-scheduler-slots", str(self.max_num_seqs * 2),
                ])
        else:
            args = [
                "python", "-m", "sglang.launch_server",
                "--model-path", str(self.model_path_or_id),
                "--port", str(self.vllm_port),
                "--dtype", str(self.dtype),
                "--tp", str(self.tensor_parallel_size),
                "--mem-fraction-static", str(self.gpu_memory_utilization),
                "--trust-remote-code",
            ]
            if self.max_model_len:
                args.extend(["--context-length", str(self.max_model_len)])
        return args

    def _calculate_optimal_memory_utilization(self, base_utilization: float) -> float:
        optimal = base_utilization
        if self.tensor_parallel_size > 1:
            optimal = min(optimal, 0.85)
        if self.max_model_len > 16384:
            optimal = min(optimal, 0.8)
        elif self.max_model_len > 8192:
            optimal = min(optimal, 0.85)
        if self.max_num_seqs > 128:
            optimal = min(optimal, 0.85)
        elif self.max_num_seqs > 256:
            optimal = min(optimal, 0.8)
        optimal = max(0.6, min(0.95, optimal))
        if optimal != base_utilization:
            print(f"🔧 Phi-4 Memory optimization: {base_utilization:.2f} → {optimal:.2f}")
        return optimal

    def _launch_optimized_vllm_server(
        self, 
        backend: str,
        skip_server_setup: bool
    ) -> Optional[subprocess.Popen]:
        if skip_server_setup:
            return None
        effective_tp_size = self.tensor_parallel_size
        optimal_memory = self._calculate_optimal_memory_utilization(self.gpu_memory_utilization)
        print(f"🚀 Launching Phi-4 optimized {backend} server:")
        print(f"  - Model: {self.model_path_or_id}")
        print(f"  - Tensor Parallel: {effective_tp_size} GPUs")
        print(f"  - Memory Utilization: {optimal_memory:.1%}")
        print(f"  - Context Length: {self.max_model_len}")
        print(f"  - Batch Size: {self.max_num_seqs}")
        print(f"  - KV Cache: {self.kv_cache_dtype}")
        if self.tp_config.status == ConfigStatus.BROKEN:
            raise RuntimeError(
                f"Cannot launch server with broken tensor-parallel configuration. "
                f"Limitations: {', '.join(self.tp_config.limitations)}"
            )
        server_args = self.get_vllm_server_args(backend)
        if backend == "vllm":
            for i, arg in enumerate(server_args):
                if arg == "--gpu-memory-utilization" and i + 1 < len(server_args):
                    server_args[i + 1] = str(optimal_memory)
                    break
        else:
            for i, arg in enumerate(server_args):
                if arg == "--mem-fraction-static" and i + 1 < len(server_args):
                    server_args[i + 1] = str(optimal_memory)
                    break
        print(f"📋 Server command: {' '.join(server_args[:8])}... ({len(server_args)} total args)")
        try:
            process = subprocess.Popen(
                server_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            print(f"✅ Server process started (PID: {process.pid})")
            return process
        except Exception as e:
            raise RuntimeError(f"Failed to launch Phi-4 vLLM server: {e}")

    def launch_phi4_batch_inference(
        self,
        test_entries: list[dict],
        num_gpus: int,
        gpu_memory_utilization: float,
        backend: str,
        skip_server_setup: bool,
        local_model_path: Optional[str],
        include_input_log: bool,
        exclude_state_log: bool,
        update_mode: bool,
        result_dir=RESULT_PATH,
    ):
        print("🚀 Starting Phi-4 optimized batch inference...")
        if not skip_server_setup:
            if num_gpus != self.tensor_parallel_size:
                print(f"⚠️ GPU count mismatch: requested {num_gpus}, configured {self.tensor_parallel_size}")
                available_memory = gpu_memory_utilization * 24.0
                optimal_config = TensorParallelPresets.get_optimal_config(
                    available_gpus=num_gpus,
                    memory_per_gpu_gb=available_memory,
                    allow_broken=False
                )
                if optimal_config:
                    self.tensor_parallel_size = optimal_config.tensor_parallel_size
                    self.tp_config = optimal_config
                    print(f"🔄 Auto-adjusted to {self.tensor_parallel_size} GPU configuration")
        print(f"📊 Phi-4 Configuration Summary:")
        print(f"  - Tensor Parallel: {self.tensor_parallel_size} GPUs") 
        print(f"  - Context Length: {self.max_model_len}")
        print(f"  - Batch Size: {self.max_num_seqs}")
        print(f"  - Memory Utilization: {self.gpu_memory_utilization:.1%}")
        print(f"  - KV Cache: {self.kv_cache_dtype}")
        print(f"  - Optimizations: {'Enabled' if self.enable_phi4_optimizations else 'Disabled'}")
        return super().batch_inference(
            test_entries=test_entries,
            num_gpus=self.tensor_parallel_size,
            gpu_memory_utilization=self._calculate_optimal_memory_utilization(gpu_memory_utilization),
            backend=backend,
            skip_server_setup=skip_server_setup,
            local_model_path=local_model_path,
            include_input_log=include_input_log,
            exclude_state_log=exclude_state_log,
            update_mode=update_mode,
            result_dir=result_dir,
        )

    def _auto_select_config(
        self, 
        available_gpus: Optional[int], 
        memory_per_gpu_gb: Optional[float]
    ) -> TensorParallelConfig:
        if available_gpus is None or memory_per_gpu_gb is None:
            raise ValueError(
                "auto_config=True requires available_gpus and memory_per_gpu_gb parameters"
            )
        config = TensorParallelPresets.get_optimal_config(
            available_gpus=available_gpus,
            memory_per_gpu_gb=memory_per_gpu_gb,
            allow_broken=False
        )
        if config is None:
            raise ValueError(
                f"No suitable tensor-parallel configuration found for "
                f"{available_gpus} GPUs with {memory_per_gpu_gb}GB memory each"
            )
        return config

    def _get_config_for_tp_size(self, tp_size: int) -> TensorParallelConfig:
        all_configs = TensorParallelPresets.get_all_configs()
        if tp_size not in all_configs:
            supported_sizes = list(all_configs.keys())
            raise ValueError(
                f"tensor_parallel_size={tp_size} not supported. "
                f"Supported sizes: {supported_sizes}"
            )
        config = all_configs[tp_size]
        if config.status != ConfigStatus.WORKING:
            warnings.warn(
                f"tensor_parallel_size={tp_size} status: {config.status.value}. "
                f"Limitations: {', '.join(config.limitations)}",
                UserWarning
            )
        return config

    def get_config_info(self) -> str:
        config = self.tp_config
        info = f"""
Phi-4 Tensor Parallel Configuration:
  - Tensor Parallel Size: {config.tensor_parallel_size}
  - Memory per GPU: {config.memory_per_gpu_gb}GB
  - Total Memory: {config.total_memory_gb}GB
  - Expected Speedup: {config.expected_speedup}x
  - Status: {config.status.value}
  - Supported GPUs: {', '.join(config.supported_gpus)}
"""
        if config.limitations:
            info += f"  - Limitations: {', '.join(config.limitations)}\n"
        return info

    def _validate_tensor_parallel_config(self) -> None:
        phi4_kv_heads = 8
        if phi4_kv_heads % self.tensor_parallel_size != 0:
            raise ValueError(
                f"tensor_parallel_size={self.tensor_parallel_size} is incompatible with "
                f"Phi-4's {phi4_kv_heads} KV heads. Must be one of: [1, 2, 4, 8]"
            )

    @override
    def _format_prompt(self, messages, function):
        cache_key = self._create_prompt_cache_key(messages, function)
        if cache_key in self._prompt_cache:
            return self._prompt_cache[cache_key]
        prompt_parts = []
        has_functions = function and len(function) > 0
        has_system_msgs = self._has_system_messages(messages)
        if has_functions or has_system_msgs:
            system_content = self._build_system_content(messages, function)
            if system_content:
                prompt_parts.append(self._format_message("system", system_content))
        for message in messages:
            if message["role"] == "system" and (has_functions or has_system_msgs):
                continue
            prompt_parts.append(self._format_message(message["role"], message["content"]))
        prompt_parts.append(self.assistant_start)
        formatted_prompt = "".join(prompt_parts)
        if self._validate_prompt_length(formatted_prompt):
            self._prompt_cache[cache_key] = formatted_prompt
            return formatted_prompt
        else:
            return self._truncate_prompt_for_vllm(messages, function)

    def _create_prompt_cache_key(self, messages, function) -> str:
        import hashlib
        message_str = str([(m["role"], m["content"][:100]) for m in messages])
        function_str = str([f.get("name", "") for f in function]) if function else ""
        combined = f"{message_str}:{function_str}:{self.is_phi4_mini}"
        return hashlib.md5(combined.encode()).hexdigest()[:16]

    def _build_system_content(self, messages, function) -> str:
        system_parts = []
        for message in messages:
            if message["role"] == "system":
                system_parts.append(message["content"])
        if function:
            func_descriptions = []
            for func in function:
                if isinstance(func, dict) and "name" in func:
                    func_desc = f"Function: {func['name']}"
                    if "description" in func:
                        func_desc += f" - {func['description']}"
                    if "parameters" in func:
                        func_desc += f"\nParameters: {func['parameters']}"
                    func_descriptions.append(func_desc)
            if func_descriptions:
                functions_text = "Available functions:\n" + "\n\n".join(func_descriptions)
                system_parts.append(functions_text)
        return "\n\n".join(system_parts) if system_parts else ""

    def _has_system_messages(self, messages) -> bool:
        return any(msg["role"] == "system" for msg in messages)

    def _format_message(self, role: str, content: str) -> str:
        if role == "system":
            return self.system_template.format(content=content) + "\n"
        elif role == "user":
            return self.user_template.format(content=content) + "\n"
        elif role == "assistant":
            return self.assistant_template.format(content=content) + "\n"
        else:
            if self.is_phi4_mini:
                return f"<|{role}|>{content}<|end|>\n"
            else:
                return f"<|im_start|>{role}<|im_sep|>{content}<|im_end|>\n"

    def _validate_prompt_length(self, prompt: str) -> bool:
        if not hasattr(self, 'tokenizer') or self.tokenizer is None:
            estimated_tokens = len(prompt) // 4
            return estimated_tokens <= self._max_prompt_tokens
        try:
            tokens = self.tokenizer.encode(prompt, add_special_tokens=False)
            return len(tokens) <= self._max_prompt_tokens
        except Exception:
            estimated_tokens = len(prompt) // 4
            return estimated_tokens <= self._max_prompt_tokens

    def _truncate_prompt_for_vllm(self, messages, function) -> str:
        system_content = self._build_system_content(messages, function)
        truncated_messages = []
        if system_content:
            truncated_messages.append({"role": "system", "content": system_content})
        conversation_messages = [m for m in messages if m["role"] != "system"]
        for message in reversed(conversation_messages):
            test_messages = [{"role": "system", "content": system_content}] + \
                          [message] + truncated_messages[1:]
            test_prompt = self._format_prompt_simple(test_messages)
            if self._validate_prompt_length(test_prompt):
                truncated_messages.insert(-1 if len(truncated_messages) > 1 else 1, message)
            else:
                break
        return self._format_prompt_simple(truncated_messages)

    def _format_prompt_simple(self, messages) -> str:
        prompt_parts = []
        for message in messages:
            prompt_parts.append(self._format_message(message["role"], message["content"]))
        prompt_parts.append(self.assistant_start)
        return "".join(prompt_parts)

    @override
    def decode_ast(self, result, language="Python"):
        return super().decode_ast(result, language)

    @override
    def decode_execute(self, result):
        return super().decode_execute(result)

    def _get_vllm_engine_args(self) -> dict:
        engine_args = {
            "tensor_parallel_size": self.tensor_parallel_size,
            "gpu_memory_utilization": self.gpu_memory_utilization,
            "dtype": self.dtype,
            "trust_remote_code": True,
        }
        if self.max_model_len is not None:
            engine_args["max_model_len"] = self.max_model_len
        return engine_args

    def _optimize_kv_cache_config(self) -> dict:
        return {
            "enable_prefix_caching": True,
            "kv_cache_dtype": "auto",
        }

    def _get_tensor_parallel_strategy(self) -> str:
        if self.tensor_parallel_size <= 2:
            return "standard"
        elif self.tensor_parallel_size <= 4:
            return "experimental"
        else:
            return "advanced"
    
    @override
    def _parse_query_response_prompting(self, api_response: any) -> dict:
        try:
            request_latency_ms = self._calculate_request_latency()
            raw_response = api_response.choices[0].text
            cleaned_response = self._clean_phi4_response(raw_response)
            
            if self._monitoring_enabled:
                performance_metrics = self._collect_performance_metrics(request_latency_ms)
                performance_summary = self._get_performance_summary()
            else:
                performance_metrics = None
                performance_summary = {}
            
            response_metadata = self._extract_response_metadata(api_response)
            if performance_metrics:
                response_metadata.update({
                    "performance_metrics": {
                        "request_latency_ms": performance_metrics.request_latency_ms,
                        "gpu_utilization_avg": performance_metrics.gpu_utilization_avg,
                        "gpu_memory_used_gb": performance_metrics.gpu_memory_used_gb,
                        "tensor_parallel_efficiency": performance_metrics.tensor_parallel_efficiency,
                        "kv_cache_utilization": performance_metrics.kv_cache_utilization,
                    },
                    "performance_summary": performance_summary,
                })
            
            return {
                "model_responses": cleaned_response,
                "input_token": self._safe_token_count(api_response.usage.prompt_tokens),
                "output_token": self._safe_token_count(api_response.usage.completion_tokens),
                "tensor_parallel_size": self.tensor_parallel_size,
                "response_metadata": response_metadata,
            }
            
        except Exception as e:
            return self._handle_parsing_error(api_response, e)
    
    def _calculate_request_latency(self) -> float:
        if self._request_start_time is None:
            return 0.0
        return (time.perf_counter() - self._request_start_time) * 1000
    
    def _clean_phi4_response(self, raw_response: str) -> str:
        """Clean phi-4 specific response artifacts with caching."""
        if not raw_response:
            return ""
            
        cache_key = hash(raw_response[:100])
        if hasattr(self, '_response_cache') and cache_key in self._response_cache:
            return self._response_cache[cache_key]
            
        if not hasattr(self, '_response_cache'):
            self._response_cache = {}
            
        cleaned = raw_response
        
        if self.is_phi4_mini:
            cleaned = self._clean_phi4_mini_response(cleaned)
        else:
            cleaned = self._clean_phi4_standard_response(cleaned)
            
        cleaned = self._remove_reasoning_traces(cleaned)
        cleaned = self._normalize_whitespace(cleaned)
        
        if len(self._response_cache) < 1000:
            self._response_cache[cache_key] = cleaned
            
        return cleaned
    
    def _clean_phi4_mini_response(self, response: str) -> str:
        """Clean phi-4-mini specific template markers."""
        patterns = [
            (r'<\|end\|>.*?$', ''),
            (r'<\|assistant\|>', ''),
            (r'<\|user\|>', ''),
            (r'<\|system\|>', ''),
        ]
        
        for pattern, replacement in patterns:
            response = self._safe_regex_sub(pattern, replacement, response)
            
        return response.strip()
    
    def _clean_phi4_standard_response(self, response: str) -> str:
        """Clean standard phi-4 template markers."""
        patterns = [
            (r'<\|im_end\|>.*?$', ''),
            (r'<\|im_start\|>assistant<\|im_sep\|>', ''),
            (r'<\|im_start\|>user<\|im_sep\|>', ''),
            (r'<\|im_start\|>system<\|im_sep\|>', ''),
        ]
        
        for pattern, replacement in patterns:
            response = self._safe_regex_sub(pattern, replacement, response)
            
        return response.strip()
    
    def _remove_reasoning_traces(self, response: str) -> str:
        """Remove reasoning traces from response."""
        if "</think>" in response:
            parts = response.split("</think>")
            if len(parts) > 1:
                response = parts[-1].lstrip('\n')
                
        return response
    
    def _normalize_whitespace(self, response: str) -> str:
        """Normalize whitespace efficiently."""
        import re
        response = re.sub(r'\n\s*\n', '\n\n', response)
        response = re.sub(r'[ \t]+', ' ', response)
        return response.strip()
    
    def _safe_regex_sub(self, pattern: str, replacement: str, text: str) -> str:
        """Safe regex substitution with error handling."""
        try:
            import re
            return re.sub(pattern, replacement, text, flags=re.DOTALL | re.MULTILINE)
        except Exception:
            return text
    
    def _safe_token_count(self, token_count: int) -> int:
        """Safe token counting with tensor-parallel validation."""
        if not isinstance(token_count, int) or token_count < 0:
            if self.tensor_parallel_size > 1:
                return self._estimate_tokens_for_tensor_parallel()
            return 0
            
        if self.tensor_parallel_size > 1 and token_count == 0:
            return self._estimate_tokens_for_tensor_parallel()
            
        return token_count
    
    def _estimate_tokens_for_tensor_parallel(self) -> int:
        """Estimate token count for tensor-parallel when API returns invalid count."""
        if hasattr(self, '_last_valid_token_count'):
            return self._last_valid_token_count
        return 1
    
    def _extract_response_metadata(self, api_response: any) -> dict:
        """Extract metadata from vLLM response for debugging."""
        metadata = {
            "finish_reason": getattr(api_response.choices[0], 'finish_reason', None),
            "vllm_version": getattr(api_response, 'model', 'unknown'),
        }
        
        if self.tensor_parallel_size > 1:
            metadata["tensor_parallel_size"] = self.tensor_parallel_size
            metadata["config_status"] = self.tp_config.status.value
            
        if hasattr(api_response, 'usage'):
            metadata["total_tokens"] = getattr(api_response.usage, 'total_tokens', None)
            
        return metadata
    
    def _handle_parsing_error(self, api_response: any, error: Exception) -> dict:
        """Handle parsing errors with tensor-parallel specific recovery."""
        error_msg = f"Response parsing failed: {str(error)}"
        
        if self.tensor_parallel_size > 1:
            error_msg += f" (TP={self.tensor_parallel_size}, Status={self.tp_config.status.value})"
            
        try:
            fallback_response = api_response.choices[0].text if hasattr(api_response, 'choices') else ""
        except Exception:
            fallback_response = f"Error during parsing: {str(error)}"
            
        return {
            "model_responses": fallback_response,
            "input_token": 0,
            "output_token": 0,
            "error": error_msg,
            "tensor_parallel_size": self.tensor_parallel_size,
            "response_metadata": {"error": True, "error_type": type(error).__name__},
        }

    def _init_performance_monitoring(self) -> None:
        self._performance_history = []
        self._monitoring_enabled = self.tensor_parallel_size > 1
        self._last_gpu_stats = None
        self._request_start_time = None

    def _start_request_timing(self) -> None:
        self._request_start_time = time.perf_counter()

    def _get_gpu_utilization(self) -> Dict[str, float]:
        try:
            import pynvml
            pynvml.nvmlInit()
            device_count = pynvml.nvmlDeviceGetCount()
            
            total_util = 0
            total_memory_used = 0
            total_memory_total = 0
            
            for i in range(min(device_count, self.tensor_parallel_size)):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                memory = pynvml.nvmlDeviceGetMemoryInfo(handle)
                
                total_util += util.gpu
                total_memory_used += memory.used
                total_memory_total += memory.total
            
            return {
                "avg_utilization": total_util / self.tensor_parallel_size,
                "total_memory_used_gb": total_memory_used / (1024**3),
                "total_memory_total_gb": total_memory_total / (1024**3),
                "memory_efficiency": total_memory_used / total_memory_total * 100
            }
        except ImportError:
            return {
                "avg_utilization": 0.0,
                "total_memory_used_gb": 0.0,
                "total_memory_total_gb": 0.0,
                "memory_efficiency": 0.0
            }
        except Exception:
            return {
                "avg_utilization": 0.0,
                "total_memory_used_gb": 0.0,
                "total_memory_total_gb": 0.0,
                "memory_efficiency": 0.0
            }

    def _calculate_tensor_parallel_efficiency(self, gpu_stats: Dict[str, float]) -> float:
        if self.tensor_parallel_size == 1:
            return 100.0
        
        baseline_util = gpu_stats["avg_utilization"]
        expected_util = 85.0
        
        if baseline_util == 0:
            return 0.0
        
        efficiency = min(100.0, (baseline_util / expected_util) * 100.0)
        return efficiency

    def _estimate_kv_cache_utilization(self, total_memory_used_gb: float) -> float:
        phi4_model_size_gb = 14.0
        kv_cache_memory = max(0, total_memory_used_gb - phi4_model_size_gb)
        max_kv_cache = self._calculate_max_kv_cache_size()
        
        if max_kv_cache == 0:
            return 0.0
        
        return min(100.0, (kv_cache_memory / max_kv_cache) * 100.0)

    def _calculate_max_kv_cache_size(self) -> float:
        hidden_size = 3072
        num_layers = 32
        sequence_length = self.max_model_len
        precision_bytes = 2
        
        size_per_token = 2 * num_layers * hidden_size * precision_bytes
        max_tokens = sequence_length * self.max_num_seqs
        total_size_bytes = max_tokens * size_per_token
        
        return total_size_bytes / (1024**3)

    def _collect_performance_metrics(self, request_latency_ms: float) -> PerformanceMetrics:
        gpu_stats = self._get_gpu_utilization()
        tp_efficiency = self._calculate_tensor_parallel_efficiency(gpu_stats)
        kv_utilization = self._estimate_kv_cache_utilization(gpu_stats["total_memory_used_gb"])
        
        metrics = PerformanceMetrics(
            request_latency_ms=request_latency_ms,
            gpu_utilization_avg=gpu_stats["avg_utilization"],
            gpu_memory_used_gb=gpu_stats["total_memory_used_gb"],
            gpu_memory_total_gb=gpu_stats["total_memory_total_gb"],
            tensor_parallel_efficiency=tp_efficiency,
            kv_cache_utilization=kv_utilization,
            timestamp=time.time()
        )
        
        if len(self._performance_history) >= 100:
            self._performance_history.pop(0)
        self._performance_history.append(metrics)
        
        return metrics

    def _get_performance_summary(self) -> Dict[str, float]:
        if not self._performance_history:
            return {}
        
        recent_metrics = self._performance_history[-10:]
        
        return {
            "avg_latency_ms": sum(m.request_latency_ms for m in recent_metrics) / len(recent_metrics),
            "avg_gpu_utilization": sum(m.gpu_utilization_avg for m in recent_metrics) / len(recent_metrics),
            "avg_memory_used_gb": sum(m.gpu_memory_used_gb for m in recent_metrics) / len(recent_metrics),
            "avg_tp_efficiency": sum(m.tensor_parallel_efficiency for m in recent_metrics) / len(recent_metrics),
            "avg_kv_utilization": sum(m.kv_cache_utilization for m in recent_metrics) / len(recent_metrics),
        }

    @override
    def _query_prompting(self, inference_data: dict):
        self._start_request_timing()
        api_response, query_latency = super()._query_prompting(inference_data)
        return api_response, query_latency 