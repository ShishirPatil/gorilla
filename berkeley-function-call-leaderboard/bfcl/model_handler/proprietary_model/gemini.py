from bfcl.model_handler.base_handler import BaseHandler
from bfcl.model_handler.model_style import ModelStyle
from bfcl.model_handler.utils import (
    convert_to_tool,
    convert_to_function_call,
    func_doc_language_specific_pre_processing,
)
from bfcl.model_handler.constant import GORILLA_TO_OPENAPI
import subprocess, requests, json, time


class GeminiHandler(BaseHandler):
    def __init__(self, model_name, temperature=0.001, top_p=1, max_tokens=1000) -> None:
        super().__init__(model_name, temperature, top_p, max_tokens)
        self.model_style = ModelStyle.Google

    def _query_gemini(self, prompt, functions):
        """
        Query Gemini Pro model.
        """
        YOUR_GCP_PROJECT_ID_HERE = subprocess.run(
            "gcloud config get-value project",
            shell=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

        token = subprocess.run(
            "gcloud auth print-access-token",
            check=False,
            shell=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

        system_prompt = self._extract_system_prompt(prompt)
        if system_prompt:
            json_data = {
                "contents": prompt,
                "system_instruction": {"parts": [{"text": system_prompt}]},
                "generation_config": {
                    "max_output_tokens": self.max_tokens,
                    "temperature": self.temperature,
                },
                "tools": {"function_declarations": functions},
            }
        else:
            json_data = {
                "contents": prompt,
                "generation_config": {
                    "max_output_tokens": self.max_tokens,
                    "temperature": self.temperature,
                },
                "tools": {"function_declarations": functions},
            }

        # NOTE: To run the gemini model, you need to provide your own GCP project ID, which can be found in the GCP console.
        API_URL = (
            f"https://us-central1-aiplatform.googleapis.com/v1beta1/projects/{YOUR_GCP_PROJECT_ID_HERE}/locations/us-central1/publishers/google/models/"
            + self.model_name
            + ":generateContent"
        )
        headers = {
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
        }
        start = time.time()
        response = requests.post(
            API_URL,
            headers=headers,
            data=json.dumps(json_data),
        )
        latency = time.time() - start
        result = json.loads(response.content)
        if "error" in result:
            return result["error"]["message"], {
                "latency": latency,
                "processed_message": {"system": system_prompt, "message": prompt},
                "processed_tool": functions,
            }
        try:
            fc_parts = []
            text_parts = []
            for part in result["candidates"][0]["content"]["parts"]:
                if "functionCall" in part:
                    if (
                        "name" in part["functionCall"]
                        and "args" in part["functionCall"]
                    ):
                        fc_parts.append(
                            {
                                part["functionCall"]["name"]: json.dumps(
                                    part["functionCall"]["args"]
                                )
                            }
                        )
                    else:
                        text_parts.append(
                            "Parsing error: " + json.dumps(part["functionCall"])
                        )
                else:
                    text_parts.append(part["text"])
            if fc_parts:
                result = fc_parts
            else:
                result = text_parts
            metatdata = {}
            metatdata["input_token_count"] = json.loads(response.content)["usageMetadata"][
                "promptTokenCount"
            ]
            metatdata["output_token_count"] = json.loads(response.content)["usageMetadata"][
                "candidatesTokenCount"
            ]
            metatdata["latency"] = latency
            metatdata["processed_message"] = {"system": system_prompt, "message": prompt}
            metatdata["processed_tool"] = functions
        except Exception as e:
            result = "Parsing error: " + json.dumps(result)
            metatdata = {
                "latency": latency,
                "processed_message": {"system": system_prompt, "message": prompt},
                "processed_tool": functions,
            }
        return result, metatdata

    def _substitute_prompt_role(self, prompts):
        # Allowed roles: user, model, function
        modified_prompts = []
        for prompt in prompts:
            if prompt["role"] == "user":
                modified_prompts.append(
                    {"role": "user", "parts": [{"text": prompt["content"]}]}
                )
            elif prompt["role"] == "assistant":
                modified_prompts.append(
                    {"role": "model", "parts": [{"text": prompt["content"]}]}
                )
            elif prompt["role"] == "tool":
                modified_prompts.append(
                    {"role": "function", "parts": [{"text": prompt["content"]}]}
                )
        return modified_prompts

    def _extract_system_prompt(self, prompts):
        for i, prompt in enumerate(prompts):
            if prompt["role"] == "system":
                system_prompt = prompt["content"]
                del prompts[i]
                return system_prompt
        return None

    def inference(self, prompt, functions, test_category):
        prompt = self._substitute_prompt_role(prompt)
        functions = func_doc_language_specific_pre_processing(functions, test_category)
        gemini_tool = convert_to_tool(
            functions, GORILLA_TO_OPENAPI, self.model_style, test_category
        )
        result, metadata = self._query_gemini(prompt, gemini_tool)
        return result, metadata

    def decode_ast(self, result, language="Python"):
        if type(result) is not list:
            result = [result]
        decoded_output = []
        for invoked_function in result:
            name = list(invoked_function.keys())[0]
            params = json.loads(invoked_function[name])
            decoded_output.append({name: params})
        return decoded_output

    def decode_execute(self, result):
        return convert_to_function_call(result)
