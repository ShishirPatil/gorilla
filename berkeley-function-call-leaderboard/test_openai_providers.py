import subprocess
import concurrent.futures
import uuid
from datetime import datetime
from threading import Lock
from bfcl_eval.utils import upload_to_s3
from pathlib import Path, PurePosixPath
from dotenv import load_dotenv
import json
import time
import csv
import os
from pathlib import Path
import pandas as pd

load_dotenv()

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

date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
base_dir = Path(__file__).resolve().parent
results_dir = base_dir / "results"
scores_csv_file_path = results_dir / date / 'scores.csv'
scores_csv_file_path.parent.mkdir(parents=True, exist_ok=True)
with open(scores_csv_file_path, 'w', newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=CSV_HEADERS, delimiter=';')
    writer.writeheader()

def load_json(file_path):
    with open(file_path, "r") as f:
        return json.load(f)
    
def generate_summary_tables(scores_path: str, summaries_paths):
    df = pd.read_csv(scores_path, sep=';')
    df = df.dropna(subset=["provider", "test_suite_name"], how='all')

    # Melt the wide format to long format (model columns → rows)
    df_long = df.melt(
        id_vars=["date", "test_suite_name", "provider"],
        value_vars=[col for col in df.columns if col not in ["run_id", "test_suite_name", "provider", "n_samples", "date"]],
        var_name="model",
        value_name="Accuracy"
    )
    
    for test_type in df["test_suite_name"].dropna().unique():
        test_type = test_type.split(" - ")[-1]
        filtered = df_long[df_long["test_suite_name"].str.contains(test_type, case=False)]
        # Convert Accuracy to numeric just in case
        filtered["Accuracy"] = pd.to_numeric(filtered["Accuracy"], errors='coerce')

        # Group by and average (or use first, max, etc.)
        summary = (
            filtered
            .groupby(["date", "provider", "model"], as_index=False)
            .agg({"Accuracy": "mean"})
            .sort_values(by=["provider", "model"])
        )
        
        # Save to CSV
        summary_filepath = summaries_paths / f"summary_{test_type.lower().replace(' ', '_')}.csv"
        summary.to_csv(summary_filepath, index=False, sep=";")
        print(f"Saved summary to: {summary_filepath}")
        upload_to_s3(scores_csv_file_path, f"fc-so-testing-suite/gorilla_snova/{date}/{PurePosixPath(summary_filepath).name}")

def run_bfcl_command(command_type, model, test_category, result_dir, score_dir=None):
    
    result_dir = str(result_dir)
    score_dir = str(score_dir)
    
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

def run_models_for_provider(provider, 
                            models,
                            run_id,
                            test_category,
                            model_map,
                            lock,
                            date,
                            concurrency_models: bool = True
                            ):
    
    result_path = Path("./result") / provider / date
    score_path = Path("./score") / provider / date

    def run_model(model, concurrent):
        for category in test_category:
            run_bfcl_command("generate", model, category, result_path)
            run_bfcl_command("evaluate", model, category, result_path, score_dir=score_path)
            curr_dict = {
                "run_id": run_id,
                "test_suite_name": f"Berkeley AI Benchmarking - {category}",
                "provider": provider,
                "date": date
            }
            model_safe = model.replace("/", "_")
            category_score_path = score_path / model_safe / f"BFCL_v3_{category}_score.json"
            
            try:
                with open(category_score_path, "r") as f:
                    first_line = f.readline()
                    data = json.loads(first_line)
                    curr_dict["n_samples"] = data.get("total_count")
                    curr_dict[model_map[model_safe]] = data.get("accuracy")
                print(f"inserting data: {curr_dict}")
            except FileNotFoundError:
                print(f"Score file not found: {category_score_path}")
            except json.JSONDecodeError:
                print(f"Invalid JSON in file: {category_score_path}")
            except Exception as e:
                print(f"Error reading score for {provider}/{model}: {e}")

            if concurrent:
                with lock:
                    df =  pd.read_csv(scores_csv_file_path, sep=";")
                    mask = (
                        (df["test_suite_name"] == curr_dict["test_suite_name"]) &
                        (df["provider"] == curr_dict["provider"])
                    )
                    if df[mask].empty:
                        df = pd.concat([df, pd.DataFrame([curr_dict])], ignore_index=True)
                    else:
                        for key, value in curr_dict.items():
                            df.loc[mask, key] = value
                    df.to_csv(scores_csv_file_path, index=False, sep=";")
                    upload_to_s3(scores_csv_file_path, f"fc-so-testing-suite/gorilla_snova/{date}/{PurePosixPath(scores_csv_file_path).name}")
            else:
                df =  pd.read_csv(scores_csv_file_path, sep=";")
                mask = (
                    (df["test_suite_name"] == curr_dict["test_suite_name"]) &
                    (df["provider"] == curr_dict["provider"])
                )
                if df[mask].empty:
                    df = pd.concat([df, pd.DataFrame([curr_dict])], ignore_index=True)
                else:
                    for key, value in curr_dict.items():
                        df.loc[mask, key] = value
                df.to_csv(scores_csv_file_path, index=False, sep=";")
                upload_to_s3(scores_csv_file_path, f"fc-so-testing-suite/gorilla_snova/{date}/{PurePosixPath(scores_csv_file_path).name}")
        

    if concurrency_models is True:
    # Run all models concurrently
        with concurrent.futures.ThreadPoolExecutor() as model_executor:
            model_futures = [model_executor.submit(run_model, model, concurrency_models) for model in models]
            concurrent.futures.wait(model_futures)
    else:
        for model in models:
            run_model(model, concurrency_models)

def main(date: str):
    json_path = base_dir / "provider_models.json"
    providers = load_json(json_path)
    mapping_path = base_dir / "model_map.json"
    model_map = load_json(mapping_path)
    test_category = ["simple", "multiple", "live_parallel", "multi_turn_base", "parallel_multiple", "multi_turn_long_context"]
    run_id = str(uuid.uuid4())
    lock = Lock()

    subset_command = ["python", "generate_subsets.py", "BFCL_v3_simple", "BFCL_v3_live_simple", "BFCL_v3_multi_turn_base", "BFCL_v3_multiple", "BFCL_v3_live_multiple", "BFCL_v3_parallel_multiple", "BFCL_v3_live_parallel_multiple", "BFCL_v3_multi_turn_long_context", "-n", "100"]

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
        
    generate_summary_tables(scores_csv_file_path, results_dir)


if __name__ == "__main__":
    start_time = time.time()
    main(date)
    end_time = time.time()
    execution_time = end_time - start_time
    print(f"Execution time: {execution_time:.6f} seconds")
