import json
import re

from bfcl_eval.model_handler.local_inference.base_oss_handler import OSSHandler
from bfcl_eval.model_handler.utils import (
    convert_to_function_call,
    func_doc_language_specific_pre_processing,
)
from overrides import override


class PelicanVLMFCHandler(OSSHandler):
    def __init__(self, model_name, temperature) -> None:
        super().__init__(model_name, temperature)
        self.is_fc_model = True
        self.model_name_huggingface = model_name.replace("-FC", "")

    @override
    def decode_ast(self, result, language="Python"):
        # Model response is of the form:
        # "<tool_call>\n{\"name\": \"spotify.play\", \"arguments\": {\"artist\": \"Taylor Swift\", \"duration\": 20}}\n</tool_call>\n<tool_call>\n{\"name\": \"spotify.play\", \"arguments\": {\"artist\": \"Maroon 5\", \"duration\": 15}}\n</tool_call>"?
        tool_calls = self._extract_tool_calls(result)
        if type(tool_calls) != list or any(type(item) != dict for item in tool_calls):
            return []
        return [
            {call["name"]: {k: v for k, v in call["arguments"].items()}}
            for call in tool_calls
        ]

    @override
    def decode_execute(self, result):
        tool_calls = self._extract_tool_calls(result)
        if type(tool_calls) != list or any(type(item) != dict for item in tool_calls):
            return []
        decoded_result = []
        for item in tool_calls:
            if type(item) == str:
                item = eval(item)
            decoded_result.append({item["name"]: item["arguments"]})
        return convert_to_function_call(decoded_result)

    @override
    def _format_prompt(self,
        messages, 
        function
        ):
        """
        "chat_template":
        {% set image_count = namespace(value=0) %}
        {% set video_count = namespace(value=0) %}
        {% for message in messages %}
            {% if loop.first and message['role'] != 'system' %}
                <|im_start|>
                system\nYou are a helpful assistant.
                <|im_end|>\n
            {% endif %}
            <|im_start|>
            {{ message['role'] }}\n
            {% if message['content'] is string %}
                {{ message['content'] }}
            <|im_end|>\n
            {% else %}
                {% for content in message['content'] %}
                    {% if content['type'] == 'image' or 'image' in content or 'image_url' in content %}
                        {% set image_count.value = image_count.value + 1 %}
                        {% if add_vision_id %}
                            Picture {{ image_count.value }}: 
                        {% endif %}
                        <|vision_start|><|image_pad|><|vision_end|>
                    {% elif content['type'] == 'video' or 'video' in content %}
                        {% set video_count.value = video_count.value + 1 %}
                        {% if add_vision_id %}
                            Video {{ video_count.value }}:
                        {% endif %}
                        <|vision_start|><|video_pad|><|vision_end|>
                    {% elif 'text' in content %}
                        {{ content['text'] }}
                    {% endif %}
                {% endfor %}
                </im_end>\n
            {% endif %}
        {% endfor %}
        {% if add_generation_prompt %}
            <|im_start|>assistant\n
        {% endif %}"
        """
        add_vision_id=False
        add_generation_prompt=True
        formatted_prompt = ""
        image_count = 0
        video_count = 0
        first_system_processed = False
        
        # ===== 1. 函数调用处理 =====
        if function and len(function) > 0:
            formatted_prompt += "<|im_start|>system\n"
            
            # 检查第一条消息是否为系统消息
            if messages and messages[0]['role'] == 'system':
                formatted_prompt += messages[0]['content'] + "\n\n"
                first_system_processed = True
            
            # 添加函数调用说明
            formatted_prompt += "# Tools\n\nYou may call one or more function to assist with the user query."
            formatted_prompt += "\n\nYou are provided with function signatures within <tools></tools> XML tags:"
            formatted_prompt += "\n<tools>"
            
            for func in function:
                formatted_prompt += f"\n{json.dumps(func)}"
            
            formatted_prompt += "\n</tools>"
            formatted_prompt += "\n\nFor each function call, return a json object with functions name and arguments within <tool_call></tool_call> XML tags:"
            formatted_prompt += '\n<tool_call>\n{"name": <function-name>, "arguments": <args-json-object>}\n</tool_call>'
            formatted_prompt += "<|im_end|>\n"
        
        # ===== 2. 系统消息处理 =====
        # 处理未在函数部分处理的系统消息
        if messages and messages[0]['role'] == 'system' and not first_system_processed:
            formatted_prompt += f"<|im_start|>system\n{messages[0]['content']}<|im_end|>\n"
            first_system_processed = True
        elif not function and (not messages or messages[0]['role'] != 'system'):
            # 添加默认系统消息
            formatted_prompt += "<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n"
        
        # ===== 3. 消息遍历处理 =====
        for idx, message in enumerate(messages):
            role = message['role']
            content = message['content']
            
            # 跳过已处理的系统消息
            if idx == 0 and role == 'system' and first_system_processed:
                continue
                
            # 添加消息开始标签
            formatted_prompt += f"<|im_start|>{role}\n"
            
            # 处理工具响应消息
            if role == "tool":
                formatted_prompt += f"<tool_response>\n{content}\n</tool_response>"
            
            # 处理助理消息（可能包含函数调用）
            elif role == "assistant":
                # 处理函数调用
                if "tool_calls" in message:
                    for call in message["tool_calls"]:
                        func = call.get("function", call)
                        name = func["name"]
                        args = func["arguments"]
                        
                        if isinstance(args, dict):
                            args = json.dumps(args, ensure_ascii=False)
                        
                        formatted_prompt += f'<tool_call>\n{{"name": "{name}", "arguments": {args}}}\n</tool_call>'
                
                # 处理常规内容
                if content:
                    formatted_prompt += content
            
            # 处理用户消息（可能包含多模态内容）
            elif role == "user":
                if isinstance(content, str):
                    formatted_prompt += content
                elif isinstance(content, list):
                    for content_part in content:
                        # 处理图像内容
                        if ('type' in content_part and content_part['type'] == 'image') or \
                        'image' in content_part or \
                        'image_url' in content_part:
                            image_count += 1
                            if add_vision_id:
                                formatted_prompt += f"Picture {image_count}: "
                            formatted_prompt += "<|vision_start|><|image_pad|><|vision_end|>"
                        
                        # 处理视频内容
                        elif ('type' in content_part and content_part['type'] == 'video') or \
                            'video' in content_part:
                            video_count += 1
                            if add_vision_id:
                                formatted_prompt += f"Video {video_count}: "
                            formatted_prompt += "<|vision_start|><|video_pad|><|vision_end|>"
                        
                        # 处理文本内容
                        elif 'text' in content_part:
                            formatted_prompt += content_part['text']
            
            # 添加消息结束标签
            formatted_prompt += "<|im_end|>\n"
        
        # ===== 4. 添加助理提示 =====
        if add_generation_prompt:
            formatted_prompt += "<|im_start|>assistant\n"
        
        # print("=================================start of formatted prompt=================================")
        # print(formatted_prompt)

        return formatted_prompt

    @override
    def _pre_query_processing_prompting(self, test_entry: dict) -> dict:
        functions: list = test_entry["function"]
        test_category: str = test_entry["id"].rsplit("_", 1)[0]

        functions = func_doc_language_specific_pre_processing(functions, test_category)
        # FC models use its own system prompt, so no need to add any message

        return {"message": [], "function": functions}

    @override
    def _parse_query_response_prompting(self, api_response: any) -> dict:
        """ Qwen2.5-VL """
        # 获取原始响应
        raw_response = api_response.choices[0].text
        image_references = []
        
        # 提取图像引用
        if "<image>" in raw_response:
            # 获取所有图像引用
            image_matches = re.findall(r'<image>([^<]+)</image>', raw_response)
            image_references = [{"id": img.split(":", 1)[0], "url": img.split(":", 1)[1]} 
                            for img in image_matches if ":" in img]
            
            # 从响应中移除图像标签
            cleaned_response = re.sub(r'<image>.*?</image>', '', raw_response).strip()
        else:
            cleaned_response = raw_response
        
        # 解析工具调用
        tool_calls = self._extract_tool_calls(cleaned_response)
        
        return {
            "model_responses": cleaned_response,
            "image_references": image_references,
            "model_responses_message_for_chat_history": {
                "role": "assistant",
                "content": "" if tool_calls else cleaned_response,
                "tool_calls": tool_calls
            },
            "input_token": getattr(api_response.usage, "prompt_tokens", -1),
            "output_token": getattr(api_response.usage, "completion_tokens", -1),
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
        pattern = r"<tool_call>\n(.*?)\n</tool_call>"
        matches = re.findall(pattern, input_string, re.DOTALL)

        # Process matches into a list of dictionaries
        result = []
        for match in matches:
            try:
                match = json.loads(match)
            except Exception as e:
                pass
            result.append(match)
        return result

