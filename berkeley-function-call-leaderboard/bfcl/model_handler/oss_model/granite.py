import json

from bfcl.model_handler.constant import GORILLA_TO_OPENAPI
from bfcl.model_handler.model_style import ModelStyle
from bfcl.model_handler.oss_model.base_oss_handler import OSSHandler
from bfcl.model_handler.utils import (
    convert_to_tool,
    func_doc_language_specific_pre_processing,
)


class GraniteHandler(OSSHandler):
    def __init__(self, model_name, temperature) -> None:
        super().__init__(model_name, temperature)

    def _format_prompt(self, messages, function):
        """
        "chat_template": "{% set function_str = messages.get('functions_str', {}) %}\n{% set query = messages['query'] %}\n{% set sys_prompt = 'You are a helpful assistant with access to the following function calls. Your task is to produce a sequence of function calls necessary to generate response to the user utterance. Use the following function calls as required. ' %}\n{% set funcstr = function_str|join('\n') %}\n{{ 'SYSTEM: ' + sys_prompt + '\n<|function_call_library|>\n' + funcstr + '\n\nIf none of the functions are relevant or the given question lacks the parameters required by the function, please output \"<function_call> {\"name\": \"no_function\", \"arguments\": {}}\".\n\nUSER: ' + query}}\n{% if add_generation_prompt %}\n{{ 'ASSISTANT:' }}{% endif %}",
        """

        prompt_str = (
            "SYSTEM: You are a helpful assistant with access to the following function calls. "
            "Your task is to produce a sequence of function calls necessary to generate response to the user utterance. "
            "Use the following function calls as required."
            "\n<|function_call_library|>\n{functions_str}\n"
            'If none of the functions are relevant or the given question lacks the parameters required by the function, please output "<function_call> {"name": "no_function", "arguments": {}}".\n\n'
        )

        function = convert_to_tool(
            function, GORILLA_TO_OPENAPI, model_style=ModelStyle.OSSMODEL
        )

        functions_str = "\n".join([json.dumps(func) for func in function])
        prompt_str = prompt_str.replace("{functions_str}", functions_str)

        for message in messages:
            prompt_str += f"{message['role'].upper()}:\n{message['content']}\n\n"

        prompt_str += "ASSISTANT: "

        return prompt_str

    def _pre_query_processing_prompting(self, test_entry: dict) -> dict:
        functions: list = test_entry["function"]
        test_category: str = test_entry["id"].rsplit("_", 1)[0]

        functions = func_doc_language_specific_pre_processing(functions, test_category)

        # Granite use its own system prompt

        return {"message": [], "function": functions}

    def decode_ast(self, result, language="Python"):
        decoded_outputs = []
        result = [
            call.strip()
            for call in result.split("<function_call>")
            if len(call.strip()) > 0
        ]

        for res in result:
            try:
                res = json.loads(res.strip())
            except:
                decoded_outputs.append(res)
            else:
                fnname = res.get("name", "").strip()
                args = res.get("arguments", {})

                if fnname == "no_function":
                    decoded_outputs.append("No function is called")
                    continue

                decoded_outputs.append({fnname: args})

        return decoded_outputs

    def decode_execute(self, result):
        decoded_outputs = []
        result = [
            call.strip()
            for call in result.split("<function_call>")
            if len(call.strip()) > 0
        ]

        for res in result:
            try:
                res = json.loads(res.strip())
            except:
                decoded_outputs.append(res)
            else:
                fnname = res.get("name", "").strip()
                args = res.get("arguments", {})

                if fnname == "no_function":
                    decoded_outputs.append("No function is called")
                    continue

                # decoded_outputs.append({fnname: args})
                args_str = ",".join(
                    [f"{argname}={repr(argval)}" for argname, argval in args.items()]
                )
                decoded_outputs.append(f"{fnname}({args_str})")

        return decoded_outputs
