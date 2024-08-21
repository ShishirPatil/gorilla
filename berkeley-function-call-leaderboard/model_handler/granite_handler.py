import json

from model_handler.model_style import ModelStyle
from model_handler.oss_handler import OSSHandler
from model_handler.constant import GORILLA_TO_OPENAPI, DEFAULT_SYSTEM_PROMPT
from model_handler.utils import convert_to_tool


class GraniteHandler(OSSHandler):
    def __init__(self, model_name, temperature=0.001, top_p=1, max_tokens=1000) -> None:
        super().__init__(model_name, temperature, top_p, max_tokens)

    def _format_prompt(prompts, function, test_category):
        prompt_str = (
            "SYSTEM: You are a helpful assistant with access to the following function calls. "
            "Your task is to produce a sequence of function calls necessary to generate response to the user utterance. "
            "Use the following function calls as required."
            "\n<|function_call_library|>\n{functions_str}\n"
            'If none of the functions are relevant or the given question lacks the parameters required by the function, please output "<function_call> {"name": "no_function", "arguments": {}}".\n\n'
        )

        function = convert_to_tool(
            function,
            GORILLA_TO_OPENAPI,
            model_style=ModelStyle.OSSMODEL,
            test_category=test_category,
        )

        functions_str = "\n".join([json.dumps(func) for func in function])
        prompt_str = prompt_str.replace("{functions_str}", functions_str)

        for prompt in prompts:
            prompt_str += f"{prompt['role'].upper()}:\n{prompt['content']}\n\n"

        prompt_str += "ASSISTANT: "

        return prompt_str

    def inference(
        self,
        test_question,
        num_gpus,
        gpu_memory_utilization,
        backend,
        format_prompt_func=_format_prompt,
    ):
        return super().inference(
            test_question,
            num_gpus,
            gpu_memory_utilization,
            backend, 
            format_prompt_func=format_prompt_func,
            use_default_system_prompt=False,
            include_default_formatting_prompt=False,
        )

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
