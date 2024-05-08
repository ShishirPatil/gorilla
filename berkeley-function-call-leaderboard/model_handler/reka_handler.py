

import os, time, json
from model_handler.handler import BaseHandler
from model_handler.model_style import ModelStyle
from model_handler.constant import (
    SYSTEM_PROMPT_FOR_CHAT_MODEL,
    USER_PROMPT_FOR_CHAT_MODEL,
    GORILLA_TO_OPENAPI,
)
from model_handler.utils import (
    convert_to_tool,
    ast_parse,
    convert_to_function_call,
    augment_prompt_by_languge,
    language_specific_pre_processing,
)
import requests

class RekaHandler(BaseHandler):
    def __init__(self, 
                 model_name, 
                 temperature=0.7, 
                 top_p=1, 
                 max_tokens=1000,
                 reka_server="https://api.aws-staging.reka.ai" # staging
                 ) -> None:
        super().__init__(model_name, temperature, top_p, max_tokens)
        self._SERVER = reka_server
        self._API_KEY = os.getenv("REKA_API_KEY")
        self.model_style = ModelStyle.Reka

    def inference(self, prompt, functions, test_category):
        prompt = augment_prompt_by_languge(prompt, test_category)

        functions = language_specific_pre_processing(
            functions, test_category, False
        )

        human_message = SYSTEM_PROMPT_FOR_CHAT_MODEL + "\n"
        human_message += USER_PROMPT_FOR_CHAT_MODEL.format(
            user_prompt=prompt, functions=str(functions))

        print(f"Prompt: {human_message}\n")

        start = time.time()

        # Using Reka's REST API because token length metadata
        # is not included in the python API.
        conversation_history = [
            {"type": "human", "text": human_message}
        ]
        result = requests.post(
            url=self._SERVER + "/chat",
            json={
                "conversation_history": conversation_history,
                "model_name": self.model_name,
                "runtime_top_p": self.top_p,
                "temperature": self.temperature,
            },
            headers={"X-Api-Key": self._API_KEY},
        )


        latency = time.time() - start
        response = result.json()

        try:
            metadata = {
                "input_tokens": response["metadata"]["input_tokens"],
                "output_tokens": response["metadata"]["generated_tokens"],
                "latency": latency,
            }
        except Exception as e:
            print(f"Invalid response from Reka: {response}")
            raise e
        return response["text"], metadata
    
    def decode_ast(self, result, language="Python"):
        json_blocks = result.split("```")
        if len(json_blocks) > 1:
            result = json_blocks[1]
        
        if result.startswith("json"):
            result = result[len("json"):]
        elif result.startswith("python"):
            result = result[len("python"):]
        result = result.replace("\n", "").strip()

        print(f"Result: {result}")

        decoded_output = ast_parse(result, language)
        return decoded_output

    def decode_execute(self, result):
        json_blocks = result.split("```")
        if len(json_blocks) > 1:
            result = json_blocks[1]
        
        if result.startswith("json"):
            result = result[len("json"):]
        elif result.startswith("python"):
            result = result[len("python"):]
        result = result.replace("\n", "").strip()

        print(f"Result: {result}")

        decoded_output = ast_parse(result)
        execution_list = []
        for function_call in decoded_output:
            for key, value in function_call.items():
                execution_list.append(
                    f"{key}({','.join([f'{k}={repr(v)}' for k, v in value.items()])})"
                )
        return execution_list