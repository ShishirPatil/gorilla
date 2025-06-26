import os
import json
import csv
import argparse
from typing import List, Dict

SCORE_DIR = './score'
OUTPUT_CSV = 'error_report.csv'


def get_provider_dirs(base_dir: str) -> List[str]:
    return [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]


def get_model_dirs(provider_path: str, target_id: str) -> List[str]:
    target_path = os.path.join(provider_path, target_id)
    if not os.path.isdir(target_path):
        return []
    return [
        os.path.join(target_path, model)
        for model in os.listdir(target_path)
        if os.path.isdir(os.path.join(target_path, model))
    ]


def process_json_file(file_path: str, provider: str, test_file: str, model: str, target_id: str) -> List[Dict]:
    rows = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                if not line.strip():
                    continue
                try:
                    content = json.loads(line)
                except json.JSONDecodeError:
                    print(f"JSON decode error in {file_path} on line {line_num}")
                    continue

                error = content.get("error")
                error_type = content.get("error_type") or content.get("sub_error_type")
                if error is None and error_type is None:
                    continue

                rows.append({
                    "id": f"{target_id}-{model}",
                    "id_test": content.get("id"),
                    "provider": provider,
                    "test": test_file,
                    "model": content.get("model_name", model),
                    "error": "; ".join(error) if isinstance(error, list) else str(error),
                    "error_type": error_type
                })
    except Exception as e:
        print(f"Failed to process {file_path}: {e}")
    return rows


def collect_error_data(score_dir: str, target_id: str) -> List[Dict]:
    all_rows = []
    for provider in get_provider_dirs(score_dir):
        provider_path = os.path.join(score_dir, provider)
        model_dirs = get_model_dirs(provider_path, target_id)

        for model_dir in model_dirs:
            model_name = os.path.basename(model_dir)
            for file in os.listdir(model_dir):
                if file.endswith('.json') and 'multi_turn' not in file:
                    file_path = os.path.join(model_dir, file)
                    all_rows.extend(process_json_file(file_path, provider, file, model_name, target_id))
    return all_rows


def write_csv(data: List[Dict], output_path: str):
    with open(output_path, mode='w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(
            csvfile,
            fieldnames=["id", "id_test", "provider", "test", "model", "error", "error_type"],
            delimiter=';'
        )
        writer.writeheader()
        writer.writerows(data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate error report from score directory")
    parser.add_argument(
        "--target_id",
        type=str,
        default="2025-06-19-23-36-51",
        help="Target ID to use for locating model scores"
    )

    args = parser.parse_args()
    rows = collect_error_data(SCORE_DIR, args.target_id)
    write_csv(rows, OUTPUT_CSV)
    print(f"Report saved to {OUTPUT_CSV}")
