import json
import os
import time

import re
from bfcl.model_handler.base_handler import BaseHandler
from bfcl.constants.type_mappings import GORILLA_TO_OPENAPI
from bfcl.model_handler.model_style import ModelStyle
from bfcl.model_handler.utils import (
    convert_to_function_call,
    convert_to_tool,
    format_execution_results_prompting,
    func_doc_language_specific_pre_processing,
    retry_with_backoff,
)
from openai import OpenAI, RateLimitError


class MiningHandler(BaseHandler):
    def __init__(self, model_name, temperature) -> None:
        super().__init__(model_name, temperature)
        self.model_style = ModelStyle.OpenAI
        self.client = OpenAI(api_key=os.getenv("MINING_API_KEY"),base_url=os.getenv("MINING_API_BASE"))

    def decode_ast(self, result, language="Python"):
        if "FC" in self.model_name or self.is_fc_model:
            decoded_output = []
            for invoked_function in result:
                name = list(invoked_function.keys())[0]
                params = json.loads(invoked_function[name])
                decoded_output.append({name: params})
            return decoded_output
        else:
            decoded_output = []
            for invoked_function in result:
                name = invoked_function["name"]
                params = invoked_function["arguments"]
                decoded_output.append({name: params})
            return decoded_output
            # return default_decode_ast_prompting(result, language)

    def decode_execute(self, result):
        if "FC" in self.model_name or self.is_fc_model:
            return convert_to_function_call(result)
        else:
            # print("qwen_ming:45,decode_execute->",result)
            # return default_decode_execute_prompting(result)
            too_call_format = []
            for tool_call in result:
                if isinstance(tool_call, dict):
                    name = tool_call.get("name", "")
                    arguments = tool_call.get("arguments", {})
                    args_str = ", ".join(
                        [f"{key}={repr(value)}" for key, value in arguments.items()]
                    )
                    too_call_format.append(f"{name}({args_str})")
            # print("qwen_ming:45,decode_execute->",too_call_format)
            return too_call_format

    @retry_with_backoff(error_type=RateLimitError)
    def generate_with_backoff(self, **kwargs):
        start_time = time.time()
        kwargs.pop("temperature", None)  # None 确保 key 不存在时不会报错
        api_response = self.client.chat.completions.create(top_p=1,temperature=0,**kwargs)
        end_time = time.time()

        return api_response, end_time - start_time

    #### FC methods ####

    def _query_FC(self, inference_data: dict):
        message: list[dict] = inference_data["message"]
        tools = inference_data["tools"]
        inference_data["inference_input_log"] = {"message": repr(message), "tools": tools}

        if len(tools) > 0:
            # Reasoning models don't support temperature parameter
            # Beta limitation: https://platform.openai.com/docs/guides/reasoning/beta-limitations
            if "o1" in self.model_name or "o3-mini" in self.model_name:
                return self.generate_with_backoff(
                    messages=message,
                    model=self.model_name.replace("-FC", ""),
                    tools=tools,
                )
            else:
                return self.generate_with_backoff(
                    messages=message,
                    model=self.model_name.replace("-FC", ""),
                    temperature=self.temperature,
                    tools=tools,
                )
        else:
            if "o1" in self.model_name or "o3-mini" in self.model_name:
                return self.generate_with_backoff(
                    messages=message,
                    model=self.model_name.replace("-FC", ""),
                )
            else:
                return self.generate_with_backoff(
                    messages=message,
                    model=self.model_name.replace("-FC", ""),
                    temperature=self.temperature,
                )

    def _pre_query_processing_FC(self, inference_data: dict, test_entry: dict) -> dict:
        inference_data["message"] = []
        return inference_data

    def _compile_tools(self, inference_data: dict, test_entry: dict) -> dict:
        functions: list = test_entry["function"]
        test_category: str = test_entry["id"].rsplit("_", 1)[0]

        functions = func_doc_language_specific_pre_processing(functions, test_category)
        tools = convert_to_tool(functions, GORILLA_TO_OPENAPI, self.model_style)

        inference_data["tools"] = tools

        return inference_data

    def _parse_query_response_FC(self, api_response: any) -> dict:
        try:
            model_responses = [
                {func_call.function.name: func_call.function.arguments}
                for func_call in api_response.choices[0].message.tool_calls
            ]
            tool_call_ids = [
                func_call.id for func_call in api_response.choices[0].message.tool_calls
            ]
        except:
            model_responses = api_response.choices[0].message.content
            tool_call_ids = []

        model_responses_message_for_chat_history = api_response.choices[0].message

        return {
            "model_responses": model_responses,
            "model_responses_message_for_chat_history": model_responses_message_for_chat_history,
            "tool_call_ids": tool_call_ids,
            "input_token": api_response.usage.prompt_tokens,
            "output_token": api_response.usage.completion_tokens,
        }

    def add_first_turn_message_FC(
        self, inference_data: dict, first_turn_message: list[dict]
    ) -> dict:
        inference_data["message"].extend(first_turn_message)
        return inference_data

    def _add_next_turn_user_message_FC(
        self, inference_data: dict, user_message: list[dict]
    ) -> dict:
        inference_data["message"].extend(user_message)
        return inference_data

    def _add_assistant_message_FC(
        self, inference_data: dict, model_response_data: dict
    ) -> dict:
        inference_data["message"].append(
            model_response_data["model_responses_message_for_chat_history"]
        )
        return inference_data

    def _add_execution_results_FC(
        self,
        inference_data: dict,
        execution_results: list[str],
        model_response_data: dict,
    ) -> dict:
        # Add the execution results to the current round result, one at a time
        for execution_result, tool_call_id in zip(
            execution_results, model_response_data["tool_call_ids"]
        ):
            tool_message = {
                "role": "tool",
                "content": execution_result,
                "tool_call_id": tool_call_id,
            }
            inference_data["message"].append(tool_message)

        return inference_data

    #### Prompting methods ####

    def _query_prompting(self, inference_data: dict):
        inference_data["inference_input_log"] = {"message": repr(inference_data["message"])}
        return self.generate_with_backoff(
            messages=inference_data["message"],
            model=self.model_name,
            temperature=self.temperature,
        )


    def _pre_query_processing_prompting(self, test_entry: dict) -> dict:
        functions: list = test_entry["function"]
        test_category: str = test_entry["id"].rsplit("_", 1)[0]

        functions = func_doc_language_specific_pre_processing(functions, test_category)

        test_entry["question"][0] = self.mining_system_prompt_pre_processing_chat_model(
            test_entry["question"][0], functions, test_category
        )
        return {"message": []}

    def _parse_query_response_prompting(self, api_response: any) -> dict:
        match = re.search(r'<tool_calls>\n(.*?)\n</tool_calls>', api_response.choices[0].message.content, re.DOTALL)
        tool_calls = api_response.choices[0].message.content
        tool_call_format = []
        # 如果匹配不到则输出原始内容
        if match:
           tool_calls =  match.group(1).strip()
        try:
        #    calls = eval(calls)
            tool_calls = tool_calls.replace("'",'"')
            tool_calls = json.loads(tool_calls)
            # for tool_call in tool_calls:
            #     tool_name = tool_call.get("name","")
            #     arguments = tool_call.get("arguments","")

            #     tool_call_format.append()
        except:
            pass
        message = api_response.choices[0].message
        # message = [x.replace("'",'"') for x in message]
        # print("qwen_mining:209,->",calls)
        return {
            # "model_responses": api_response.choices[0].message.content,
            "model_responses": tool_calls,
            "model_responses_message_for_chat_history": message,
            "input_token": api_response.usage.prompt_tokens,
            "output_token": api_response.usage.completion_tokens,
        }

    def add_first_turn_message_prompting(
        self, inference_data: dict, first_turn_message: list[dict]
    ) -> dict:
        # print("qwen_mining:222,add_first_turn_message_prompting->",first_turn_message)
        inference_data["message"].extend(first_turn_message)
        return inference_data

    def _add_next_turn_user_message_prompting(
        self, inference_data: dict, user_message: list[dict]
    ) -> dict:
        inference_data["message"].extend(user_message)
        return inference_data

    def _add_assistant_message_prompting(
        self, inference_data: dict, model_response_data: dict
    ) -> dict:
        inference_data["message"].append(
            model_response_data["model_responses_message_for_chat_history"]
        )
        return inference_data

    def _add_execution_results_prompting(
        self, inference_data: dict, execution_results: list[str], model_response_data: dict
    ) -> dict:
        formatted_results_message = format_execution_results_prompting(
            inference_data, execution_results, model_response_data
        )
        inference_data["message"].append(
            {"role": "user", "content": formatted_results_message}
        )

        return inference_data
    def mining_system_prompt_pre_processing_chat_model(self,prompts, function_docs, test_category):
        system_pre="""You are a function calling AI model. 
You are provided with function signatures within <tools></tools> XML tags.
You may call one or more functions to assist with the user query. 
Don't make assumptions about what values to plug into functions.

Here are the available tools:
<tools> 
{}
</tools>
"""
        system_suffix = """

Use the following pydantic model json schema for each tool call you will make: 
{"title": "FunctionCalls", "type": "array", "properties": {"arguments": {"title": "Arguments", "type": "object"}, "name": {"title": "Name", "type": "string"}}, "required": ["arguments", "name"]}

# Output Format
If you find suitable function, for each function call return a json object with function name and arguments within <tool_calls></tool_calls> XML tags as follows:
<think>
{reasoning process here}
</think>
<tool_calls>
{[tool_call]}
</tool_calls>

If no suitable function is found, just respond with XML tags as follows:
<think>
{reasoning process here}
</think>
<tool_calls>
[]
</tool_calls>"""
        assert type(prompts) == list

        system_prompt = system_pre.format(function_docs)+system_suffix

        # System prompt must be in the first position
        # If the question comes with a system prompt, append its content at the end of the chat template.
        if prompts[0]["role"] == "system":
            prompts[0]["content"] = system_prompt + "\n\n" + prompts[0]["content"]
        # Otherwise, use the system prompt template to create a new system prompt.
        else:
            prompts.insert(
                0,
                {"role": "system", "content": system_prompt},
            )

        return prompts
