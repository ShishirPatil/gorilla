from bfcl.model_handler.oss_model.base_oss_handler import OSSHandler
from bfcl.model_handler.utils import func_doc_language_specific_pre_processing


class DeepseekCoderHandler(OSSHandler):
    """
    This is the handler for the Deepseek-Coder models. Models are benchmarked in their Function Calling mode.
    """
    def __init__(self, model_name, temperature) -> None:
        super().__init__(model_name, temperature)

    def _format_prompt(self, messages, function):
        """
        "bos_token": {
            "__type": "AddedToken",
            "content": "<｜begin▁of▁sentence｜>",
            "lstrip": false,
            "normalized": true,
            "rstrip": false,
            "single_word": false
        },
        "chat_template": "{% if not add_generation_prompt is defined %}{% set add_generation_prompt = false %}{% endif %}{% set ns = namespace(is_first=false, is_tool=false, is_output_first=true, system_prompt='') %}{%- for message in messages %}    {%- if message['role'] == 'system' %}        {% set ns.system_prompt = message['content'] %}    {%- endif %}{%- endfor %}{{bos_token}}{{ns.system_prompt}}{%- for message in messages %}    {%- if message['role'] == 'user' %}    {%- set ns.is_tool = false -%}{{'<｜User｜>' + message['content']}}    {%- endif %}    {%- if message['role'] == 'assistant' and message['content'] is none %}        {%- set ns.is_tool = false -%}        {%- for tool in message['tool_calls']%}            {%- if not ns.is_first %}{{'<｜Assistant｜><｜tool▁calls▁begin｜><｜tool▁call▁begin｜>' + tool['type'] + '<｜tool▁sep｜>' + tool['function']['name'] + '\\n' + '```json' + '\\n' + tool['function']['arguments'] + '\\n' + '```' + '<｜tool▁call▁end｜>'}}            {%- set ns.is_first = true -%}            {%- else %}{{'\\n' + '<｜tool▁call▁begin｜>' + tool['type'] + '<｜tool▁sep｜>' + tool['function']['name'] + '\\n' + '```json' + '\\n' + tool['function']['arguments'] + '\\n' + '```' + '<｜tool▁call▁end｜>'}}{{'<｜tool▁calls▁end｜><｜end▁of▁sentence｜>'}}                   {%- endif %}        {%- endfor %}    {%- endif %}    {%- if message['role'] == 'assistant' and message['content'] is not none %}        {%- if ns.is_tool %}{{'<｜tool▁outputs▁end｜>' + message['content'] + '<｜end▁of▁sentence｜>'}}        {%- set ns.is_tool = false -%}        {%- else %}{{'<｜Assistant｜>' + message['content'] + '<｜end▁of▁sentence｜>'}}        {%- endif %}    {%- endif %}    {%- if message['role'] == 'tool' %}        {%- set ns.is_tool = true -%}        {%- if ns.is_output_first %}{{'<｜tool▁outputs▁begin｜><｜tool▁output▁begin｜>' + message['content'] + '<｜tool▁output▁end｜>'}}        {%- set ns.is_output_first = false %}        {%- else %}{{'\\n<｜tool▁output▁begin｜>' + message['content'] + '<｜tool▁output▁end｜>'}}        {%- endif %}    {%- endif %}{%- endfor -%}{% if ns.is_tool %}{{'<｜tool▁outputs▁end｜>'}}{% endif %}{% if add_generation_prompt and not ns.is_tool %}{{'<｜Assistant｜>'}}{% endif %}"
        "chat_template": "{% if not add_generation_prompt is defined %}{% set add_generation_prompt = false %}{% endif %}{% set ns = namespace(is_first=false, is_tool=false, is_output_first=true, system_prompt='') %}{%- for message in messages %}    {%- if message['role'] == 'system' %}        {% set ns.system_prompt = message['content'] %}    {%- endif %}{%- endfor %}{{bos_token}}{{ns.system_prompt}}{%- for message in messages %}    {%- if message['role'] == 'user' %}    {%- set ns.is_tool = false -%}{{'<｜User｜>' + message['content']}}    {%- endif %}    {%- if message['role'] == 'assistant' and message['content'] is none %}        {%- set ns.is_tool = false -%}        {%- for tool in message['tool_calls']%}            {%- if not ns.is_first %}{{'<｜Assistant｜><｜tool▁calls▁begin｜><｜tool▁call▁begin｜>' + tool['type'] + '<｜tool▁sep｜>' + tool['function']['name'] + '\\n' + '```json' + '\\n' + tool['function']['arguments'] + '\\n' + '```' + '<｜tool▁call▁end｜>'}}            {%- set ns.is_first = true -%}            {%- else %}{{'\\n' + '<｜tool▁call▁begin｜>' + tool['type'] + '<｜tool▁sep｜>' + tool['function']['name'] + '\\n' + '```json' + '\\n' + tool['function']['arguments'] + '\\n' + '```' + '<｜tool▁call▁end｜>'}}{{'<｜tool▁calls▁end｜><｜end▁of▁sentence｜>'}}                   {%- endif %}        {%- endfor %}    {%- endif %}    {%- if message['role'] == 'assistant' and message['content'] is not none %}        {%- if ns.is_tool %}{{'<｜tool▁outputs▁end｜>' + message['content'] + '<｜end▁of▁sentence｜>'}}        {%- set ns.is_tool = false -%}        {%- else %}{{'<｜Assistant｜>' + message['content'] + '<｜end▁of▁sentence｜>'}}        {%- endif %}    {%- endif %}    {%- if message['role'] == 'tool' %}        {%- set ns.is_tool = true -%}        {%- if ns.is_output_first %}{{'<｜tool▁outputs▁begin｜><｜tool▁output▁begin｜>' + message['content'] + '<｜tool▁output▁end｜>'}}        {%- set ns.is_output_first = false %}        {%- else %}{{'\\n<｜tool▁output▁begin｜>' + message['content'] + '<｜tool▁output▁end｜>'}}        {%- endif %}    {%- endif %}{%- endfor -%}{% if ns.is_tool %}{{'<｜tool▁outputs▁end｜>'}}{% endif %}{% if add_generation_prompt and not ns.is_tool %}{{'<｜Assistant｜>'}}{% endif %}"
        """
        formatted_prompt = "<｜begin▁of▁sentence｜>"

        is_first_tool_call = True
        is_output_first = True
        is_tool = False

        # Extract the system prompt
        for message in messages:
            if message["role"] == "system":
                formatted_prompt += message["content"]
                break

        for message in messages:
            if message["role"] == "user":
                is_tool = False
                formatted_prompt += f"<｜User｜>{message['content']}"

            elif message["role"] == "assistant" and message["content"] is None:
                is_tool = False
                formatted_prompt += "<｜Assistant｜><｜tool▁calls▁begin｜>"
                for tool_call in message["tool_calls"]:
                    tool_call_template = (
                        "<｜tool▁call▁begin｜>{type}<｜tool▁sep｜>{name}\\n"
                        "```json\\n{arguments}\\n```<｜tool▁call▁end｜>"
                    )
                    tool_call_formatted = tool_call_template.format(
                        type=tool_call["type"],
                        name=tool_call["function"]["name"],
                        arguments=tool_call["function"]["arguments"],
                    )
                    if not is_first_tool_call:
                        formatted_prompt += f"\\n{tool_call_formatted}"
                    else:
                        formatted_prompt += tool_call_formatted
                        is_first_tool_call = False
                formatted_prompt += "<｜tool▁calls▁end｜><｜end▁of▁sentence｜>"

            elif message["role"] == "assistant" and message["content"] is not None:
                if is_tool:
                    formatted_prompt += (
                        f"<｜tool▁outputs▁end｜>{message['content']}<｜end▁of▁sentence｜>"
                    )
                    is_tool = False
                else:
                    formatted_prompt += (
                        f"<｜Assistant｜>{message['content']}<｜end▁of▁sentence｜>"
                    )

            elif message["role"] == "tool":
                is_tool = True
                tool_output_template = (
                    "<｜tool▁output▁begin｜>{content}<｜tool▁output▁end｜>"
                )
                if is_output_first:
                    formatted_prompt += f"<｜tool▁outputs▁begin｜>{tool_output_template.format(content=message['content'])}"
                    is_output_first = False
                else:
                    formatted_prompt += (
                        f"\\n{tool_output_template.format(content=message['content'])}"
                    )

        if is_tool:
            formatted_prompt += "<｜tool▁outputs▁end｜>"

        if not is_tool:
            formatted_prompt += "<｜Assistant｜>"

        return formatted_prompt

    def _pre_query_processing_prompting(self, test_entry: dict) -> dict:
        functions: list = test_entry["function"]
        test_category: str = test_entry["id"].rsplit("_", 1)[0]

        functions = func_doc_language_specific_pre_processing(functions, test_category)

        # Deepseek coder is in FC mode, so no need to add the default system prompt

        return {"message": [], "function": functions}
