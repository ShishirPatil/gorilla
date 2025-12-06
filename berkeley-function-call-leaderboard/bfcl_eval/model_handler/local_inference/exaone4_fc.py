import json
import re
from typing import Any

from bfcl_eval.model_handler.local_inference.base_oss_handler import OSSHandler
from bfcl_eval.model_handler.utils import convert_to_function_call
from overrides import override


class Exaone4FCHandler(OSSHandler):
    def __init__(
        self,
        model_name,
        temperature,
        registry_name,
        is_fc_model,
        dtype="bfloat16",
        **kwargs,
    ) -> None:
        super().__init__(model_name, temperature, registry_name, is_fc_model, **kwargs)
        self.model_name_huggingface = model_name
    
    @override
    def decode_ast(self, result, language, has_tool_call_tag):
        tool_calls = self._extract_tool_calls(result)
        if type(tool_calls) != list or any(type(item) != dict for item in tool_calls):
            raise ValueError(f"Model did not return a list of function calls: {result}")
        return [
            {call["name"]: {k: v for k, v in call["arguments"].items()}}
            for call in tool_calls
        ]
    
    @override
    def decode_execute(self, result, has_tool_call_tag):
        tool_calls = self._extract_tool_calls(result)
        if type(tool_calls) != list or any(type(item) != dict for item in tool_calls):
            raise ValueError(f"Model did not return a list of function calls: {result}")
        decoded_result = []
        for item in tool_calls:
            if type(item) == str:
                item = eval(item)
            decoded_result.append({item["name"]: item["arguments"]})
        return convert_to_function_call(decoded_result)
    
    @override
    def _format_prompt(self, messages, function):
        """
        "chat_template":
        {%- if not skip_think is defined %}
            {%- set skip_think = true %}
        {%- endif %}
        {%- set role_indicators = {
            'user': '[|user|]\n',
            'assistant': '[|assistant|]\n',
            'system': '[|system|]\n',
            'tool': '[|tool|]\n'
        } %}
        {%- set end_of_turn = '[|endofturn|]\n' %}
        {%- macro available_tools(tools) %}
            {{- "# Available Tools" }}
            {{- "\nYou can use none, one, or multiple of the following tools by calling them as functions to help with the user’s query." }}
            {{- "\nHere are the tools available to you in JSON format within <tool> and </tool> tags:\n" }}
            {%- for tool in tools %}
                {{- "<tool>" }}
                {{- tool | tojson(ensure_ascii=False) | safe }}
                {{- "</tool>\n" }}
            {%- endfor %}
            {{- "\nFor each function call you want to make, return a JSON object with function name and arguments within <tool_call> and </tool_call> tags, like:" }}
            {{- "\n<tool_call>{\"name\": function_1_name, \"arguments\": {argument_1_name: argument_1_value, argument_2_name: argument_2_value}}</tool_call>" }}
            {{- "\n<tool_call>{\"name\": function_2_name, \"arguments\": {...}}</tool_call>\n..." }}
            {{- "\nNote that if no argument name is specified for a tool, you can just print the argument value directly, without the argument name or JSON formatting." }}
        {%- endmacro %}
        {%- set ns = namespace(last_query_index = messages|length - 1) %}
        {%- for message in messages %}
            {%- if message.role == "user" and message.content is string %}
                {%- set ns.last_query_index = loop.index0 -%}
            {%- endif %}
        {%- endfor %}
        {%- for i in range(messages | length) %}
            {%- set msg = messages[i] %}
            {%- set role = msg.role %}
            {%- if role not in role_indicators %}
                {{- raise_exception('Unknown role: ' ~ role) }}
            {%- endif %}
            
            {%- if i == 0 %}
                {%- if role == 'system' %}
                    {{- role_indicators['system'] }}
                    {{- msg.content }}
                    {%- if tools is defined and tools %}
                        {{- "\n\n" }}{{- available_tools(tools) }}
                    {%- endif %}
                    {{- end_of_turn -}}
                    {%- continue %}
                {%- elif tools is defined and tools %}            
                    {{- role_indicators['system'] }}
                    {{- available_tools(tools) }}
                    {{- end_of_turn -}}            
                {%- endif %}
            {%- endif %}
            {%- if role == 'assistant' %}
                {{- role_indicators['assistant'] }}
                {%- if msg.content %}        
                    {%- if "</think>" in msg.content %}
                        {%- set content = msg.content.split('</think>')[-1].strip() %}
                        {%- set reasoning_content = msg.content.split('</think>')[0].strip() %}
                        {%- if reasoning_content.startswith("<think>") %}
                            {%- set reasoning_content = reasoning_content[9:].strip() %}
                        {%- endif %}
                    {%- else %}
                        {%- set content = msg.content %}
                    {%- endif %}
                    {%- if msg.reasoning_content %}
                        {%- set reasoning_content = msg.reasoning_content %}
                    {%- endif %}
                    {%- if (not skip_think and loop.last) and reasoning_content is defined %}
                        {{- "<think>\n" }}
                        {{- reasoning_content}}
                        {{- "\n</think>\n\n" }}
                    {%- else %}
                        {{- "<think>\n\n</think>\n\n" }}
                    {%- endif %}
                    {{- content }}
                {%- endif %}
                {%- if msg.tool_calls %}
                    {%- if msg.content %}
                        {{- "\n" }}
                    {%- else %}
                        {{- "<think>\n\n</think>\n\n" }}
                    {%- endif %}
                    {%- for tool_call in msg.tool_calls %}
                        {%- if tool_call.function is defined %}
                            {%- set tool_call = tool_call.function %}
                        {%- endif %}
                        {%- if tool_call.arguments is defined %}
                            {%- set arguments = tool_call.arguments %}
                        {%- elif tool_call.parameters is defined %}
                            {%- set arguments = tool_call.parameters %}
                        {%- else %}
                            {{- raise_exception('arguments or parameters are mandatory: ' ~ tool_call) }}
                        {%- endif %}
                        {{- "<tool_call>" }}{"name": "{{- tool_call.name }}", "arguments": {{ arguments | tojson(ensure_ascii=False) | safe }}}{{- "</tool_call>" }}
                        {%- if not loop.last %}
                            {{- "\n" }}
                        {%- endif %}
                    {%- endfor %}
                {%- endif %}
                {{- end_of_turn -}}
            {%- elif role == "tool" %}
                {%- if i == 0 or messages[i - 1].role != "tool" %}
                    {{- role_indicators['tool'] }}
                {%- endif %}
                {%- if msg.content is defined %}            
                    {{- "<tool_result>" }}{"result": {{ msg.content | tojson(ensure_ascii=False) | safe }}}{{- "</tool_result>" }}            
                {%- endif %}
                {%- if loop.last or messages[i + 1].role != "tool" %}
                    {{- end_of_turn -}}
                {%- else %}
                    {{- "\n" }}
                {%- endif %}
            {%- else %}
                {{- role_indicators[role] }}
                {{- msg.content }}
                {{- end_of_turn -}}
            {%- endif %}
        {% endfor %}
        {%- if add_generation_prompt %}
            {{- role_indicators['assistant'] }}
            {%- if enable_thinking is defined and enable_thinking is true %}
                {{- "<think>\n" }}
            {%- else %}
                {{- "<think>\n\n</think>\n\n" }}
            {%- endif %}
        {%- endif %}
        """
        formatted_prompt = ""
        
        # Handle system message and tools
        if len(function) > 0:
            formatted_prompt += "[|system|]\n"
            
            # Add system message content if present
            if messages and messages[0]["role"] == "system":
                formatted_prompt += messages[0]["content"] + "\n\n"
            
            # Add tools definition
            formatted_prompt += "# Available Tools\n"
            formatted_prompt += "You can use none, one, or multiple of the following tools by calling them as functions to help with the user's query.\n"
            formatted_prompt += "Here are the tools available to you in JSON format within <tool> and </tool> tags:\n"
            
            for tool in function:
                formatted_prompt += f"<tool>{json.dumps(tool)}</tool>\n"
            
            formatted_prompt += "\nFor each function call you want to make, return a JSON object with function name and arguments within <tool_call> and </tool_call> tags, like:\n"
            formatted_prompt += '<tool_call>{"name": function_name, "arguments": {argument_name: argument_value}}</tool_call>\n'
            formatted_prompt += "[|endofturn|]\n"
        else:
            # No tools, just system message if present
            if messages and messages[0]["role"] == "system":
                formatted_prompt += f"[|system|]\n{messages[0]['content']}[|endofturn|]\n"
        
        # Track last user query index for reasoning mode handling
        last_query_index = len(messages) - 1
        for offset, message in enumerate(reversed(messages)):
            idx = len(messages) - 1 - offset
            if (
                message["role"] == "user"
                and type(message["content"]) == str
                and not (
                    message["content"].startswith("<tool_response>")
                    and message["content"].endswith("</tool_response>")
                )
            ):
                last_query_index = idx
                break
        
        # Process messages
        for idx, message in enumerate(messages):
            role = message["role"]
            content = message.get("content", "")
            
            # Skip first system message (already handled above with tools)
            if role == "system" and idx == 0:
                continue
            
            if role == "user":
                formatted_prompt += f"[|user|]\n{content}[|endofturn|]\n"
            
            elif role == "assistant":
                # Handle reasoning content if present
                reasoning_content = ""
                if "reasoning_content" in message and message["reasoning_content"]:
                    reasoning_content = message["reasoning_content"]
                elif "</think>" in content:
                    parts = content.split("</think>")
                    reasoning_content = parts[0].rstrip("\n").split("<think>")[-1].lstrip("\n")
                    content = parts[-1].lstrip("\n")
                
                formatted_prompt += f"[|assistant|]\n"
                
                # Add reasoning block if present
                if reasoning_content:
                    formatted_prompt += f"<think>\n{reasoning_content.strip()}\n</think>\n\n"
                
                formatted_prompt += content
                
                # Add tool calls if present
                if "tool_calls" in message and message["tool_calls"]:
                    for tool_call in message["tool_calls"]:
                        tc = tool_call
                        if "function" in tool_call:
                            tc = tool_call["function"]
                        
                        if content:
                            formatted_prompt += "\n"
                        
                        formatted_prompt += "<tool_call>\n"
                        formatted_prompt += json.dumps({
                            "name": tc["name"],
                            "arguments": tc["arguments"] if isinstance(tc["arguments"], dict) else json.loads(tc["arguments"])
                        })
                        formatted_prompt += "\n</tool_call>"
                
                formatted_prompt += "[|endofturn|]\n"
            
            elif role == "tool":
                # Tool responses are formatted as user messages with <tool_response> tags
                prev_role = messages[idx - 1]["role"] if idx > 0 else None
                next_role = messages[idx + 1]["role"] if idx < len(messages) - 1 else None
                
                if idx == 0 or prev_role != "tool":
                    formatted_prompt += "[|user|]\n"
                
                formatted_prompt += f"<tool_response>\n{content}\n</tool_response>"
                
                if idx == len(messages) - 1 or next_role != "tool":
                    formatted_prompt += "[|endofturn|]\n"
        
        # Add generation prompt
        formatted_prompt += "[|assistant|]\n"
        
        return formatted_prompt
    
    @override
    def _pre_query_processing_prompting(self, test_entry: dict) -> dict:
        functions: list = test_entry["function"]
        return {"message": [], "function": functions}
    
    @override
    def _parse_query_response_prompting(self, api_response: Any) -> dict:
        model_response = api_response.choices[0].text
        extracted_tool_calls = self._extract_tool_calls(model_response)
        
        # Extract reasoning content if present
        reasoning_content = ""
        cleaned_response = model_response
        if "</think>" in model_response:
            parts = model_response.split("</think>")
            reasoning_content = parts[0].rstrip("\n").split("<think>")[-1].lstrip("\n")
            cleaned_response = parts[-1].lstrip("\n")
        
        # Build message for chat history
        if len(extracted_tool_calls) > 0:
            model_responses_message_for_chat_history = {
                "role": "assistant",
                "content": "",
                "tool_calls": extracted_tool_calls,
            }
        else:
            model_responses_message_for_chat_history = {
                "role": "assistant",
                "content": cleaned_response,
            }
        
        model_responses_message_for_chat_history["reasoning_content"] = reasoning_content
        
        return {
            "model_responses": cleaned_response,
            "reasoning_content": reasoning_content,
            "model_responses_message_for_chat_history": model_responses_message_for_chat_history,
            "input_token": api_response.usage.prompt_tokens,
            "output_token": api_response.usage.completion_tokens,
        }
    
    @override
    def _add_assistant_message_prompting(
        self, inference_data: dict, model_response_data: dict
    ) -> dict:
        inference_data["message"].append(
            model_response_data["model_responses_message_for_chat_history"],
        )
        return inference_data
    
    @staticmethod
    def _extract_tool_calls(input_string):
        # Match tool calls with optional whitespace/newlines
        pattern = r"<tool_call>\s*(.*?)\s*</tool_call>"
        matches = re.findall(pattern, input_string, re.DOTALL)
        
        result = []
        for match in matches:
            try:
                parsed = json.loads(match.strip())
                result.append(parsed)
            except json.JSONDecodeError:
                # Try to clean up the JSON
                try:
                    # Remove any trailing content after the JSON object
                    cleaned = match.strip()
                    # Find the matching closing brace
                    brace_count = 0
                    end_idx = 0
                    for i, char in enumerate(cleaned):
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                end_idx = i + 1
                                break
                    if end_idx > 0:
                        parsed = json.loads(cleaned[:end_idx])
                        result.append(parsed)
                except Exception:
                    pass
        
        return result