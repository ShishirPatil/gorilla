from model_handler.oss_handler import OSSHandler
from model_handler.utils import convert_to_tool
from model_handler.constant import GORILLA_TO_OPENAPI, DEFAULT_SYSTEM_PROMPT
from model_handler.model_style import ModelStyle
import json
import inspect


class HermesHandler(OSSHandler):
    def __init__(self, model_name, temperature=0.001, top_p=1, max_tokens=1000) -> None:
        super().__init__(model_name, temperature, top_p, max_tokens)
        # Only this specific Hermes model uses float16
        if model_name == "NousResearch/Hermes-2-Pro-Llama-3-8B":
            self.dtype = "float16"

    def _format_prompt(prompts, function, test_category):
        # Hermes use Langchain to OpenAI conversion. It does not use tool call but function call.
        function = convert_to_tool(
            function, GORILLA_TO_OPENAPI, ModelStyle.OSSMODEL, test_category
        )
        pydantic_format = """{"properties": {"arguments": {"title": "Arguments", "type": "object"}, "name": {"title": "Name", "type": "string"}}, "required": ["arguments", "name"], "title": "FunctionCall", "type": "object"}"""
        tool_call_format = """{"arguments": <args-dict>, "name": <function-name>}"""
        formatted_prompt = inspect.cleandoc(
            """<|im_start|>system
            You are a function calling AI model. You are provided with function signatures within <tools></tools> XML tags. You may call one or more functions to assist with the user query. Don't make assumptions about what values to plug into functions. Here are the available tools:
            <tools>
            {function}
            </tools>
            Use the following pydantic model json schema for each tool call you will make:
            {pydantic_format}
            For each function call return a json object with function name and arguments within <tool_call></tool_call> XML tags as follows:
            <tool_call>
            {tool_call_format}
            </tool_call>
            <|im_end|>
            """
        )

        formatted_prompt = formatted_prompt.format(
            function=function,
            pydantic_format=pydantic_format,
            tool_call_format=tool_call_format,
        )

        for prompt in prompts:
            formatted_prompt += (
                f"<|im_start|>{prompt['role']}\n{prompt['content']}\n<|im_end|>\n"
            )

        formatted_prompt += "<|im_start|>assistant"

        return formatted_prompt

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
        lines = result.split("\n")
        flag = False
        func_call = []
        for line in lines:
            if "<tool_call>" == line:
                flag = True
            elif "</tool_call>" == line:
                flag = False
            else:
                if flag:
                    line = line.replace("'", '"')
                    tool_result = json.loads(line)
                    func_call.append({tool_result["name"]: tool_result["arguments"]})
                flag = False
        return func_call

    def decode_execute(self, result):
        lines = result.split("\n")
        flag = False
        function_call_list = []
        for line in lines:
            if "<tool_call>" == line:
                flag = True
            elif "</tool_call>" == line:
                flag = False
            else:
                if flag:
                    line = line.replace("'", '"')
                    tool_result = json.loads(line)
                    function_call_list.append(
                        {tool_result["name"]: tool_result["arguments"]}
                    )
                flag = False
        execution_list = []
        for function_call in function_call_list:
            for key, value in function_call.items():
                execution_list.append(
                    f"{key}({','.join([f'{k}={repr(v)}' for k,v in value.items()])})"
                )
        return execution_list
