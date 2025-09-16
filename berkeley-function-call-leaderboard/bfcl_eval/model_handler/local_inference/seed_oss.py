import json
from typing import Any

from bfcl_eval.model_handler.local_inference.base_oss_handler import OSSHandler
from overrides import override


class SeedOSSHandler(OSSHandler):
    """
    This is the local inference handler for the Seed-OSS models such as Seed-OSS-36B-Instruct.
    The Seed-OSS models support reasoning capabilities with thinking tokens.
    """

    def __init__(self, model_name, temperature) -> None:
        super().__init__(model_name, temperature)
        self.is_fc_model = False

    @override
    def _format_prompt(self, messages, function):
        """
        Format prompt for Seed-OSS models based on the actual chat_template.jinja.
        
        Format: <seed:bos>role\ncontent<seed:eos>
        - BOS/EOS tokens: <seed:bos> and <seed:eos>
        - Thinking tokens: <seed:think> and </seed:think>
        - Generation prompt: <seed:bos>assistant\n
        """
        formatted_prompt = ""

        # Process system message and add function calling instructions if functions are present
        if messages and messages[0]["role"] == "system":
            formatted_prompt += f"<seed:bos>system\n{messages[0]['content']}"
            message_start_idx = 1
        else:
            formatted_prompt += "<seed:bos>system\nYou are a helpful assistant."
            message_start_idx = 0

        # Add function calling instructions if functions are provided
        if function and len(function) > 0:
            formatted_prompt += "\n\n# Tools\n\nYou may call one or more functions to assist with the user query.\n\n"
            formatted_prompt += "You are provided with function signatures within <tools></tools> XML tags:\n<tools>\n"
            for func in function:
                formatted_prompt += f"{json.dumps(func, indent=2)}\n"
            formatted_prompt += "</tools>\n\n"
            
            formatted_prompt += "For each function call, return the function call in the exact format:\n"
            formatted_prompt += "[function_name(parameter1=value1, parameter2=value2)]\n\n"
            formatted_prompt += "IMPORTANT:\n"
            formatted_prompt += "- Use the EXACT function name from the tools above\n"
            formatted_prompt += "- Do not use variables or placeholders like 'func_name1'\n"
            formatted_prompt += "- Use the actual parameter names as specified\n"
            formatted_prompt += "- Format: [actual_function_name(param1=value1, param2=value2)]\n"
        
        formatted_prompt += "<seed:eos>"

        # Process conversation messages
        for idx in range(message_start_idx, len(messages)):
            message = messages[idx]
            role = message["role"]
            content = message["content"]

            if role in ["user", "system"]:
                formatted_prompt += f"<seed:bos>{role}\n{content}<seed:eos>"
            
            elif role == "assistant":
                formatted_prompt += f"<seed:bos>{role}"
                
                # Handle reasoning content if present
                reasoning_content = ""
                if "reasoning_content" in message and message["reasoning_content"]:
                    reasoning_content = message["reasoning_content"].strip()
                elif "<seed:think>" in content and "</seed:think>" in content:
                    # Extract thinking content if embedded in the content
                    parts = content.split("</seed:think>")
                    if len(parts) > 1:
                        reasoning_part = parts[0]
                        if "<seed:think>" in reasoning_part:
                            reasoning_content = reasoning_part.split("<seed:think>")[-1].strip()
                        content = parts[-1].strip()

                # Add thinking content if present
                if reasoning_content:
                    formatted_prompt += f"\n<seed:think>{reasoning_content}</seed:think>"
                
                # Add main content if present
                if content and content.strip():
                    formatted_prompt += f"\n{content.strip()}<seed:eos>"
                elif reasoning_content:
                    # If we only have reasoning content, still need to close with eos
                    formatted_prompt += "<seed:eos>"
            
            elif role == "tool":
                # Handle tool responses - based on the template, tools are treated as regular role messages
                formatted_prompt += f"<seed:bos>{role}\n{content}<seed:eos>"

        # Add generation prompt
        formatted_prompt += "<seed:bos>assistant\n"
        
        return formatted_prompt

    @override
    def _parse_query_response_prompting(self, api_response: Any) -> dict:
        """
        Parse the response from Seed-OSS models, extracting thinking content if present.
        """
        model_response = api_response.choices[0].text
        
        reasoning_content = ""
        cleaned_response = model_response
        
        # Extract thinking content if present
        if "</seed:think>" in model_response:
            parts = model_response.split("</seed:think>")
            if len(parts) > 1:
                reasoning_part = parts[0]
                if "<seed:think>" in reasoning_part:
                    reasoning_content = reasoning_part.split("<seed:think>")[-1].strip()
                cleaned_response = parts[-1].strip()
        
        return {
            "model_responses": cleaned_response,
            "reasoning_content": reasoning_content,
            "input_token": api_response.usage.prompt_tokens,
            "output_token": api_response.usage.completion_tokens,
        }

    @override
    def _add_assistant_message_prompting(
        self, inference_data: dict, model_response_data: dict
    ) -> dict:
        """
        Add assistant message with reasoning content support.
        """
        inference_data["message"].append(
            {
                "role": "assistant",
                "content": model_response_data["model_responses"],
                "reasoning_content": model_response_data.get("reasoning_content", ""),
            }
        )
        return inference_data
