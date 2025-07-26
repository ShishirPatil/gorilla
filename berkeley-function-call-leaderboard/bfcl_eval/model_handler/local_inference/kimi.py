from bfcl_eval.model_handler.local_inference.base_oss_handler import OSSHandler
from bfcl_eval.model_handler.utils import (
    combine_consecutive_user_prompts,
    func_doc_language_specific_pre_processing,
    system_prompt_pre_processing_chat_model,
)
from overrides import override
import json


class KimiHandler(OSSHandler):
    """Local inference for Kimi models."""
    def __init__(self, model_name: str, temperature: float) -> None:
        super().__init__(model_name, temperature)
        self.is_fc_model = False

        self.max_context_length = 128000 # 128k context length from HF
        # recommended temperature from HF
        if self.temperature is None or self.temperature == 0.001:
            self.temperature = 0.6

    @override
    def _format_prompt(self, messages: list[dict], function: dict) -> str:
        """
        Manually apply the chat template to construct the formatted prompt.
        This way, we can have full control over the final formatted prompt and is generally recommended for advanced use cases.
        """
        #try converting functions to tools, in openai format
        tools = None
        if function and len(function) > 0:
            tools = []
            for func in function:
                tools.append({
                    "type": "function", 
                    "function": func
                })

        try:
            formatted_prompt = self.tokenizer.apply_chat_template(
                messages, 
                tools=tools,
                tokenize=False, 
                add_generation_prompt=True
            )
        except Exception as e:
            #fall back to manual formatting
            formatted_prompt = self._fallback_format_prompt(messages, function)

        return formatted_prompt
    
    def _fallback_format_prompt(self, messages, function):
        """
        Fallback to manual formatting.
        """
        formatted_prompt = ""

        system_message = "You are Kimi, an AI assistant created by Moonshot AI."
        remaining_messages = messages
        if messages and messages[0].get("role") == "system":
            system_message = messages[0]["content"]
            remaining_messages = messages[1:] 
        

        if function and len(function) > 0:
            system_message += "\n\nYou have access to the following tools. Use them when appropriate:\n\n"
            for func in function:
                system_message += json.dumps(func, indent=2) + "\n\n"
            system_message += "When you need to call a tool, respond with a JSON object in this format:\n"
            system_message += '{"name": "function_name", "arguments": {"arg1": "value1", "arg2": "value2"}}\n'
        
        #add system msg
        formatted_prompt += f"<|im_start|>system\n{system_message}<|im_end|>\n"

        #add conversation msg
        # Add conversation messages
        for message in remaining_messages:
            role = message["role"]
            content = message["content"]
            formatted_prompt += f"<|im_start|>{role}\n{content}<|im_end|>\n"
        
        #add assisstant prompt
        formatted_prompt += "<|im_start|>assistant\n"
        return formatted_prompt

    @override
    def _add_execution_results_prompting(self, inference_data: dict, execution_results: list[str], model_response_data: dict) -> dict:
        """
        Add tool execution results to the conversation.
        Kimi K2 uses OpenAI-compatible format, so we use the "tool" role for execution results.
        """
        for execution_result in execution_results:
            # Kimi K2 uses the `tool` role for execution results (OpenAI-compatible)
            inference_data["message"].append(
                {
                    "role": "tool",
                    "content": execution_result,
                }
            )
        return inference_data