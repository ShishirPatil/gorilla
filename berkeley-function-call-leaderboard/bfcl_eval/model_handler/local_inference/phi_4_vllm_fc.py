import json
import re
import time
from typing import List, Dict, Any, Optional, Tuple
from overrides import override

from bfcl_eval.model_handler.local_inference.phi_4_vllm import Phi4VllmHandler
from bfcl_eval.model_handler.utils import (
    convert_to_function_call,
    func_doc_language_specific_pre_processing,
)


class Phi4VllmFCHandler(Phi4VllmHandler):

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
        enforce_eager: bool = False,
        enable_vllm_tool_calling: bool = True,
        tool_call_parser: str = "hermes"
    ) -> None:
        super().__init__(
            model_name=model_name,
            temperature=temperature,
            tensor_parallel_size=tensor_parallel_size,
            max_model_len=max_model_len,
            gpu_memory_utilization=gpu_memory_utilization,
            dtype=dtype,
            auto_config=auto_config,
            available_gpus=available_gpus,
            memory_per_gpu_gb=memory_per_gpu_gb,
            enable_phi4_optimizations=enable_phi4_optimizations,
            kv_cache_dtype=kv_cache_dtype,
            enable_prefix_caching=enable_prefix_caching,
            max_num_seqs=max_num_seqs,
            enforce_eager=enforce_eager
        )
        self.model_name_huggingface = model_name.replace("-FC", "")
        self.is_fc_model = True
        self.enable_vllm_tool_calling = enable_vllm_tool_calling
        self.tool_call_parser = tool_call_parser
        self._init_tool_calling_optimizations()

    def _init_tool_calling_optimizations(self) -> None:
        if hasattr(self, '_tool_call_cache'):
            return
        self._tool_call_cache = {}
        self._tool_extraction_patterns = self._compile_tool_patterns()
        self._parallel_tool_threshold = 3

    def _compile_tool_patterns(self) -> Dict[str, Any]:
        patterns = {
            'standard': re.compile(r"<\|tool_call\|>(.*?)<\|/tool_call\|>", re.DOTALL),
            'incomplete': re.compile(r"<\|tool_call\|>(.*?)(?:<\|/tool_call\|>)?$", re.DOTALL),
            'json_block': re.compile(r"```json\s*(.*?)\s*```", re.DOTALL | re.IGNORECASE),
            'python_block': re.compile(r"```python\s*(.*?)\s*```", re.DOTALL | re.IGNORECASE)
        }
        return patterns

    @override
    def _format_prompt(self, messages, function):
        if self.enable_vllm_tool_calling and function:
            return self._format_vllm_tool_prompt(messages, function)
        else:
            return self._format_phi_tool_prompt(messages, function)

    def _format_vllm_tool_prompt(self, messages, function) -> str:
        cache_key = self._create_tool_prompt_cache_key(messages, function)
        if cache_key in self._tool_call_cache:
            return self._tool_call_cache[cache_key]

        prompt_parts = []
        system_content = self._build_vllm_system_content(messages, function)
        
        if system_content:
            prompt_parts.append(self._format_message("system", system_content))

        for message in messages:
            if message["role"] == "system":
                continue
            prompt_parts.append(self._format_message(message["role"], message["content"]))

        prompt_parts.append(self.assistant_start)
        formatted_prompt = "".join(prompt_parts)

        if self._validate_prompt_length(formatted_prompt):
            self._tool_call_cache[cache_key] = formatted_prompt
            return formatted_prompt
        else:
            return self._truncate_tool_prompt(messages, function)

    def _format_phi_tool_prompt(self, messages, function) -> str:
        system_messages = [msg for msg in messages if msg["role"] == "system"]
        assert 0 <= len(system_messages) <= 1

        system_message = "You are a helpful assistant with some tools."
        if messages[0]["role"] == "system":
            system_message = messages[0]["content"]
            messages = messages[1:]

        tool_contents = self._format_tool_contents(function)
        formatted_prompt = f"<|system|>{system_message}<|tool|>{tool_contents}<|/tool|><|end|>"
        
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            formatted_prompt += f"<|{role}|>{content}<|end|>"

        formatted_prompt += "<|assistant|>"
        return formatted_prompt

    def _format_tool_contents(self, function) -> str:
        if not function:
            return ""
        
        tool_parts = []
        for func in function:
            tool_parts.append(json.dumps(func, separators=(',', ':')))
        
        return "\n".join(tool_parts)

    def _build_vllm_system_content(self, messages, function) -> str:
        system_parts = []
        
        for message in messages:
            if message["role"] == "system":
                system_parts.append(message["content"])

        if function:
            tools_text = self._format_tools_for_vllm(function)
            system_parts.append(tools_text)

        return "\n\n".join(system_parts) if system_parts else ""

    def _format_tools_for_vllm(self, function) -> str:
        if not function:
            return ""
        
        tool_descriptions = []
        for func in function:
            if isinstance(func, dict) and "name" in func:
                tool_desc = f"Tool: {func['name']}"
                if "description" in func:
                    tool_desc += f"\nDescription: {func['description']}"
                if "parameters" in func:
                    tool_desc += f"\nParameters: {json.dumps(func['parameters'], separators=(',', ':'))}"
                tool_descriptions.append(tool_desc)

        if tool_descriptions:
            return "Available tools:\n\n" + "\n\n".join(tool_descriptions)
        return ""

    def _create_tool_prompt_cache_key(self, messages, function) -> str:
        import hashlib
        message_str = str([(m["role"], m["content"][:50]) for m in messages])
        function_str = str([f.get("name", "") for f in function]) if function else ""
        combined = f"{message_str}:{function_str}:{self.is_phi4_mini}:fc"
        return hashlib.md5(combined.encode()).hexdigest()[:16]

    def _truncate_tool_prompt(self, messages, function) -> str:
        system_content = self._build_vllm_system_content(messages, function)
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

    @override
    def decode_ast(self, result, language="Python"):
        if type(result) != list or any(type(item) != dict for item in result):
            return []
        return result

    @override
    def decode_execute(self, result):
        if type(result) != list or any(type(item) != dict for item in result):
            return []
        return convert_to_function_call(result)

    @override
    def _pre_query_processing_prompting(self, test_entry: dict) -> dict:
        functions: list = test_entry["function"]
        test_category: str = test_entry["id"].rsplit("_", 1)[0]

        functions = func_doc_language_specific_pre_processing(functions, test_category)
        return {"message": [], "function": functions}

    @override
    def _parse_query_response_prompting(self, api_response: any) -> dict:
        self._start_request_timing()
        
        try:
            request_latency_ms = self._calculate_request_latency()
            raw_response = api_response.choices[0].text
            cleaned_response = self._clean_phi4_response(raw_response)
            
            extracted_tool_calls = self._extract_tool_calls_optimized(cleaned_response)
            
            if self._is_tool_call_response_format(extracted_tool_calls) and len(extracted_tool_calls) > 0:
                model_responses = [
                    {item["name"]: item["arguments"]} for item in extracted_tool_calls
                ]
                model_responses_message = cleaned_response
            else:
                model_responses = cleaned_response
                model_responses_message = cleaned_response

            response_metadata = self._extract_response_metadata(api_response)
            
            if self._monitoring_enabled:
                performance_metrics = self._collect_performance_metrics(request_latency_ms)
                response_metadata.update({
                    "performance_metrics": {
                        "request_latency_ms": performance_metrics.request_latency_ms,
                        "tool_calls_extracted": len(extracted_tool_calls) if extracted_tool_calls else 0,
                        "tensor_parallel_efficiency": performance_metrics.tensor_parallel_efficiency,
                    }
                })

            return {
                "model_responses": model_responses,
                "model_responses_message_for_chat_history": model_responses_message,
                "input_token": self._safe_token_count(api_response.usage.prompt_tokens),
                "output_token": self._safe_token_count(api_response.usage.completion_tokens),
                "tensor_parallel_size": self.tensor_parallel_size,
                "response_metadata": response_metadata,
            }
            
        except Exception as e:
            return self._handle_parsing_error(api_response, e)

    def _extract_tool_calls_optimized(self, input_string: str) -> List[Dict[str, Any]]:
        if not input_string or not input_string.strip():
            return []

        cache_key = hash(input_string[:200])
        if hasattr(self, '_tool_extraction_cache') and cache_key in self._tool_extraction_cache:
            return self._tool_extraction_cache[cache_key]

        result = []
        
        for pattern_name, pattern in self._tool_extraction_patterns.items():
            matches = pattern.findall(input_string)
            if matches:
                result.extend(self._process_tool_matches(matches))
                break

        if not hasattr(self, '_tool_extraction_cache'):
            self._tool_extraction_cache = {}
        if len(self._tool_extraction_cache) > 1000:
            self._tool_extraction_cache.clear()
        
        self._tool_extraction_cache[cache_key] = result
        return result

    def _process_tool_matches(self, matches: List[str]) -> List[Dict[str, Any]]:
        result = []
        
        for match in matches:
            if not match.strip():
                continue
                
            processed_match = self._normalize_tool_match(match)
            
            try:
                parsed_match = json.loads(processed_match)
            except json.JSONDecodeError:
                continue

            if isinstance(parsed_match, list):
                for item in parsed_match:
                    if isinstance(item, str):
                        try:
                            item = json.loads(item)
                        except:
                            continue
                    if isinstance(item, dict):
                        result.append(item)
            elif isinstance(parsed_match, dict):
                result.append(parsed_match)

        return result

    def _normalize_tool_match(self, match: str) -> str:
        match = match.strip()
        
        if not match.startswith("[") and not match.endswith("]"):
            if "," in match and '"name"' in match:
                match = "[" + match + "]"
        
        return match

    def _is_tool_call_response_format(self, input_data: Any) -> bool:
        if not isinstance(input_data, list):
            return False

        for item in input_data:
            if not isinstance(item, dict):
                return False
            if "name" not in item:
                return False
            if "arguments" not in item:
                return False
            if len(item) != 2:
                return False

        return True

    @override
    def _add_assistant_message_prompting(
        self, inference_data: dict, model_response_data: dict
    ) -> dict:
        inference_data["message"].append(
            {
                "role": "assistant",
                "content": model_response_data["model_responses_message_for_chat_history"],
            }
        )
        return inference_data

    @override
    def get_vllm_server_args(self, backend: str = "vllm") -> List[str]:
        args = super().get_vllm_server_args(backend)
        
        if self.enable_vllm_tool_calling and backend == "vllm":
            args.extend([
                "--enable-auto-tool-choice",
                "--tool-call-parser", self.tool_call_parser
            ])
        
        return args

    @override
    def _parse_query_response_FC(self, api_response: any) -> dict:
        try:
            self._start_request_timing()
            request_latency_ms = self._calculate_request_latency()
            
            raw_response = api_response.choices[0].text
            cleaned_response = self._clean_phi4_response(raw_response)
            
            model_responses, tool_call_ids = self._extract_fc_tool_calls_vllm_optimized(cleaned_response)
            
            if self._monitoring_enabled:
                performance_metrics = self._collect_performance_metrics(request_latency_ms)
                fc_metadata = {
                    "performance_metrics": {
                        "request_latency_ms": performance_metrics.request_latency_ms,
                        "tool_calls_extracted": len(tool_call_ids) if tool_call_ids else 0,
                        "tensor_parallel_efficiency": performance_metrics.tensor_parallel_efficiency,
                        "tool_extraction_efficiency": self._calculate_tool_calling_efficiency(),
                    },
                    "tensor_parallel_size": self.tensor_parallel_size,
                    "tool_parser": self.tool_call_parser,
                }
            else:
                fc_metadata = {"tensor_parallel_size": self.tensor_parallel_size}
            
            response_metadata = self._extract_response_metadata(api_response)
            response_metadata.update(fc_metadata)
            
            message_for_history = self._build_fc_message_for_history(cleaned_response, model_responses, tool_call_ids)
            
            return {
                "model_responses": model_responses,
                "model_responses_message_for_chat_history": message_for_history,
                "tool_call_ids": tool_call_ids,
                "input_token": self._safe_token_count(api_response.usage.prompt_tokens),
                "output_token": self._safe_token_count(api_response.usage.completion_tokens),
                "response_metadata": response_metadata,
            }
            
        except Exception as e:
            return self._handle_fc_parsing_error(api_response, e)

    def _extract_fc_tool_calls_vllm_optimized(self, response_text: str) -> tuple[any, list[str]]:
        if not response_text or not response_text.strip():
            return response_text, []

        cache_key = hash(response_text[:300])
        if hasattr(self, '_fc_extraction_cache') and cache_key in self._fc_extraction_cache:
            return self._fc_extraction_cache[cache_key]

        extracted_calls = []
        tool_call_ids = []
        
        if self.enable_vllm_tool_calling:
            vllm_calls = self._extract_vllm_native_tool_calls(response_text)
            if vllm_calls:
                extracted_calls = vllm_calls
                tool_call_ids = [f"call_{i}" for i in range(len(extracted_calls))]
        
        if not extracted_calls:
            phi_calls = self._extract_tool_calls_optimized(response_text)
            if phi_calls and self._is_tool_call_response_format(phi_calls):
                extracted_calls = [{item["name"]: item["arguments"]} for item in phi_calls]
                tool_call_ids = [f"phi_call_{i}" for i in range(len(extracted_calls))]
            else:
                extracted_calls = response_text
                tool_call_ids = []

        if not hasattr(self, '_fc_extraction_cache'):
            self._fc_extraction_cache = {}
        if len(self._fc_extraction_cache) > 500:
            self._fc_extraction_cache.clear()
        
        result = (extracted_calls, tool_call_ids)
        self._fc_extraction_cache[cache_key] = result
        return result

    def _extract_vllm_native_tool_calls(self, response_text: str) -> list[dict]:
        try:
            if self.tool_call_parser == "hermes":
                return self._extract_hermes_tool_calls(response_text)
            elif self.tool_call_parser == "llama4_pythonic":
                return self._extract_pythonic_tool_calls(response_text)
            else:
                return self._extract_generic_vllm_tool_calls(response_text)
        except Exception:
            return []

    def _extract_hermes_tool_calls(self, response_text: str) -> list[dict]:
        import re
        tool_call_pattern = re.compile(r'<tool_call>\s*(.*?)\s*</tool_call>', re.DOTALL)
        matches = tool_call_pattern.findall(response_text)
        
        results = []
        for match in matches:
            try:
                if match.strip().startswith('[') and match.strip().endswith(']'):
                    tool_list = json.loads(match.strip())
                    for tool in tool_list:
                        if isinstance(tool, dict) and "name" in tool and "arguments" in tool:
                            results.append({tool["name"]: tool["arguments"]})
                else:
                    tool_data = json.loads(match.strip())
                    if isinstance(tool_data, dict) and "name" in tool_data and "arguments" in tool_data:
                        results.append({tool_data["name"]: tool_data["arguments"]})
            except (json.JSONDecodeError, KeyError):
                continue
        
        return results

    def _extract_pythonic_tool_calls(self, response_text: str) -> list[dict]:
        import re
        pythonic_pattern = re.compile(r'\[([^[\]]*(?:\([^)]*\)[^[\]]*)*)\]', re.DOTALL)
        matches = pythonic_pattern.findall(response_text)
        
        results = []
        for match in matches:
            try:
                if "(" in match and ")" in match:
                    func_calls = re.findall(r'(\w+)\s*\(([^)]*)\)', match)
                    for func_name, args_str in func_calls:
                        try:
                            args_dict = eval(f"dict({args_str})")
                            results.append({func_name: args_dict})
                        except:
                            results.append({func_name: {"raw_args": args_str}})
            except:
                continue
        
        return results

    def _extract_generic_vllm_tool_calls(self, response_text: str) -> list[dict]:
        json_pattern = re.compile(r'\{[^{}]*"name"[^{}]*"arguments"[^{}]*\}', re.DOTALL)
        matches = json_pattern.findall(response_text)
        
        results = []
        for match in matches:
            try:
                tool_data = json.loads(match)
                if isinstance(tool_data, dict) and "name" in tool_data and "arguments" in tool_data:
                    results.append({tool_data["name"]: tool_data["arguments"]})
            except json.JSONDecodeError:
                continue
        
        return results

    def _build_fc_message_for_history(self, raw_response: str, model_responses: any, tool_call_ids: list[str]) -> dict:
        if tool_call_ids and isinstance(model_responses, list):
            tool_calls = []
            for i, (response, call_id) in enumerate(zip(model_responses, tool_call_ids)):
                if isinstance(response, dict):
                    for func_name, func_args in response.items():
                        tool_calls.append({
                            "id": call_id,
                            "type": "function",
                            "function": {
                                "name": func_name,
                                "arguments": json.dumps(func_args) if isinstance(func_args, dict) else str(func_args)
                            }
                        })
            
            return {
                "role": "assistant",
                "content": None,
                "tool_calls": tool_calls
            }
        else:
            return {
                "role": "assistant", 
                "content": str(model_responses)
            }

    def _handle_fc_parsing_error(self, api_response: any, error: Exception) -> dict:
        print(f"⚠️ FC parsing error (TP={self.tensor_parallel_size}): {error}")
        
        try:
            raw_response = api_response.choices[0].text if hasattr(api_response, 'choices') else str(api_response)
            token_usage = getattr(api_response, 'usage', None)
            
            return {
                "model_responses": raw_response,
                "model_responses_message_for_chat_history": {"role": "assistant", "content": raw_response},
                "tool_call_ids": [],
                "input_token": self._safe_token_count(token_usage.prompt_tokens if token_usage else 0),
                "output_token": self._safe_token_count(token_usage.completion_tokens if token_usage else 0),
                "response_metadata": {
                    "error": str(error),
                    "tensor_parallel_size": self.tensor_parallel_size,
                    "error_type": "fc_parsing_error"
                }
            }
        except Exception as fallback_error:
            return {
                "model_responses": f"FC parsing failed: {error}",
                "model_responses_message_for_chat_history": {"role": "assistant", "content": f"Error: {error}"},
                "tool_call_ids": [],
                "input_token": 0,
                "output_token": 0,
                "response_metadata": {
                    "error": str(error),
                    "fallback_error": str(fallback_error),
                    "tensor_parallel_size": self.tensor_parallel_size,
                    "error_type": "fc_critical_error"
                }
            }

    def _calculate_tool_calling_efficiency(self) -> float:
        if not hasattr(self, '_tool_extraction_cache'):
            return 1.0
        
        cache_size = len(self._tool_extraction_cache)
        if cache_size == 0:
            return 1.0
        
        hit_rate = min(cache_size / 100.0, 1.0)
        parallel_boost = min(self.tensor_parallel_size / 4.0, 1.5)
        
        return hit_rate * parallel_boost 