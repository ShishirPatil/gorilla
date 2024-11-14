import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import requests
from bfcl.model_handler.base_handler import BaseHandler
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
        self.model_name_huggingface = model_name
        self.model_style = ModelStyle.OSSMODEL
        self.dtype = dtype
        self.client = OpenAI(base_url=f"http://localhost:{VLLM_PORT}/v1", api_key="EMPTY")

    def inference(self, test_entry: dict, include_input_log: bool, include_state_log: bool):
        """
        OSS models have a different inference method.
        They needs to spin up a server first and then send requests to it.
        It is more efficient to spin up the server once for the whole batch, instead of for each individual entry.
        So we implement batch_inference method instead.
        """
        raise NotImplementedError(
            "OSS Models should call the batch_inference method instead."
        )

    def decode_ast(self, result, language="Python"):
        return default_decode_ast_prompting(result, language)

    def decode_execute(self, result):
        return default_decode_execute_prompting(result)

    def batch_inference(
        self,
        test_entries: list[dict],
        num_gpus: int,
        gpu_memory_utilization: float,
        backend: str,
        include_input_log: bool,
        include_state_log: bool,
    ):
        """
        Batch inference for OSS models.
        """
        from transformers import AutoConfig, AutoTokenizer

        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name_huggingface)

        config = AutoConfig.from_pretrained(self.model_name_huggingface)
        if hasattr(config, "max_position_embeddings"):
            self.max_context_length = config.max_position_embeddings
        elif self.tokenizer.model_max_length is not None:
            self.max_context_length = self.tokenizer.model_max_length
        else:
            if not hasattr(self, "max_context_length"):
                raise ValueError(
                    "Model does not have a max_position_embeddings attribute or tokenizer.model_max_length attribute. Please set the max_context_length attribute in the corresponding model handler."
                )
        print(f"Max context length: {self.max_context_length}")

        if backend == "vllm":
            process = subprocess.Popen(
                [
                    "vllm",
                    "serve",
                    str(self.model_name_huggingface),
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
        elif backend == "sglang":
            # Check if the flashinfer package is installed to determine the backend
            try:
                import flashinfer
                backend_choice = "flashinfer"
            except ImportError as e:
                backend_choice = "triton"
                pass

            process = subprocess.Popen(
                [
                    "python",
                    "-m",
                    "sglang.launch_server",
                    "--model-path",
                    str(self.model_name_huggingface),
                    "--port",
                    str(VLLM_PORT),
                    "--dtype",
                    str(self.dtype),
                    "--tp",
                    str(num_gpus),
                    "--mem-fraction-static",
                    str(gpu_memory_utilization),
                    "--attention-backend",
                    str(backend_choice),
                    "--trust-remote-code",
                ],
                stdout=subprocess.PIPE,  # Capture stdout
                stderr=subprocess.PIPE,  # Capture stderr
                text=True,  # To get the output as text instead of bytes
            )
        else:
            raise ValueError(f"Backend {backend} is not supported.")

        stop_event = (
            threading.Event()
        )  # Event to signal threads to stop; no need to see logs after server is ready

        def log_subprocess_output(pipe, stop_event):
            # Read lines until stop event is set
            for line in iter(pipe.readline, ""):
                if stop_event.is_set():
                    break
                else:
                    print(line, end="")
            pipe.close()
            print("server log tracking thread stopped successfully.")

        # Start threads to read and print stdout and stderr
        stdout_thread = threading.Thread(
            target=log_subprocess_output, args=(process.stdout, stop_event)
        )
        stderr_thread = threading.Thread(
            target=log_subprocess_output, args=(process.stderr, stop_event)
        )
        stdout_thread.start()
        stderr_thread.start()

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
                        print("server is ready!")
                except requests.exceptions.ConnectionError:
                    # If the connection is not ready, wait and try again
                    time.sleep(1)

            # Signal threads to stop reading output
            stop_event.set()

            # Once the server is ready, make the completion requests
            futures = []
            with ThreadPoolExecutor(max_workers=100) as executor:
                with tqdm(
                    total=len(test_entries),
                    desc=f"Generating results for {self.model_name}",
                ) as pbar:

                    for test_case in test_entries:
                        future = executor.submit(self._multi_threaded_inference, test_case, include_input_log, include_state_log)
                        futures.append(future)

                    for future in futures:
                        # This will wait for the task to complete, so that we are always writing in order
                        result = future.result()
                        self.write(result)
                        pbar.update()


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

            # Wait for the output threads to finish
            stop_event.set()
            stdout_thread.join()
            stderr_thread.join()
            
    def _multi_threaded_inference(self, test_case, include_input_log: bool, include_state_log: bool):
        """
        This is a wrapper function to make sure that, if an error occurs during inference, the process does not stop.
        """
        assert type(test_case["function"]) is list

        try:
            if "multi_turn" in test_case["id"]:
                model_responses, metadata = self.inference_multi_turn_prompting(test_case, include_input_log, include_state_log)
            else:
                model_responses, metadata = self.inference_single_turn_prompting(test_case, include_input_log)
        except Exception as e:
            print("-" * 100)
            print(
                "❗️❗️ Error occurred during inference. Maximum reties reached for rate limit or other error. Continuing to next test case."
            )
            print(f"❗️❗️ Test case ID: {test_case['id']}, Error: {str(e)}")
            print("-" * 100)

            model_responses = f"Error during inference: {str(e)}"
            metadata = {}

        result_to_write = {
            "id": test_case["id"],
            "result": model_responses,
        }
        result_to_write.update(metadata)

        return result_to_write

    #### Prompting methods ####

    def _format_prompt(self, messages, function):
        raise NotImplementedError(
            "OSS Models should implement their own prompt formatting."
        )

    def _query_prompting(self, inference_data: dict):
        # We use the OpenAI Completions API
        function: list[dict] = inference_data["function"]
        message: list[dict] = inference_data["message"]

        formatted_prompt: str = self._format_prompt(message, function)
        inference_data["inference_input_log"] = {"formatted_prompt": formatted_prompt}

        # Tokenize the formatted prompt to get token count
        input_token_count = len(self.tokenizer.tokenize(formatted_prompt))

        # Determine the number of tokens to request. Cap it at 4096 if the model has a larger limit.
        if self.max_context_length < input_token_count + 2:
            # If the prompt is already at the max length, just request 1000 token, we will get an error anyway
            leftover_tokens_count = 1000
        else:
            leftover_tokens_count = min(4096, self.max_context_length - input_token_count - 2)

        if hasattr(self, "stop_token_ids"):
            api_response = self.client.completions.create(
                model=self.model_name_huggingface,
                temperature=self.temperature,
                prompt=formatted_prompt,
                max_tokens=leftover_tokens_count,
                extra_body={"stop_token_ids": self.stop_token_ids},
            )
        else:
            api_response = self.client.completions.create(
                model=self.model_name_huggingface,
                temperature=self.temperature,
                prompt=formatted_prompt,
                max_tokens=leftover_tokens_count,
            )

        return api_response

    def _pre_query_processing_prompting(self, test_entry: dict) -> dict:
        functions: list = test_entry["function"]
        test_category: str = test_entry["id"].rsplit("_", 1)[0]

        functions = func_doc_language_specific_pre_processing(functions, test_category)

        test_entry["question"][0] = system_prompt_pre_processing_chat_model(
            test_entry["question"][0], functions, test_category
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
