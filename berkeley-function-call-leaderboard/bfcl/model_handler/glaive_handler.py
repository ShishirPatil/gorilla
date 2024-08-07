from bfcl.model_handler.oss_handler import OSSHandler
from bfcl.model_handler.utils import convert_to_function_call
import json


class GlaiveHandler(OSSHandler):
    def __init__(self, model_name, temperature=0.7, top_p=1, max_tokens=1000) -> None:
        super().__init__(model_name, temperature, top_p, max_tokens)

    def _format_prompt(prompt, function, test_category):
        formatted_prompt = """
            SYSTEM: You are an helpful assistant who has access to the following functions to help the user, you can use the functions if needed-
            {function}\n
            USER: {prompt}\n
        """
        return formatted_prompt.format(function=function, prompt=prompt)

    def inference(
        self, test_question, num_gpus, gpu_memory_utilization, format_prompt_func=_format_prompt
    ):
        return super().inference(
            test_question, num_gpus, gpu_memory_utilization, format_prompt_func=format_prompt_func
        )

    def decode_ast(self, result, language="Python"):
        function_call = result.split("<functioncall>")[-1]
        function_call = function_call.replace("'", "")
        decoded_function = json.loads(function_call)
        for key, value in decoded_function["arguments"].items():
            if language == "Python":
                pass
            else:
                # all values of the json are casted to string for java and javascript
                decoded_function["arguments"][key] = str(
                    decoded_function["arguments"][key]
                )
        decoded_result = [{decoded_function["name"]: decoded_function["arguments"]}]
        return decoded_result

    def decode_execute(self, result):
        function_call = result.split("<functioncall>")[-1]
        function_call = function_call.replace("'", "")
        decoded_function = json.loads(function_call)
        decoded_result = [{decoded_function["name"]: decoded_function["arguments"]}]
        return convert_to_function_call(decoded_result)
