import pdb
import re, time

from bfcl.model_handler.constant import DEFAULT_SYSTEM_PROMPT
from bfcl.model_handler.handler import BaseHandler
from bfcl.model_handler.model_style import ModelStyle
from bfcl.model_handler.utils import (
    ast_parse,
    combine_consecutive_user_prompr,
    convert_system_prompt_into_user_prompt,
    func_doc_language_specific_pre_processing,
    system_prompt_pre_processing_chat_model,
)
from transformers import (  # type: ignore
    AutoModelForCausalLM,
    AutoTokenizer,
    GenerationConfig,
    pipeline,
    PreTrainedTokenizerFast,
)


class HuggingFaceHandler(BaseHandler):
    def __init__(
        self,
        model_name,
        temperature=0,
        top_p=1,
        max_tokens=1000,
        add_generation_prompt=True,
        system_prompt_support=False,
        attn_implementation=None,
    ) -> None:
        super().__init__(model_name, temperature, top_p, max_tokens)
        self.model_style = ModelStyle.OSSMODEL
        self.system_prompt_support = system_prompt_support
        self.add_generation_prompt = add_generation_prompt
        self.attn_implementation = attn_implementation
        self.model_name = model_name

    def _format_prompt(self, prompt, function, test_category, tokenizer):
        if isinstance(prompt, str):
            return prompt
        elif isinstance(prompt, list):
            if self.system_prompt_support:
                msg_list = prompt
            # If the model does not support system prompt, we need to convert the system prompt into user prompt.
            else:
                msg_list = convert_system_prompt_into_user_prompt(prompt)
                msg_list = combine_consecutive_user_prompr(msg_list)
            return tokenizer.apply_chat_template(
                msg_list,
                tokenize=False,
                add_generation_prompt=True,
            )
        else:
            raise NotImplementedError(f"Unsupported prompt type {type(prompt)}")

    def process_input(
        self,
        test_question,
        format_prompt_func,
        tokenizer,
        include_system_prompt=True,
    ):
        prompts = []
        for question in test_question:
            test_category = question["id"].rsplit("_", 1)[0]
            functions = func_doc_language_specific_pre_processing(
                question["function"], test_category
            )
            # Only the chat model needs the system prompt; also some require special formatting
            if include_system_prompt:
                question["question"] = system_prompt_pre_processing_chat_model(
                    question["question"], DEFAULT_SYSTEM_PROMPT, functions
                )

            formatted_prompt = format_prompt_func(
                question["question"], functions, test_category, tokenizer
            )
            prompts.append(formatted_prompt)

        return prompts

    def inference(
        self,
        test_question,
        num_gpus,
        gpu_memory_utilization,
        format_prompt_func=None,
        stop_token_ids=None,
        max_model_len=None,
        include_system_prompt=True,
    ):

        model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            device_map="auto",
            torch_dtype="auto",
            trust_remote_code=True,
            attn_implementation=(
                self.attn_implementation
                if self.attn_implementation is not None
                else None
            ),
        )
        tokenizer = AutoTokenizer.from_pretrained(
            self.model_name,
            padding_size="left",
            truncation=True,
            trust_remote_code=True,
        )
        if tokenizer.pad_token_id is None:
            tokenizer.pad_token_id = (
                model.config.pad_token_id
                or tokenizer.eos_token_id
                or model.config.eos_token_id
            )
        prompts = self.process_input(
            test_question,
            (
                format_prompt_func
                if format_prompt_func is not None
                else self._format_prompt
            ),
            tokenizer,
            include_system_prompt=include_system_prompt,
        )

        final_ans_jsons = []
        for prompt in prompts:
            pipe = pipeline(
                "text-generation",
                model=model,
                tokenizer=tokenizer,
            )

            message = prompt
            print("Prompt: ", message)
            output = pipe(
                message,
                max_new_tokens=self.max_tokens,
                temperature=self.temperature,
                top_p=self.top_p,
                return_full_text=False,
            )
            result = output[0]["generated_text"]
            print("Generation: ", result)

            final_ans_jsons.append(result)

        return final_ans_jsons, prompts

    def decode_ast(self, result, language="Python"):
        result = result.strip()
        PRETTY_FORMAT_PATTERN = r"```\n?(python|json|tool_code)\n?(.*)\n?```"
        pattern = r"\[(.*)\]"
        # Searching for the pattern in the input text

        unformatted = re.search(PRETTY_FORMAT_PATTERN, result, re.DOTALL)
        raw_match = re.search(PRETTY_FORMAT_PATTERN, result, re.DOTALL)
        if unformatted:
            removed_formatting = unformatted.group(2)
            match = re.search(pattern, removed_formatting, re.DOTALL)
            if match:
                raw_input = match.group(1)
            else:
                raw_input = removed_formatting
        elif raw_match:
            raw_input = raw_match.group(1)
        else:
            raw_input = result
        raw = raw_input.strip()
        func = "[" + raw + "]"
        decoded_output = ast_parse(func, language=language)

        return decoded_output

    def decode_execute(self, result):
        result = result.strip()
        PRETTY_FORMAT_PATTERN = r"```\n?(python|json|tool_code)\n?(.*)\n?```"
        pattern = r"\[(.*)\]"
        # Searching for the pattern in the input text

        unformatted = re.search(PRETTY_FORMAT_PATTERN, result, re.DOTALL)
        raw_match = re.search(PRETTY_FORMAT_PATTERN, result, re.DOTALL)
        if unformatted:
            removed_formatting = unformatted.group(2)
            match = re.search(pattern, removed_formatting, re.DOTALL)
            if match:
                raw_input = match.group(1)
            else:
                raw_input = removed_formatting
        elif raw_match:
            raw_input = raw_match.group(1)
        else:
            raw_input = result
        raw = raw_input.strip()
        func = "[" + raw + "]"
        decoded_output = ast_parse(func, language=language)

        execution_list = []
        for function_call in decoded_output:
            for key, value in function_call.items():
                execution_list.append(
                    f"{key}({','.join([f'{k}={repr(v)}' for k, v in value.items()])})"
                )
        return execution_list
