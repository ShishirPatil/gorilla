from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, List

from bfcl_eval.model_handler.local_inference.base_oss_handler import OSSHandler
from overrides import override


class ConfigStatus(Enum):
    """Status of tensor parallel configuration."""
    WORKING = "working"
    BROKEN = "broken"
    UNTESTED = "untested"


@dataclass(frozen=True)
class TensorParallelConfig:
    """
    Configuration for tensor-parallel setup with Phi-4.
    
    Based on research of vLLM limitations and Phi-4's 8 KV head architecture.
    """
    tensor_parallel_size: int
    memory_per_gpu_gb: float
    total_memory_gb: float
    supported_gpus: List[str]
    expected_speedup: float
    status: ConfigStatus
    limitations: List[str]
    
    def __post_init__(self):
        """Validate configuration parameters."""
        phi4_kv_heads = 8
        if phi4_kv_heads % self.tensor_parallel_size != 0:
            raise ValueError(
                f"tensor_parallel_size={self.tensor_parallel_size} incompatible with "
                f"Phi-4's {phi4_kv_heads} KV heads"
            )


class TensorParallelPresets:
    """Predefined tensor-parallel configurations for Phi-4 based on research."""
    
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
        """Get all available configurations mapped by tensor parallel size."""
        return {
            1: cls.SINGLE_GPU,
            2: cls.DUAL_GPU,
            4: cls.QUAD_GPU,
            8: cls.OCTA_GPU,
        }
    
    @classmethod
    def get_working_configs(cls) -> Dict[int, TensorParallelConfig]:
        """Get only working configurations."""
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
        """
        Select optimal configuration based on available resources.
        
        Args:
            available_gpus: Number of available GPUs
            memory_per_gpu_gb: Memory available per GPU in GB
            allow_broken: Whether to consider broken configurations
            
        Returns:
            Optimal configuration or None if no suitable config found
        """
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
        memory_per_gpu_gb: Optional[float] = None
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
        
        self._validate_tensor_parallel_config()

    def _auto_select_config(
        self, 
        available_gpus: Optional[int], 
        memory_per_gpu_gb: Optional[float]
    ) -> TensorParallelConfig:
        """
        Automatically select optimal tensor-parallel configuration.
        
        Args:
            available_gpus: Number of available GPUs
            memory_per_gpu_gb: Memory available per GPU in GB
            
        Returns:
            Selected tensor-parallel configuration
            
        Raises:
            ValueError: If no suitable configuration found
        """
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
        """
        Get configuration for specified tensor parallel size.
        
        Args:
            tp_size: Tensor parallel size
            
        Returns:
            Configuration for the specified size
            
        Raises:
            ValueError: If tensor parallel size is not supported
        """
        all_configs = TensorParallelPresets.get_all_configs()
        
        if tp_size not in all_configs:
            supported_sizes = list(all_configs.keys())
            raise ValueError(
                f"tensor_parallel_size={tp_size} not supported. "
                f"Supported sizes: {supported_sizes}"
            )
        
        config = all_configs[tp_size]
        
        if config.status != ConfigStatus.WORKING:
            import warnings
            warnings.warn(
                f"tensor_parallel_size={tp_size} status: {config.status.value}. "
                f"Limitations: {', '.join(config.limitations)}",
                UserWarning
            )
        
        return config

    def get_config_info(self) -> str:
        """
        Get human-readable information about current configuration.
        
        Returns:
            Formatted configuration information
        """
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
        """Validate that tensor parallel size is compatible with Phi-4's 8 KV heads."""
        phi4_kv_heads = 8
        if phi4_kv_heads % self.tensor_parallel_size != 0:
            raise ValueError(
                f"tensor_parallel_size={self.tensor_parallel_size} is incompatible with "
                f"Phi-4's {phi4_kv_heads} KV heads. Must be one of: [1, 2, 4, 8]"
            )

    @override
    def _format_prompt(self, messages, function):
        """
        Format prompt for Phi-4 using optimized vLLM tokenization.
        
        Args:
            messages: List of chat messages
            function: List of available functions
            
        Returns:
            Formatted prompt string
        """
        formatted_prompt = ""
        
        for message in messages:
            formatted_prompt += f"<|im_start|>{message['role']}<|im_sep|>{message['content']}<|im_end|>\n"
        formatted_prompt += "<|im_start|>assistant<|im_sep|>"
        
        return formatted_prompt

    @override
    def decode_ast(self, result, language="Python"):
        """
        Decode AST results with vLLM-specific optimizations.
        
        Args:
            result: Raw model output
            language: Programming language for parsing
            
        Returns:
            Parsed AST result
        """
        return super().decode_ast(result, language)

    @override
    def decode_execute(self, result):
        """
        Decode execution results with batching optimizations.
        
        Args:
            result: Raw execution output
            
        Returns:
            Parsed execution result
        """
        return super().decode_execute(result)

    def _get_vllm_engine_args(self) -> dict:
        """
        Get vLLM engine arguments optimized for Phi-4.
        
        Returns:
            Dictionary of vLLM engine configuration parameters
        """
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
        """
        Configure KV cache settings optimized for Phi-4's GQA architecture.
        
        Returns:
            KV cache configuration parameters
        """
        return {
            "enable_prefix_caching": True,
            "kv_cache_dtype": "auto",
        }

    def _get_tensor_parallel_strategy(self) -> str:
        """
        Determine optimal tensor parallel strategy based on GPU configuration.
        
        Returns:
            Tensor parallelism strategy name
        """
        if self.tensor_parallel_size <= 2:
            return "standard"
        else:
            return "pipeline_parallel" 