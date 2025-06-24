import argparse
import json
import os
import random
from pathlib import Path

DEFAULT_SEED = 42
CURRENT_DIR = Path(__file__).resolve().parent
DATA_DIR = CURRENT_DIR / "bfcl_eval" / "data"
BACKUP_DIR = CURRENT_DIR / "bfcl_eval" / "original_data"


def load_jsonl(path):
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def save_jsonl(path, data):
    with open(path, "w", encoding="utf-8") as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def backup_original(file_path, backup_dir):
    backup_path = backup_dir / file_path.relative_to(DATA_DIR)
    if not backup_path.exists():
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        backup_path.write_text(file_path.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"  Backup created: {backup_path}")
    else:
        print(f"  Backup already exists: {backup_path}")


def generate_subset(dataset_name, subset_size, seed):
    question_path = DATA_DIR / f"{dataset_name}.json"
    answer_path = DATA_DIR / "possible_answer" / f"{dataset_name}.json"
    backup_dir = BACKUP_DIR

    if not question_path.exists():
        raise FileNotFoundError(f"Question file not found: {question_path}")
    if not answer_path.exists():
        raise FileNotFoundError(f"Answer file not found: {answer_path}")

    # Backup original files if not already backed up
    backup_original(question_path, backup_dir)
    backup_original(answer_path, backup_dir)

    source_question_path = backup_dir / question_path.relative_to(DATA_DIR)
    source_answer_path = backup_dir / answer_path.relative_to(DATA_DIR)

    print(f"\nProcessing dataset: {dataset_name}")

    questions = load_jsonl(source_question_path)
    answers = load_jsonl(source_answer_path)

    if len(questions) != len(answers):
        raise ValueError(
            f"Mismatched lengths: {len(questions)} questions vs {len(answers)} answers"
        )

    if subset_size > len(questions):
        raise ValueError(
            f"Subset size {subset_size} is larger than dataset size {len(questions)}"
        )

    random.seed(seed)
    indices = sorted(random.sample(range(len(questions)), subset_size))

    subset_questions = [questions[i] for i in indices]
    subset_answers = [answers[i] for i in indices]

    save_jsonl(question_path, subset_questions)
    save_jsonl(answer_path, subset_answers)

    # Save the indices used for this subset
    index_log_path = question_path.with_name(question_path.stem + "_indices.txt")
    with open(index_log_path, "w", encoding="utf-8") as f:
        for idx in indices:
            f.write(f"{idx}\n")

    print(f"  Selected indices: {indices}")
    print(f"  Subset saved to: {question_path} and {answer_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate aligned subsets of datasets."
    )
    parser.add_argument(
        "datasets", nargs="+", help="Dataset names without .json extension"
    )
    parser.add_argument("-n", "--num", type=int, required=True, help="Subset size")
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help=f"Random seed (default: {DEFAULT_SEED})",
    )

    args = parser.parse_args()

    for dataset_name in args.datasets:
        try:
            generate_subset(dataset_name, args.num, args.seed)
        except Exception as e:
            print(f"  Error processing {dataset_name}: {e}")


if __name__ == "__main__":
    main()
    # sample usage: `python generate_subsets.py BFCL_v3_simple BFCL_v3_live_simple BFCL_v3_multi_turn_base BFCL_v3_multiple BFCL_v3_live_multiple BFCL_v3_parallel_multiple BFCL_v3_live_parallel_multiple BFCL_v3_multi_turn_long_context -n 3`
