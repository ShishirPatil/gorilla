from bfcl.model_handler.oss_model.base_oss_handler import OSSHandler
from bfcl.model_handler.model_style import ModelStyle
import json
from bfcl.model_handler.utils import (
    convert_to_tool,
)
from bfcl.model_handler.constant import (
    GORILLA_TO_OPENAPI,
)


class EmpowerHandler(OSSHandler):
    def __init__(self, model_name, temperature) -> None:
        super().__init__(model_name, temperature)

    def _preprocess_messages(self, messages):
        # remove system message
        messages = [
            message for message in messages if message['role'] != "system"]

        # combine tool responses
        result = []
        temp_tool_content = None
        for message in messages:
            if message['role'] == 'tool':
                decoded_content = json.loads(message['content'])
                if temp_tool_content:
                    temp_tool_content.append(decoded_content)
                else:
                    temp_tool_content = [decoded_content]
            else:
                if temp_tool_content:
                    result.append({
                        'role': 'tool',
                        'content': json.dumps(temp_tool_content, indent=2)
                    })
                    temp_tool_content = None
                result.append(message)
        if temp_tool_content:
            result.append({
                'role': 'tool',
                'content': json.dumps(temp_tool_content, indent=2)
            })

        return result

    def _format_prompt(self, messages, functions):
        formatted_prompt = "<|begin_of_text|>"

        for idx, message in enumerate(self._preprocess_messages(messages)):
            if idx == 0:
                tools = convert_to_tool(
                    functions, GORILLA_TO_OPENAPI, ModelStyle.OSSMODEL
                )
                message['content'] = "In this environment you have access to a set of functions defined in the JSON format you can use to address user's requests, use them if needed.\nFunctions:\n" \
                    + json.dumps(tools, indent=2) \
                    + "\n\n" \
                    + "User Message:\n" \
                    + message['content']
            else:
                if message['role'] == 'tool':
                    message['role'] = 'user'
                    message['content'] = '<r>' + message['content']
                elif message['role'] == 'user' and not message['content'].startswith('<r>') and not message['content'].startswith('<u>'):
                    message['content'] = '<u>' + message['content']

            formatted_prompt += f"<|start_header_id|>{message['role']}<|end_header_id|>\n\n{message['content']}<|eot_id|>"

        formatted_prompt += f"<|start_header_id|>assistant<|end_header_id|>\n\n"

        return formatted_prompt

    def decode_ast(self, result, language="Python"):
        if not result.startswith('<f>'):
            return []

        # strip the function/conversation tag <f>/<c>
        result_stripped = result[3:]

        decoded_output = []
        for invoked_function in json.loads(result_stripped):
            name = invoked_function["name"]
            params = invoked_function["arguments"] if "arguments" in invoked_function else {
            }
            decoded_output.append({name: params})

        return decoded_output

    def decode_execute(self, result):
        execution_list = []

        for function_call in self.decode_ast(result):
            for key, value in function_call.items():
                argument_list = []
                for k, v in value.items():
                    argument_list.append(f'{k}={repr(v)}')
                execution_list.append(
                    f"{key}({','.join(argument_list)})"
                )

        return execution_list
