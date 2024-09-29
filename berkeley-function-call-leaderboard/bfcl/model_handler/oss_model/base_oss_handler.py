import subprocess
import time

import requests
from bfcl.model_handler.base_handler import BaseHandler
from bfcl.model_handler.constant import DEFAULT_SYSTEM_PROMPT
from bfcl.model_handler.model_style import ModelStyle
from bfcl.model_handler.oss_model.constant import VLLM_PORT
from bfcl.model_handler.utils import (
    default_decode_ast_prompting,
    default_decode_execute_prompting,
    func_doc_language_specific_pre_processing,
    system_prompt_pre_processing_chat_model,
)
from openai import OpenAI
from tqdm import tqdm


class OSSHandler(BaseHandler):
    def __init__(self, model_name, temperature, dtype="bfloat16") -> None:
        super().__init__(model_name, temperature)
        self.model_style = ModelStyle.OSSMODEL
        self.dtype = dtype
        self.client = OpenAI(base_url=f"http://localhost:{VLLM_PORT}/v1", api_key="EMPTY")

    def inference(self, test_entry: dict, include_debugging_log: bool):
        """
        OSS models have a different inference method.
        They needs to spin up a vllm server first and then send requests to it.
        It is more efficient to spin up the server once for the whole batch, instead of for each individual entry.
        So we implement batch_inference method instead.
        """
        raise NotImplementedError(
            "OSS Models should call the batch_inference method instead."
        )

    def _format_prompt(self, messages, function):
        raise NotImplementedError(
            "OSS Models should implement their own prompt formatting."
        )

    def decode_ast(self, result, language="Python"):
        return default_decode_ast_prompting(result, language)

    def decode_execute(self, result):
        return default_decode_execute_prompting(result)

    def batch_inference(
        self, test_entries: list[dict], num_gpus: int, gpu_memory_utilization: float, include_debugging_log: bool
    ):
        """
        Batch inference for OSS models.
        """
        
        process = subprocess.Popen(
            [
                "vllm",
                "serve",
                str(self.model_name),
                "--port",
                str(VLLM_PORT),
                "--dtype",
                str(self.dtype),
                "--tensor-parallel-size",
                str(num_gpus),
                "--gpu-memory-utilization",
                str(gpu_memory_utilization),
                "--trust-remote-code",
            ],
            stdout=subprocess.PIPE,  # Capture stdout
            stderr=subprocess.PIPE,  # Capture stderr
            text=True,  # To get the output as text instead of bytes
        )

        try:
            # Wait for the server to be ready
            server_ready = False
            while not server_ready:
                # Check if the process has terminated unexpectedly
                if process.poll() is not None:
                    # Output the captured logs
                    stdout, stderr = process.communicate()
                    print(stdout)
                    print(stderr)
                    raise Exception(
                        f"Subprocess terminated unexpectedly with code {process.returncode}"
                    )
                try:
                    # Make a simple request to check if the server is up
                    response = requests.get(f"http://localhost:{VLLM_PORT}/v1/models")
                    if response.status_code == 200:
                        server_ready = True
                        print("vllm server is ready!")
                except requests.exceptions.ConnectionError:
                    # If the connection is not ready, wait and try again
                    time.sleep(1)

            # After the server is ready, stop capturing the output, otherwise the terminal looks messy
            process.stdout.close()
            process.stderr.close()
            process.stdout = subprocess.DEVNULL
            process.stderr = subprocess.DEVNULL

            # Once the server is ready, make the completion requests
            for test_entry in tqdm(test_entries, desc="Generating results"):
                try:
                    if "multi_turn" in test_entry["id"]:
                        model_responses, metadata = self.inference_multi_turn_prompting(test_entry, include_debugging_log)
                    else:
                        model_responses, metadata = self.inference_single_turn_prompting(test_entry, include_debugging_log)
                except Exception as e:
                    print(f"Error during inference for test entry {test_entry['id']}: {str(e)}")
                    model_responses = f"Error during inference: {str(e)}"
                    metadata = {}
                    
                result_to_write = {
                    "id": test_entry["id"],
                    "result": model_responses,
                }
                result_to_write.update(metadata)

                self.write(result_to_write)

        except Exception as e:
            raise e

        finally:
            # Ensure the server process is terminated properly
            process.terminate()
            try:
                # Wait for the process to terminate fully
                process.wait(timeout=15)
                print("Process terminated successfully.")
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()  # Wait again to ensure it's fully terminated
                print("Process killed.")

    #### Prompting methods ####

    def _query_prompting(self, inference_data: dict):
        # We use the OpenAI Completions API with vLLM
        function: list[dict] = inference_data["function"]
        message: list[dict] = inference_data["message"]

        formatted_prompt: str = self._format_prompt(message, function)
        inference_data["inference_input_log"] = {"formatted_prompt": formatted_prompt}

        if hasattr(self, "stop_token_ids"):
            api_response = self.client.completions.create(
                model=self.model_name,
                temperature=self.temperature,
                prompt=formatted_prompt,
                stop_token_ids=self.stop_token_ids,
                max_tokens=4096,  # TODO: Is there a better way to handle this?
            )
        else:
            api_response = self.client.completions.create(
                model=self.model_name,
                temperature=self.temperature,
                prompt=formatted_prompt,
                max_tokens=4096,
            )

        return api_response

    def _pre_query_processing_prompting(self, test_entry: dict) -> dict:
        functions: list = test_entry["function"]
        test_category: str = test_entry["id"].rsplit("_", 1)[0]

        functions = func_doc_language_specific_pre_processing(functions, test_category)

        test_entry["question"][0] = system_prompt_pre_processing_chat_model(
            test_entry["question"][0], DEFAULT_SYSTEM_PROMPT, functions
        )

        return {"message": [], "function": functions}

    def _parse_query_response_prompting(self, api_response: any) -> dict:
        return {
            "model_responses": api_response.choices[0].text,
            "input_token": api_response.usage.prompt_tokens,
            "output_token": api_response.usage.completion_tokens,
        }

    def add_first_turn_message_prompting(
        self, inference_data: dict, first_turn_message: list[dict]
    ) -> dict:
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
            {"role": "assistant", "content": model_response_data["model_responses"]}
        )
        return inference_data

    def _add_execution_results_prompting(
        self, inference_data: dict, execution_results: list[str], model_response_data: dict
    ) -> dict:
        for execution_result, decoded_model_response in zip(
            execution_results, model_response_data["model_responses_decoded"]
        ):
            inference_data["message"].append(
                {
                    "role": "tool",
                    "name": decoded_model_response,
                    "content": execution_result,
                }
            )

        return inference_data
