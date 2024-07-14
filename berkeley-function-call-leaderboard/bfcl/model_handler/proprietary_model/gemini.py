import subprocess
import time
import json
import os

import requests

from bfcl.model_handler import utils
from bfcl.model_handler import constants
from bfcl.model_handler.base import BaseHandler, ModelStyle


class GeminiHandler(BaseHandler):
    model_style = ModelStyle.GOOGLE

    def __init__(
        self, 
        model_name, 
        temperature=0.7, 
        top_p=1, 
        max_tokens=1000, 
        gcp_project_id: str | None = None
    ) -> None:
        
        super().__init__(model_name, temperature, top_p, max_tokens)
        if gcp_project_id is None:
            gcp_project_id = os.getenv('GEMINI_GCP_PROJECT_ID')
            
        assert gcp_project_id, (
            '`gcp_project_id` cannot be empty! To run the gemini model, you need to provide '
            'your own GCP project ID, which can be found in the GCP console.'
        )
        self.api_url = (
            f'https://us-central1-aiplatform.googleapis.com/v1beta1/projects/{gcp_project_id}/locations/us-central1/publishers/google/models/'
            + self.model_name 
            + ":generateContent"
        )

    @classmethod
    def supported_models(cls):
        return [
            'gemini-1.0-pro',
            'gemini-1.5-pro-preview-0409',
            'gemini-1.5-pro-preview-0514',
            'gemini-1.5-flash-preview-0514',
        ]

    def inference(self, prompt, functions, test_category):
        prompt = utils.augment_prompt_by_languge(prompt, test_category)
        functions = utils.language_specific_pre_processing(functions, test_category, True)
        gemini_tool = utils.convert_to_tool(functions, constants.GORILLA_TO_OPENAPI, self.model_style, test_category, True)
        result, metadata = self._query_gemini(prompt, gemini_tool)
        return result, metadata

    def decode_ast(self, result, language="python"):
        if type(result) is not list:
            result = [result]
        decoded_output = []
        for invoked_function in result:
            name = list(invoked_function.keys())[0]
            params = json.loads(invoked_function[name])
            if language != "Python":
                for key in params:
                    params[key] = str(params[key])
            decoded_output.append({name: params})
        return decoded_output

    def decode_execute(self, result):
        return utils.convert_to_function_call(result)

    def _query_gemini(self, user_query, functions):
        token = subprocess.run(
            "gcloud auth print-access-token",
            check=False,
            shell=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

        json_data = {
            "contents": {
                "role": "user",
                "parts": {
                    "text": user_query,
                },
            },
            "generation_config": {
                "max_output_tokens": self.max_tokens,
                "temperature": self.temperature,
            },
            "tools": {"function_declarations": functions},
        }
        headers = {
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
        }
        start = time.time()
        response = requests.post(self.api_url, headers=headers, data=json.dumps(json_data))
        latency = time.time() - start
        result = json.loads(response.content)
        if "error" in result:
            return result["error"]["message"], {
                "input_tokens": 0,
                "output_tokens": 0,
                "latency": latency,
            }
        try:
            parts = []
            for part in result["candidates"][0]["content"]["parts"]:
                if "functionCall" in part:
                    if (
                        "name" in part["functionCall"]
                        and "args" in part["functionCall"]
                    ):
                        parts.append({part["functionCall"]["name"]: json.dumps(part["functionCall"]["args"])})
                    else:
                        parts.append("Parsing error: " + json.dumps(part["functionCall"]))
                else:
                    parts.append(part["text"])
            result = parts
            metatdata = {}
            metatdata["input_tokens"] = json.loads(response.content)["usageMetadata"]["promptTokenCount"]
            metatdata["output_tokens"] = json.loads(response.content)["usageMetadata"]["candidatesTokenCount"]
            metatdata["latency"] = latency
        except Exception:
            result = "Parsing error: " + json.dumps(result)
            metatdata = {
                "input_tokens": 0,
                "output_tokens": 0,
                "latency": latency,
            }
        return result, metatdata
