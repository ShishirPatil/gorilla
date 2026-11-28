"""Handler for SmolLM3-based models (e.g. Sentovara/Sentinel-3B), native FC.
SmolLM3 uses the same <tool_call>{json}</tool_call> output format as Qwen, so this subclasses QwenFCHandler.
The only change is the prompt: it is built with the model's own chat template (tokenizer.apply_chat_template,
tools passed natively) in SmolLM3's no-think mode ("/no_think" in the system message)."""
import json
import re

from bfcl_eval.model_handler.local_inference.qwen_fc import QwenFCHandler
from overrides import override


class SmolLM3FCHandler(QwenFCHandler):
    @override
    def _format_prompt(self, messages, function):
        msgs = []
        for i, m in enumerate(messages):
            role, content = m["role"], (m.get("content") or "")
            if role == "assistant" and m.get("tool_calls"):
                calls = []
                for tc in m["tool_calls"]:
                    tc = tc.get("function", tc)
                    args = tc.get("arguments", {})
                    if isinstance(args, str):
                        try: args = json.loads(args)
                        except Exception: pass
                    calls.append("<tool_call>\n" + json.dumps({"name": tc["name"], "arguments": args}) + "\n</tool_call>")
                content = (content + "\n" if content else "") + "\n".join(calls)
            elif role == "tool":
                content = "<tool_response>\n" + str(content) + "\n</tool_response>"
            msgs.append({"role": role, "content": content})
        if msgs and msgs[0]["role"] == "system":
            msgs[0]["content"] = msgs[0]["content"] + "\n/no_think"
        else:
            msgs = [{"role": "system", "content": "/no_think"}] + msgs
        return self.tokenizer.apply_chat_template(msgs, tools=function if function else None, tokenize=False, add_generation_prompt=True)

    @staticmethod
    @override
    def _extract_tool_calls(input_string):
        result = []
        for match in re.findall(r"<tool_call>\s*(.*?)\s*</tool_call>", input_string, re.DOTALL):
            try: result.append(json.loads(match))
            except Exception: pass
        return result
