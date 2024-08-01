import json

from bfcl.model_handler.model_style import ModelStyle
from bfcl.model_handler.oss_handler import OSSHandler
from bfcl.model_handler.constant import GORILLA_TO_OPENAPI
from bfcl.model_handler.utils import (
    language_specific_pre_processing,
    convert_to_tool,
    augment_prompt_by_languge,
)


class GraniteHandler(OSSHandler):
    def __init__(self, model_name, temperature=0.7, top_p=1, max_tokens=1000) -> None:
        temperature = 0.001
        super().__init__(model_name, temperature, top_p, max_tokens)

    def _format_prompt(prompt, function, test_category):
        prompt_str = (
            "SYSTEM: You are a helpful assistant with access to the following function calls. "
            "Your task is to produce a sequence of function calls necessary to generate response to the user utterance. "
            "Use the following function calls as required."
            "\n<|function_call_library|>\n{functions_str}\n"
            'If none of the functions are relevant or the given question lacks the parameters required by the function, please output "<function_call> {"name": "no_function", "arguments": {}}".\n\n'
            "USER: {query}\nASSISTANT: "
        )

        # Remove the language specific prompt augmentation string, such as "Note that the provided function is in Python"
        language_specific_prompt_augmented_str = augment_prompt_by_languge(
            "", test_category
        )
        if language_specific_prompt_augmented_str.strip():
            prompt = prompt.replace(language_specific_prompt_augmented_str, "")

        functions = language_specific_pre_processing(function, test_category)
        functions = convert_to_tool(
            functions,
            GORILLA_TO_OPENAPI,
            model_style=ModelStyle.OSSMODEL,
            test_category=test_category,
        )

        functions_str = "\n".join([json.dumps(func) for func in function])

        prompt = prompt_str.replace("{functions_str}", functions_str).replace(
            "{query}", prompt
        )
        return prompt

    def inference(
        self, test_question, num_gpus, gpu_memory_utilization, format_prompt_func=_format_prompt
    ):
        return super().inference(
            test_question, num_gpus, gpu_memory_utilization, format_prompt_func=format_prompt_func
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
