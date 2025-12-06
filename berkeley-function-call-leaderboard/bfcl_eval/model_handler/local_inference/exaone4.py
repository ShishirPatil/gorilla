from typing import Any

from bfcl_eval.model_handler.local_inference.base_oss_handler import OSSHandler
from overrides import override


class Exaone4Handler(OSSHandler):    
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

        # Handle system message
        if messages[0]["role"] == "system":
            formatted_prompt += f"[|system|]\n{messages[0]['content']}[|endofturn|]\n"

        # Find last user query index (for reasoning mode handling)
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
            content = message["content"]

            if role == "user" or (role == "system" and idx != 0):
                formatted_prompt += f"[|{role}|]\n{content}[|endofturn|]\n"

            elif role == "assistant":
                reasoning_content = ""
                if "reasoning_content" in message and message["reasoning_content"]:
                    reasoning_content = message["reasoning_content"]

                elif "</think>" in content:
                    parts = content.split("</think>")
                    reasoning_content = (
                        parts[0].rstrip("\n").split("<think>")[-1].lstrip("\n")
                    )
                    content = parts[-1].lstrip("\n")

                if idx > last_query_index:
                    if idx == len(messages) - 1 or reasoning_content:
                        formatted_prompt += (
                            f"[|{role}|]\n<think>\n"
                            + reasoning_content.strip("\n")
                            + f"\n</think>\n\n"
                            + content.lstrip("\n")
                        )
                    else:
                        formatted_prompt += f"[|{role}|]\n{content}"
                else:
                    formatted_prompt += f"[|{role}|]\n{content}"

                formatted_prompt += "[|endofturn|]\n"

            elif role == "tool":
                prev_role = messages[idx - 1]["role"] if idx > 0 else None
                next_role = messages[idx + 1]["role"] if idx < len(messages) - 1 else None

                if idx == 0 or prev_role != "tool":
                    formatted_prompt += "[|user|]"

                formatted_prompt += f"\n<tool_response>\n{content}\n</tool_response>"

                if idx == len(messages) - 1 or next_role != "tool":
                    formatted_prompt += "[|endofturn|]\n"

        # Add generation prompt
        formatted_prompt += "[|assistant|]\n"
        return formatted_prompt

    @override
    def _parse_query_response_prompting(self, api_response: Any) -> dict:
        model_response = api_response.choices[0].text

        reasoning_content = ""
        cleaned_response = model_response
        if "</think>" in model_response:
            parts = model_response.split("</think>")
            reasoning_content = parts[0].rstrip("\n").split("<think>")[-1].lstrip("\n")
            cleaned_response = parts[-1].lstrip("\n")

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
        inference_data["message"].append(
            {
                "role": "assistant",
                "content": model_response_data["model_responses"],
                "reasoning_content": model_response_data.get("reasoning_content", ""),
            }
        )
        return inference_data