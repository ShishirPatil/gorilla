import json
from bfcl.model_handler.model_style import ModelStyle
from bfcl.model_handler.oss_model.salesforce import SalesforceHandler
from bfcl.model_handler.oss_model.constant import VLLM_PORT
from openai import OpenAI

TASK_INSTRUCTION = """You are a tool calling assistant. In order to complete the user's request, you need to select one or more appropriate tools from the following tools and fill in the correct values for the tool parameters. Your specific tasks are:
1. Make one or more function/tool calls to meet the request based on the question.
2. If none of the function can be used, point it out and refuse to answer.
3. If the given question lacks the parameters required by the function, also point it out.
"""

FORMAT_INSTRUCTION = """
The output MUST strictly adhere to the following JSON format, and NO other text MUST be included.
The example format is as follows. Please make sure the parameter type is correct. If no function call is needed, please directly output an empty list '[]'
```
[
    {"name": "func_name1", "arguments": {"argument1": "value1", "argument2": "value2"}},
    ... (more tool calls as required)
]
```
"""


class HammerHandler(SalesforceHandler):
    def __init__(self, model_name, temperature) -> None:
        super().__init__(model_name, temperature)
        self.client = OpenAI(base_url=f"http://localhost:{VLLM_PORT}/v1", api_key="EMPTY")
    @staticmethod
    def _format_prompt(messages, function):
        """
        "chat_template": "{% set system_message = 'You are a helpful assistant.' %}{% if messages[0]['role'] == 'system' %}{% set system_message = messages[0]['content'] %}{% endif %}{% if system_message is defined %}{{ '<|im_start|>system\n' + system_message + '<|im_end|>\n' }}{% endif %}{% for message in messages %}{% set content = message['content'] %}{% if message['role'] == 'user' %}{{ '<|im_start|>user\n' + content + '<|im_end|>\n<|im_start|>assistant\n' }}{% elif message['role'] == 'assistant' %}{{ content + '<|im_end|>' + '\n' }}{% endif %}{% endfor %}",
        """

        def convert_to_format_tool(tools):

            if isinstance(tools, dict):
                format_tools = {
                    "name": tools["name"],
                    "description": tools["description"],
                    "parameters": tools["parameters"].get("properties", {}),
                }

                for param in format_tools["parameters"].keys():
                    if "properties" in format_tools["parameters"][param] and isinstance(format_tools["parameters"][param]["properties"], dict):
                        required = format_tools["parameters"][param].get("required", [])
                        format_tools["parameters"][param] = format_tools["parameters"][param]["properties"]
                        for p in required:
                            format_tools["parameters"][param][p]["required"] = True

                required = tools["parameters"].get("required", [])
                for param in required:
                    format_tools["parameters"][param]["required"] = True
                for param in format_tools["parameters"].keys():
                    if "default" in format_tools["parameters"][param]:
                        default = format_tools["parameters"][param]["default"]
                        format_tools["parameters"][param][
                            "description"
                        ] += f"default is '{default}'"
                return format_tools
            elif isinstance(tools, list):
                return [convert_to_format_tool(tool) for tool in tools]
            else:
                return tools

        tools = convert_to_format_tool(function)

        user_query = ""
        
        N = len(messages)
        if N == 2:            
            for message in messages:
                if message["role"] == "user":
                    user_query += f"{message['content']}"

        else: 
            for message in messages:
                if message['role'] == 'assistant':
                    if message['content'] != []:
                         user_query += f"{message['role']}: ```\n{json.dumps(message['content'])}\n```\n"
                elif message['role'] != 'system':
                    user_query += f"{message['role']}: {message['content']}\n"
            if messages[-1]['role'] != 'user':
                user_query += "user:  \n"


        content = f"[BEGIN OF TASK INSTRUCTION]\n{TASK_INSTRUCTION}\n[END OF TASK INSTRUCTION]\n\n"
        content += (
            "[BEGIN OF AVAILABLE TOOLS]\n"
            + json.dumps(tools)
            + "\n[END OF AVAILABLE TOOLS]\n\n"
        )
        content += f"[BEGIN OF FORMAT INSTRUCTION]\n{FORMAT_INSTRUCTION}\n[END OF FORMAT INSTRUCTION]\n\n"
        content += f"[BEGIN OF QUERY]\n{user_query}\n[END OF QUERY]\n\n"
        
        return content


    
    def _parse_query_response_prompting(self, api_response: any) -> dict:
        if api_response["choices"][0]["message"]["tool_calls"] != []:
            return {
                "model_responses": api_response["choices"][0]["message"]["tool_calls"],
                "input_token": 0,
                "output_token": 0,
            }
        else:
            return {
                "model_responses": api_response["choices"][0]["message"]["content"],
                "input_token": 0,
                "output_token": 0,
            }

    def _query_prompting(self, inference_data: dict):
        function: list[dict] = inference_data["function"]
        message: list[dict] = inference_data["message"]

        formatted_prompt = self._format_prompt(message, function)
        inference_data["inference_input_log"] = {"formatted_prompt": formatted_prompt}
        message_new = [{"role":"user","content":formatted_prompt}]
        outputs = self.client.chat.completions.create(
                model=self.model_name,
                temperature=self.temperature,
                messages=message_new,
                max_tokens=4096,  
            )
        agent_action = outputs.choices[0].message.content
        action = agent_action.replace("```", "")
        try:
            action = json.loads(action)
            
        except:
            action = []

        return {
            'choices': [{
                'message': {
                    'role': 'assistant',
                    'content': action,
                    'tool_calls': action
                }
            }]
        }