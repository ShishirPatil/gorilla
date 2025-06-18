import subprocess
import concurrent.futures
import uuid
from datetime import datetime
import json
import time
import csv
import os
from threading import Lock


CSV_HEADERS = [
    "run_id",
    "test_suite_name",
    "provider",
    "n_samples",
    "date",
    "Meta-Llama-3.1-405B-Instruct",
    "Meta-Llama-3.3-70B-Instruct",
    "Llama-4-Scout-17B-16E-Instruct",
    "Llama-4-Maverick-17B-128E-Instruct",
    "Qwen3-32B"
]

with open('scores.csv', 'w', newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=CSV_HEADERS, delimiter=';')
    writer.writeheader()

def load_json(file_path):
    with open(file_path, "r") as f:
        return json.load(f)

def run_bfcl_command(command_type, model, test_category, result_dir, score_dir=None):
    if command_type not in ["generate", "evaluate"]:
        raise ValueError("Invalid command_type. Must be 'generate' or 'evaluate'.")

    command = [
        "bfcl", command_type,
        "--model", model,
        "--test-category", test_category,
        "--result-dir", result_dir
    ]

    if command_type == "evaluate" and score_dir:
        command += ["--score-dir", score_dir]

    try:
        print(f"\nRunning command: {' '.join(command)}")
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print("Output:", result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
    except subprocess.CalledProcessError as e:
        print(f"FAILED [{model}] - Return code: {e.returncode}")
        print("Error output:", e.stderr)

def run_models_for_provider(provider, models, run_id, test_category, model_map, lock, date):

    for model in models:
        result_path = os.path.join("result", provider, date)
        score_path = os.path.join("score", provider, date)

        run_bfcl_command("generate", model, ",".join(test_category), result_path)
        run_bfcl_command("evaluate", model, ",".join(test_category), result_path, score_dir=score_path)

    for category in test_category:
        curr_dict = {
            "run_id": run_id,
            "test_suite_name": f"Berkeley AI Benchmarking - {category}",
            "provider": provider,
            "date": date
        }

        for model in models:
            model_safe = model.replace("/", "_")
            score_path = os.path.join("score", provider, date, model_safe, f"BFCL_v3_{category}_score.json")

            try:
                with open(score_path, "r") as f:
                    first_line = f.readline()
                    data = json.loads(first_line)
                    curr_dict["n_samples"] = data.get("total_count")
                    curr_dict[model_map[model_safe]] = data.get("accuracy")
            except FileNotFoundError:
                print(f"Score file not found: {score_path}")
            except json.JSONDecodeError:
                print(f"Invalid JSON in file: {score_path}")
            except Exception as e:
                print(f"Error reading score for {provider}/{model}: {e}")

        with lock:
            with open('scores.csv', 'a', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=CSV_HEADERS, delimiter=';', extrasaction='ignore')
                if os.stat('scores.csv').st_size == 0:
                    writer.writeheader()
                writer.writerow(curr_dict)

def main(date: str):
    json_path = "provider_models.json"
    providers = load_json(json_path)
    mapping_path = "model_map.json"
    model_map = load_json(mapping_path)
    test_category = ["simple", "multiple", "live_parallel", "multi_turn_base", "parallel_multiple", "multi_turn_long_context"]
    run_id = str(uuid.uuid4())
    lock = Lock()

    subset_command = ["python", "generate_subsets.py", "BFCL_v3_simple", "BFCL_v3_live_simple", "BFCL_v3_multi_turn_base", "BFCL_v3_multiple", "BFCL_v3_live_multiple", "BFCL_v3_parallel_multiple", "BFCL_v3_live_parallel_multiple", "BFCL_v3_multi_turn_long_context", "-n", "5"]

    try:
        print(f"\nRunning subset generation: {' '.join(subset_command)}")
        result = subprocess.run(subset_command, check=True, capture_output=True, text=True)
        print("Subset Output:", result.stdout)
        if result.stderr:
            print("Subset Errors:", result.stderr)
    except subprocess.CalledProcessError as e:
        print("Subset Error output:", e.stderr)
        return

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(run_models_for_provider, provider, models, run_id, test_category, model_map, lock, date)
            for provider, models in providers.items()
        ]
        concurrent.futures.wait(futures)

if __name__ == "__main__":
    start_time = time.time()
    date = datetime.now().strftime("%d-%m-%Y-%H-%M-%S")
    main(date)
    end_time = time.time()
    execution_time = end_time - start_time
    print(f"Execution time: {execution_time:.6f} seconds")
