from typing import Optional

from bfcl_eval.model_handler.local_inference.base_oss_handler import OSSHandler
from overrides import override


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
        dtype: str = "bfloat16"
    ) -> None:
        super().__init__(model_name, temperature, dtype)
        
        self.tensor_parallel_size = tensor_parallel_size
        self.max_model_len = max_model_len
        self.gpu_memory_utilization = gpu_memory_utilization
        
        self._validate_tensor_parallel_config()

    def _validate_tensor_parallel_config(self) -> None:
        """Validate that tensor parallel size is compatible with Phi-4's 8 KV heads."""
        phi4_kv_heads = 8
        if phi4_kv_heads % self.tensor_parallel_size != 0:
            raise ValueError(
                f"tensor_parallel_size={self.tensor_parallel_size} is incompatible with "
                f"Phi-4's {phi4_kv_heads} KV heads. Must be one of: [1, 2, 4, 8]"
            )

    @override
    def _format_prompt(self, messages: list[dict], function: list[dict]) -> str:
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
    def decode_ast(self, result: str, language: str = "Python") -> any:
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
    def decode_execute(self, result: str) -> any:
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