import json

from bfcl_eval.model_handler.local_inference.base_oss_handler import OSSHandler
from bfcl_eval.model_handler.utils import func_doc_language_specific_pre_processing
from overrides import override


class Falcon3FCHandler(OSSHandler):
    def __init__(self, model_name, temperature) -> None:
        super().__init__(model_name, temperature)
        self.model_name_huggingface = model_name.replace("-FC", "")

    @override
    def _format_prompt(self, messages, function):
        """Format the prompt according to Falcon 3's chat template."""
        tokenizer = self.tokenizer
        formatted_prompt = tokenizer.apply_chat_template(
            messages,
            tools=function,
            tokenize=False,
            add_generation_prompt=True
        )
        return formatted_prompt

    @override
    def decode_ast(self, result, language="Python"):
        """Decode the model's response into AST format."""
        try:
            if "<tool_call>" not in result:
                return []

            tool_calls_str = result.split("<tool_call>")[1].split("</tool_call>")[0].strip()

            if tool_calls_str.startswith("```") and tool_calls_str.endswith("```"):
                tool_calls_str = tool_calls_str.strip("```").strip()
                if tool_calls_str.startswith("json"):
                    tool_calls_str = tool_calls_str[4:].strip()

            tool_calls = json.loads(tool_calls_str)
            if not isinstance(tool_calls, list):
                tool_calls = [tool_calls]

            # Convert to required format
            decoded_output = []
            for tool_call in tool_calls:
                name = tool_call["name"]
                params = tool_call["arguments"]
                decoded_output.append({name: params})

            return decoded_output
        except (json.JSONDecodeError, KeyError, IndexError):
            return []

    @override
    def decode_execute(self, result):
        """Convert the model's response into executable function calls."""
        try:
            if "<tool_call>" not in result:
                return []

            tool_calls_str = result.split("<tool_call>")[1].split("</tool_call>")[0].strip()

            if tool_calls_str.startswith("```") and tool_calls_str.endswith("```"):
                tool_calls_str = tool_calls_str.strip("```").strip()
                if tool_calls_str.startswith("json"):
                    tool_calls_str = tool_calls_str[4:].strip()

            tool_calls = json.loads(tool_calls_str)
            if not isinstance(tool_calls, list):
                tool_calls = [tool_calls]

            execution_list = []
            for tool_call in tool_calls:
                name = tool_call["name"]
                params = tool_call["arguments"]
                param_str = ",".join([f"{k}={repr(v)}" for k, v in params.items()])
                execution_list.append(f"{name}({param_str})")

            return execution_list
        except (json.JSONDecodeError, KeyError, IndexError):
            return []

    @override
    def _pre_query_processing_prompting(self, test_entry: dict) -> dict:
        """Pre-process the query before sending it to the model."""
        functions: list = test_entry["function"]
        test_category: str = test_entry["id"].rsplit("_", 1)[0]

        functions = func_doc_language_specific_pre_processing(functions, test_category)

        return {"message": [], "function": functions}
