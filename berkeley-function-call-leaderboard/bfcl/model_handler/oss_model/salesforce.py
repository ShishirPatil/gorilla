import json

from bfcl.model_handler.model_style import ModelStyle
from bfcl.model_handler.oss_model.constant import VLLM_PORT
from bfcl.model_handler.oss_model.base_oss_handler import OSSHandler
from openai import OpenAI


class SalesforceHandler(OSSHandler):
    def __init__(self, model_name, temperature) -> None:
        super().__init__(model_name, temperature)
        self.model_style = ModelStyle.OSSMODEL

        config = xLAMConfig(base_url=f"http://localhost:{VLLM_PORT}/v1/", model=self.model_name)
        self.client = xLAMChatCompletion.from_config(config)

    def decode_ast(self, result, language="Python"):
        decoded_output = []
        for invoked_function in result:
            name = invoked_function["name"]
            params = invoked_function["arguments"]
            decoded_output.append({name: params})
        return decoded_output

    def decode_execute(self, result):
        if isinstance(result, list):
            tool_calls = result
        elif isinstance(result, dict):
            tool_calls = result.get("tool_calls", [])
        else:
            tool_calls = []
        function_call = self.xlam_json_to_python_tool_calls(tool_calls)
        return function_call

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

    @staticmethod
    def xlam_json_to_python_tool_calls(tool_calls):
        """
        Converts a list of function calls in xLAM JSON format to Python format.

        Parameters:
        tool_calls (list): A list of dictionaries, where each dictionary represents a function call in xLAM JSON format.

        Returns:
        python_format (list): A list of strings, where each string is a function call in Python format.
        """
        if not isinstance(tool_calls, list):
            tool_calls = [tool_calls]

        python_format = []
        for tool_call in tool_calls:
            if isinstance(tool_call, dict):
                name = tool_call.get("name", "")
                arguments = tool_call.get("arguments", {})
                args_str = ", ".join(
                    [f"{key}={repr(value)}" for key, value in arguments.items()]
                )
                python_format.append(f"{name}({args_str})")
            # else:
                # print(f"Invalid format: {tool_call}")

        return python_format

    def convert_to_dict(self, input_str):
        """
        Convert a JSON-formatted string into a dictionary of tool calls and their arguments.

        Parameters:
        - input_str (str): A JSON-formatted string containing 'tool_calls' with 'name' and 'arguments'.

        Returns:
        - list[dict]: A list of dictionaries with tool call names as keys and their arguments as values.
        """
        try:
            data = json.loads(input_str)
        except json.JSONDecodeError:
            return input_str

        tool_calls = data if isinstance(data, list) else data.get("tool_calls", [])

        result_list = [
            {tool_call.get("name", ""): tool_call.get("arguments", {})}
            for tool_call in tool_calls
            if isinstance(tool_call, dict)
        ]

        return result_list

    def _query_prompting(self, inference_data: dict):
        function: list[dict] = inference_data["function"]
        message: list[dict] = inference_data["message"]

        inference_data["inference_input_log"] = {
            "message": repr(message),
            "function": function,
        }

        api_response = self.client.completion(messages=message, tools=function)

        return api_response


# fmt: off
"""
The following code are from the Salesforce xLAM Client: 
https://github.com/SalesforceAIResearch/xLAM/blob/main/xLAM/client/xLAM.py
https://github.com/SalesforceAIResearch/xLAM/blob/main/xLAM/client/config.py
Copied here for easy of use since they don't have a distribution yet.
"""

"""Configuration class for xLAM client."""
class xLAMConfig:
    r"""
    Configuration class for xLAM client.

    Args:
        base_url (`str`):
            The base URL for the chat completion endpoint.
        model (`str`):
            The model name for within the xLAM series.

    Attributes:
        BASE_URL (`str`):
            The base URL for API requests.
        MODEL_NAME (`str`):
            The name of the xLAM model.
        TASK_INSTRUCTION (`str`):
            Instructions defining the task for the AI assistant.
        FORMAT_INSTRUCTION (`str`):
            Instructions on how to format the output.
    """
    TASK_INSTRUCTION = """
    Based on the previous context and API request history, generate an API request or a response as an AI assistant.""".strip()

    FORMAT_INSTRUCTION = """
    The output should be of the JSON format, which specifies a list of generated function calls. The example format is as follows, please make sure the parameter type is correct. If no function call is needed, please make 
    tool_calls an empty list "[]".
    ```
    {"thought": "the thought process, or an empty string", "tool_calls": [{"name": "api_name1", "arguments": {"argument1": "value1", "argument2": "value2"}}]}
    ```
    """.strip()
    
    def __init__(self, base_url: str, model: str):
        self.BASE_URL = base_url
        self.MODEL_NAME = model


class xLAMChatCompletion:
    r"""
    A class for handling chat completions using the xLAM model.

    Args:
        base_url (`str`):
            The base URL for the API endpoint.
        model_name (`str`):
            The name of the xLAM model to use.
        task_instruction (`str`):
            Instructions defining the task for the model.
        format_instruction (`str`):
            Instructions on how to format the output.

    Attributes:
        model_name (`str`):
            The name of the xLAM model to use.
        client (`OpenAI`):
            An OpenAI client instance for making API calls.
        task_instruction (`str`):
            Instructions defining the task for the model.
        format_instruction (`str`):
            Instructions on how to format the output.

    Methods:
        from_config(`xLAMConfig`):
            Class method to create an instance from an xLAMConfig object.
        completion(`List[Dict[str, str]]`, `Optional[List[Dict[str, Any]]]`, `**kwargs`):
            Generate a chat completion based on provided messages and tools.
    """

    def __init__(
        self, 
        base_url: str,
        model: str,
        task_instruction: str=xLAMConfig.TASK_INSTRUCTION, 
        format_instruction: str=xLAMConfig.FORMAT_INSTRUCTION
    ):
        self.model_name = model
        self.client = OpenAI(base_url=base_url, api_key="EMPTY")
        self.task_instruction = task_instruction
        self.format_instruction = format_instruction
    
    @classmethod
    def from_config(cls, config: xLAMConfig):
        return cls(
            model=config.MODEL_NAME,
            base_url=config.BASE_URL,
            task_instruction=config.TASK_INSTRUCTION,
            format_instruction=config.FORMAT_INSTRUCTION
        )
    
    def completion(self, messages, tools=None, **kwargs):
        # Convert OpenAI-style functions to xLAM format
        if messages[0]['role'] == 'system':
            system_message = messages[0]
            messages = messages[1:]
        else:
            system_message = None
            
        xlam_tools = self.convert_to_xlam_tool(tools) if tools else []
        
        # Extract the user's query (last user message)
        query = next((msg['content'] for msg in reversed(messages) if msg['role'] == 'user'), "")
        
        # Build conversation history from messages
        conversation_history = self.build_conversation_history(messages)
        
        # Build the prompt
        content = self.build_prompt(self.task_instruction, self.format_instruction, xlam_tools, query, conversation_history, system_message)
        
        # Generate response
        inputs = [{'role': 'user', 'content': content}]
        outputs = self.client.chat.completions.create(messages=inputs, model=self.model_name, **kwargs)
        agent_action = outputs.choices[0].message.content
        
        # Parse the response
        thought, tool_calls = self.parse_agent_action(agent_action)
        
        return {
            'choices': [{
                'message': {
                    'role': 'assistant',
                    'content': thought,
                    'tool_calls': tool_calls if tool_calls else []
                }
            }]
        }

    def convert_to_xlam_tool(self, tools):
        '''Convert OpenAPI-specification functions to xLAM format'''
        if isinstance(tools, dict):
            return {
                "name": tools["name"],
                "description": tools["description"],
                "parameters": {k: v for k, v in tools["parameters"].get("properties", {}).items()}
            }
        elif isinstance(tools, list):
            return [self.convert_to_xlam_tool(tool) for tool in tools]
        else:
            return tools

    def build_prompt(self, task_instruction: str, format_instruction: str, tools: list, query: str, conversation_history: list, system_message: str):
        if system_message:
            prompt = f"{system_message}\n\n"
        else:
            prompt = ""
        prompt += f"[BEGIN OF TASK INSTRUCTION]\n{task_instruction}\n[END OF TASK INSTRUCTION]\n\n"
        prompt += f"[BEGIN OF AVAILABLE TOOLS]\n{json.dumps(tools)}\n[END OF AVAILABLE TOOLS]\n\n"
        prompt += f"[BEGIN OF FORMAT INSTRUCTION]\n{format_instruction}\n[END OF FORMAT INSTRUCTION]\n\n"
        prompt += f"[BEGIN OF QUERY]\n{query}\n[END OF QUERY]\n\n"
        
        if len(conversation_history) > 0: prompt += self.build_conversation_history_prompt(conversation_history)
        return prompt
        
    def build_conversation_history_prompt(self, conversation_history: str):
        parsed_history = []
        for step_data in conversation_history:
            parsed_history.append({
                "step_id": step_data["step_id"],
                "thought": step_data["thought"],
                "tool_calls": step_data["tool_calls"],
                "next_observation": step_data["next_observation"],
                "user_input": step_data['user_input']
            })
            
        history_string = json.dumps(parsed_history)
        return f"\n[BEGIN OF HISTORY STEPS]\n{history_string}\n[END OF HISTORY STEPS]\n"
        
    def parse_agent_action(self, agent_action: str):
        """
        Given an agent's action, parse it to add to conversation history
        """
        try: parsed_agent_action_json = json.loads(agent_action)
        except: return "", []
        if "thought" not in parsed_agent_action_json.keys(): thought = ""
        else: thought = parsed_agent_action_json["thought"]
        
        if "tool_calls" not in parsed_agent_action_json.keys(): tool_calls = []
        else: tool_calls = parsed_agent_action_json["tool_calls"]
        
        return thought, tool_calls

    def build_conversation_history(self, messages):
        history = []
        for msg in messages:
            if msg['role'] == 'tool':
                history[-1]['next_observation'] = msg['content']
            else:
                history.append({
                    'step_id': len(history) + 1,
                    'thought': msg.get('content', ''),
                    'tool_calls': [msg['tool_calls']] if 'tool_calls' in msg else [],
                    'next_observation': '',
                    'user_input': msg['content'] if msg['role'] == 'user' else ''
                })
        return history
# fmt: on
