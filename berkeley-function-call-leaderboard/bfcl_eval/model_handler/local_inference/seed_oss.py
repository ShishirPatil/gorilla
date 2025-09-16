import json
from typing import Any

from bfcl_eval.model_handler.local_inference.base_oss_handler import OSSHandler
from overrides import override


class SeedOSSHandler(OSSHandler):
    """
    Handler for Seed-OSS models such as Seed-OSS-36B-Instruct.
    These models support reasoning capabilities with thinking tokens.
    """

    def __init__(self, model_name, temperature) -> None:
        super().__init__(model_name, temperature)
        self.is_fc_model = False

    @override
    def _format_prompt(self, messages, function):
        """
        Format prompt for Seed-OSS models based on the actual chat_template.jinja.
        """
        """
        {# ------------- special token variables ------------- #}
        {%- set bos_token              = '<seed:bos>'               -%}
        {%- set eos_token              = '<seed:eos>'               -%}
        {%- set pad_token              = '<seed:pad>'               -%}
        {%- set toolcall_begin_token   = '<seed:tool_call>'         -%}
        {%- set toolcall_end_token     = '</seed:tool_call>'        -%}
        {%- set think_begin_token      = '<seed:think>'             -%}
        {%- set think_end_token        = '</seed:think>'            -%}
        {%- set budget_begin_token     = '<seed:cot_budget_reflect>'-%}
        {%- set budget_end_token       = '</seed:cot_budget_reflect>'-%}
        {# -------------- reflection-interval lookup -------------- #}
        {%- if not thinking_budget is defined %}
        {%- set thinking_budget = -1 -%}
        {%- endif -%}
        {%- set budget_reflections_v05 = {
            0:      0,
            512:    128,
            1024:   256,
            2048:   512,
            4096:   512,
            8192:   1024,
            16384:  1024
        } -%}
        {# Find the first gear that is greater than or equal to the thinking_budget. #}
        {%- set ns = namespace(interval = None) -%}
        {%- for k, v in budget_reflections_v05 | dictsort -%}
            {%- if ns.interval is none and thinking_budget <= k -%}
                {%- set ns.interval = v -%}
            {%- endif -%}
        {%- endfor -%}
        {# If it exceeds the maximum gear, use the value of the last gear #}
        {%- if ns.interval is none -%}
            {%- set ns.interval = budget_reflections_v05[16384] -%}
        {%- endif -%}
        {# ---------- Preprocess the system message ---------- #}
        {%- if messages[0]["role"] == "system" %}
        {%- set system_message = messages[0]["content"] %}
        {%- set loop_messages = messages[1:] %}
        {%- else %}
        {%- set loop_messages = messages %}
        {%- endif %}
        {# ---------- Ensure tools exist ---------- #}
        {%- if not tools is defined or tools is none %}
        {%- set tools = [] %}
        {%- endif %}
        {# tools2doc.jinja #}
        {%- macro py_type(t) -%}
            {%- if t == "string" -%}str
            {%- elif t in ("number", "integer") -%}int
            {%- elif t == "boolean" -%}bool
            {%- elif t == "array" -%}list
            {%- else -%}Any{%- endif -%}
        {%- endmacro -%}
        {# ---------- Output the system block ---------- #}
        {%- if system_message is defined %}
        {{ bos_token + "system\n" + system_message }}
        {%- else %}
        {%- if tools is iterable and tools | length > 0 %}
        {{ bos_token + "system\nYou are Doubao, a helpful AI assistant. You may call one or more functions to assist with the user query." }}
        {%- endif %}
        {%- endif %}
        {%- if use_json_tooldef is defined and use_json_tooldef %}
        {{"Tool List:\nYou are authorized to use the following tools (described in JSON Schema format). Before performing any task, you must decide how to call them based on the descriptions and parameters of these tools."}}
        {{ tools | tojson(ensure_ascii=False) }}
        {%- else %}
        {%- for item in tools if item.type == "function" %}
        Function:
        def {{ item.function.name }}(
        {%- for name, spec in item.function.parameters.properties.items() %}
                {{- name }}: {{ py_type(spec.type) }}{% if not loop.last %},{% endif %}
        {%- endfor %}):
            ""
            {{ item.function.description | trim }}
            {# ---------- Args ---------- #}
            {%- if item.function.parameters.properties %}
            Args:
            {%- for name, spec in item.function.parameters.properties.items() %}
            - {{ name }} ({{ py_type(spec.type) }})
            {%- if name in item.function.parameters.required %} [必填]{% else %} [选填]{% endif %}:
            {{- " " ~ (spec.description or "") }}
            {%- endfor %}
            {%- endif %}
            {# ---------- Returns ---------- #}
            {%- if item.function.returns is defined
                and item.function.returns.properties is defined
                and item.function.returns.properties %}
            Returns:
            {%- for name, spec in item.function.returns.properties.items() %}
            - {{ name }} ({{ py_type(spec.type) }}):
            {{- " " ~ (spec.description or "") }}
            {%- endfor %}
            {%- endif %}
            ""
        {%- endfor %}
        {%- endif %}
        {%- if tools is iterable and tools | length > 0 %}
        {{"工具调用请遵循如下格式:\n<seed:tool_call>\n<function=example_function_name>\n<parameter=example_parameter_1>value_1</parameter>\n<parameter=example_parameter_2>This is the value for the second parameter\nthat can span\nmultiple lines</parameter>\n</function>\n</seed:tool_call>\n"}}
        {%- endif %}
        {# End the system block line #}
        {%- if system_message is defined or tools is iterable and tools | length > 0 %}
        {{ eos_token }}
        {%- endif %}
        {# ---------- Thinking Budget ---------- #}
        {%- if thinking_budget is defined %}
        {%- if thinking_budget == 0 %}
        {{ bos_token+"system" }}
        {{ "You are an intelligent assistant that can answer questions in one step without the need for reasoning and thinking, that is, your thinking budget is 0. Next, please skip the thinking process and directly start answering the user's questions." }}
        {{ eos_token }}
        {%- elif not thinking_budget == -1 %}
        {{ bos_token+"system" }}
        {{ "You are an intelligent assistant with reflective ability. In the process of thinking and reasoning, you need to strictly follow the thinking budget, which is "}}{{thinking_budget}}{{". That is, you need to complete your thinking within "}}{{thinking_budget}}{{" tokens and start answering the user's questions. You will reflect on your thinking process every "}}{{ns.interval}}{{" tokens, stating how many tokens have been used and how many are left."}}
        {{ eos_token }}
        {%- endif %}
        {%- endif %}
        {# ---------- List the historical messages one by one ---------- #}
        {%- for message in loop_messages %}
        {%- if message.role == "assistant"
        and message.tool_calls is defined
        and message.tool_calls is iterable
        and message.tool_calls | length > 0 %}
        {{ bos_token + message.role }}
        {%- if message.reasoning_content is defined and message.reasoning_content is string and message.reasoning_content | trim | length > 0 %}
        {{ "\n" + think_begin_token + message.reasoning_content | trim + think_end_token }}
        {%- endif %}
        {%- if message.content is defined and message.content is string and message.content | trim | length > 0 %}
        {{ "\n" + message.content | trim + "\n" }}
        {%- endif %}
        {%- for tool_call in message.tool_calls %}
        {%- if tool_call.function is defined %}{% set tool_call = tool_call.function %}{% endif %}
        {{ "\n" + toolcall_begin_token + "\n<function=" + tool_call.name + ">\n" }}
        {%- if tool_call.arguments is defined %}
        {%- for arg_name, arg_value in tool_call.arguments | items %}
        {{ "<parameter=" + arg_name + ">" }}
        {%- set arg_value = arg_value if arg_value is string else arg_value | string %}
        {{ arg_value+"</parameter>\n" }}
        {%- endfor %}
        {%- endif %}
        {{ "</function>\n" + toolcall_end_token }}
        {%- endfor %}
        {{ eos_token }}
        {%- elif message.role in ["user", "system"] %}
        {{ bos_token + message.role + "\n" + message.content + eos_token }}
        {%- elif message.role == "assistant" %}
        {{ bos_token + message.role }}
        {%- if message.reasoning_content is defined and message.reasoning_content is string and message.reasoning_content | trim | length > 0 %}
        {{ "\n" + think_begin_token + message.reasoning_content | trim + think_end_token }}
        {%- endif %}
        {%- if message.content is defined and message.content is string and message.content | trim | length > 0 %}
        {{ "\n" + message.content | trim + eos_token }}
        {%- endif %}
        {# Include the tool role #}
        {%- else %}
        {{ bos_token + message.role + "\n" + message.content + eos_token }}
        {%- endif %}
        {%- endfor %}
        {# ---------- Control the model to start continuation ---------- #}
        {%- if add_generation_prompt %}
        {{ bos_token+"assistant\n" }}
        {%- if thinking_budget == 0 %}
        {{ think_begin_token + "\n" + budget_begin_token + "The current thinking budget is 0, so I will directly start answering the question." + budget_end_token + "\n" + think_end_token }}
        {%- endif %}
        {%- endif %}
        """
        formatted_prompt = ""

        if messages and messages[0]["role"] == "system":
            formatted_prompt += f"<seed:bos>system\n{messages[0]['content']}"
            message_start_idx = 1
        else:
            formatted_prompt += "<seed:bos>system\nYou are a helpful assistant."
            message_start_idx = 0

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

        for idx in range(message_start_idx, len(messages)):
            message = messages[idx]
            role = message["role"]
            content = message["content"]

            if role in ["user", "system"]:
                formatted_prompt += f"<seed:bos>{role}\n{content}<seed:eos>"
            
            elif role == "assistant":
                formatted_prompt += f"<seed:bos>{role}"
                
                reasoning_content = ""
                if "reasoning_content" in message and message["reasoning_content"]:
                    reasoning_content = message["reasoning_content"].strip()
                elif "<seed:think>" in content and "</seed:think>" in content:
                    parts = content.split("</seed:think>")
                    if len(parts) > 1:
                        reasoning_part = parts[0]
                        if "<seed:think>" in reasoning_part:
                            reasoning_content = reasoning_part.split("<seed:think>")[-1].strip()
                        content = parts[-1].strip()

                if reasoning_content:
                    formatted_prompt += f"\n<seed:think>{reasoning_content}</seed:think>"
                
                if content and content.strip():
                    formatted_prompt += f"\n{content.strip()}<seed:eos>"
                elif reasoning_content:
                    formatted_prompt += "<seed:eos>"
            
            elif role == "tool":
                formatted_prompt += f"<seed:bos>{role}\n{content}<seed:eos>"

        formatted_prompt += "<seed:bos>assistant\n"
        
        return formatted_prompt

    @override
    def _parse_query_response_prompting(self, api_response: Any) -> dict:
        """Parse response from Seed-OSS models, extracting thinking content if present."""
        model_response = api_response.choices[0].text
        
        reasoning_content = ""
        cleaned_response = model_response
        
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
        """Add assistant message with reasoning content support."""
        inference_data["message"].append(
            {
                "role": "assistant",
                "content": model_response_data["model_responses"],
                "reasoning_content": model_response_data.get("reasoning_content", ""),
            }
        )
        return inference_data
