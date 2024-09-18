from bfcl.model_handler.oss_model.base_oss_handler import OSSHandler
from bfcl.model_handler.utils import convert_to_function_call
from bfcl.model_handler.utils import convert_to_tool
from bfcl.model_handler.constant import GORILLA_TO_OPENAPI
from bfcl.model_handler.model_style import ModelStyle
import json

class GLMHandler(OSSHandler):
    def __init__(self, model_name, temperature=0.001, top_p=1, max_tokens=1000) -> None:
        super().__init__(model_name, temperature, top_p, max_tokens)
        self.max_model_len = 8704
        self.stop_token_ids = [151329, 151336, 151338]

    def apply_chat_template(self, prompts, functions, test_category):
        formatted_prompt = ""
        oai_tool = convert_to_tool(functions, GORILLA_TO_OPENAPI, ModelStyle.OpenAI, test_category)
        if oai_tool:
            formatted_prompt = "[gMASK]<sop><|system|>\n你是一个名为 ChatGLM 的人工智能助手。你是基于智谱AI训练的语言模型 GLM-4 模型开发的，你的任务是针对用户的问题和要求提供适当的答复和支持。\n\n# 可用工具"
            for tool in oai_tool:
                formatted_prompt += f"\n\n## {tool['function']['name']}\n\n{json.dumps(tool['function'], indent=4)}"
                formatted_prompt += "\n在调用上述函数时，请使用 Json 格式表示调用的参数。"

        for prompt in prompts:
            formatted_prompt += f"<|{prompt['role']}|>\n{prompt['content']}"
        formatted_prompt += "<|assistant|>"
        return formatted_prompt

    def inference(self, test_question, num_gpus, gpu_memory_utilization):

        return super().inference(
            test_question,
            num_gpus,
            gpu_memory_utilization,
            format_prompt_func=self.apply_chat_template,
            stop_token_ids=self.stop_token_ids,
            max_model_len=self.max_model_len,
            include_system_prompt=False,  # they have special formatting
        )

    def decode_ast(self, result, language="Python"):
        args = result.split("\n")
        if len(args) == 1:
            func = [args[0]]
        elif len(args) >= 2:
            func = [{args[0]: json.loads(args[1])}]
        return func

    def decode_execute(self, result):
        args = result.split("\n")
        if len(args) == 1:
            func = args[0]
        elif len(args) >= 2:
            func = [{args[0]: args[1]}]

        return convert_to_function_call(func)
