from bfcl_eval.model_handler.api_inference.openai import OpenAIHandler
from bfcl_eval.model_handler.api_inference.deepseek import DeepSeekAPIHandler
from openai import OpenAI, RateLimitError
import os
import time
import json
from bfcl_eval.model_handler.utils import (
    retry_with_backoff,
)
from bfcl_eval.constants.category_mapping import VERSION_PREFIX
from bfcl_eval.utils import load_file, make_json_serializable, sort_key
from overrides import final

class OpenaiCompatibleHandler(OpenAIHandler):
    def __init__(self, model_name, temperature) -> None:
        self.compatible_provider=model_name.split('/')[0]
        model_name = '/'.join([sec for sec in model_name.split('/')[1:]])
        super().__init__(model_name, temperature)

    def _init_client(self):
        if self.compatible_provider == "sambanova":
            base_url = "https://api.sambanova.ai/v1"
            self.client = OpenAI(base_url=base_url, api_key=os.getenv("SAMBANOVA_API_KEY"))
        elif self.compatible_provider == "groq":
            base_url = "https://api.groq.com/openai/v1"
            self.client = OpenAI(base_url=base_url, api_key=os.getenv("GROQ_API_KEY"))
        elif self.compatible_provider == "cerebras":
            base_url = "https://api.cerebras.ai/v1"
            self.client = OpenAI(base_url=base_url, api_key=os.getenv("CEREBRAS_API_KEY"))
        elif self.compatible_provider == "fireworks":
            base_url = "https://api.fireworks.ai/inference/v1"
            self.client = OpenAI(base_url=base_url, api_key=os.getenv("FIREWORKS_API_KEY"))
        elif self.compatible_provider == "together":
            base_url = "https://api.together.xyz/v1"
            self.client = OpenAI(base_url=base_url, api_key=os.getenv("TOGETHER_API_KEY"))
        else:
            raise(Exception(f"{self.compatible_provider} not implemented"))

    @retry_with_backoff(error_type=RateLimitError)
    def generate_with_backoff(self, **kwargs):
        max_retries = 10
        retry_count = 0
        start_time = time.time()
        while retry_count < max_retries:
            try:
                api_response = self.client.chat.completions.create(**kwargs)
                # If there's no error, break out of the loop
                if not (hasattr(api_response, 'error') and api_response.error):
                    break
            except Exception as e:
                print(f"Error occurred: {str(e)}")

            # Calculate exponential backoff (base 2)
            sleep_time = min(2 ** retry_count, 60)  # Cap at 60 seconds to avoid too long waits
            print(f"Attempt {retry_count + 1} failed. Sleeping for {sleep_time} seconds...")
            time.sleep(sleep_time)
            retry_count += 1

        end_time = time.time()
        return api_response, end_time - start_time

    @final
    def write(self, result, result_dir, update_mode=False):
        model_name_dir = self.model_name.replace("/", "_")
        model_result_dir = result_dir / f"{self.compatible_provider}_{model_name_dir}"
        model_result_dir.mkdir(parents=True, exist_ok=True)

        if isinstance(result, dict):
            result = [result]

        # Collect and format each entry for JSON compatibility
        entries_to_write = [make_json_serializable(entry) for entry in result]

        # Group entries by their `test_category` for efficient file handling
        file_entries = {}
        for entry in entries_to_write:
            test_category = entry["id"].rsplit("_", 1)[0]
            file_name = f"{VERSION_PREFIX}_{test_category}_result.json"
            file_path = model_result_dir / file_name
            file_entries.setdefault(file_path, []).append(entry)

        for file_path, entries in file_entries.items():
            if update_mode:
                # Load existing entries from the file
                existing_entries = {}
                if file_path.exists():
                    existing_entries = {
                        entry["id"]: entry for entry in load_file(file_path)
                    }

                # Update existing entries with new data
                for entry in entries:
                    existing_entries[entry["id"]] = entry

                # Sort entries by `id` and write them back to ensure order consistency
                sorted_entries = sorted(existing_entries.values(), key=sort_key)
                with open(file_path, "w") as f:
                    for entry in sorted_entries:
                        f.write(json.dumps(entry) + "\n")

            else:
                # Normal mode: Append in sorted order
                entries.sort(key=sort_key)
                with open(file_path, "a") as f:
                    for entry in entries:
                        f.write(json.dumps(entry) + "\n")