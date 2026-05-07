"""Check APIBench eval question files against canonical APIBench data.

The APIBench eval split is stored in two review-friendly formats:

* ``data/apibench/*_eval.json`` keeps the full prompt/output records.
* ``gorilla/eval/eval-data/questions`` keeps question-only JSONL files used by
  evaluation scripts.

This checker compares the normalized instruction text in both locations so data
drift is visible before benchmark results are generated from stale questions.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


DATASET_PATHS = {
    "huggingface": {
        "source": Path("data/apibench/huggingface_eval.json"),
        "questions": Path("gorilla/eval/eval-data/questions/huggingface"),
        "prefix": "questions_huggingface",
    },
    "tensorflow": {
        "source": Path("data/apibench/tensorflow_eval.json"),
        "questions": Path("gorilla/eval/eval-data/questions/tensorflowhub"),
        "prefix": "questions_tensorflowhub",
    },
    "torchhub": {
        "source": Path("data/apibench/torchhub_eval.json"),
        "questions": Path("gorilla/eval/eval-data/questions/torchhub"),
        "prefix": "questions_torchhub",
    },
}


PROMPT_SUFFIX_RE = re.compile(r"\s+Use this API documentation.*", re.DOTALL)
WHITESPACE_RE = re.compile(r"\s+")
INSTRUCTION_RE = re.compile(
    r"###\s*Instruction:\s*(?P<instruction>.*?)(?:###\s*Output:|$)",
    re.DOTALL,
)


@dataclass
class FileReport:
    file: str
    expected_count: int
    actual_count: int
    missing_count: int
    extra_count: int
    mismatched_count: int

    @property
    def ok(self) -> bool:
        return not (self.missing_count or self.extra_count or self.mismatched_count)


def normalize_question_text(text: str) -> str:
    """Normalize formatting-only differences between APIBench question files."""
    text = text.replace("\\n", "\n")
    text = PROMPT_SUFFIX_RE.sub("", text)
    return WHITESPACE_RE.sub(" ", text).strip()


def extract_instruction(code: str) -> str:
    match = INSTRUCTION_RE.search(code)
    if not match:
        raise ValueError("APIBench record does not contain an instruction block")
    return normalize_question_text(match.group("instruction"))


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as file:
        return [json.loads(line) for line in file if line.strip()]


def read_source_questions(path: Path) -> list[str]:
    return [extract_instruction(row["code"]) for row in read_jsonl(path)]


def read_eval_questions(path: Path) -> list[str]:
    return [normalize_question_text(row["text"]) for row in read_jsonl(path)]


def compare_question_file(
    repo_root: Path, source_questions: list[str], question_file: Path
) -> FileReport:
    eval_questions = read_eval_questions(question_file)
    expected_set = set(source_questions)
    actual_set = set(eval_questions)
    pair_count = min(len(source_questions), len(eval_questions))
    mismatched_count = sum(
        1
        for index in range(pair_count)
        if source_questions[index] != eval_questions[index]
    )

    return FileReport(
        file=str(question_file.relative_to(repo_root)),
        expected_count=len(source_questions),
        actual_count=len(eval_questions),
        missing_count=len(expected_set - actual_set),
        extra_count=len(actual_set - expected_set),
        mismatched_count=mismatched_count,
    )


def build_report(repo_root: Path, datasets: list[str]) -> list[FileReport]:
    reports: list[FileReport] = []
    for dataset in datasets:
        paths = DATASET_PATHS[dataset]
        source_questions = read_source_questions(repo_root / paths["source"])
        question_dir = repo_root / paths["questions"]
        for question_file in sorted(question_dir.glob(f'{paths["prefix"]}_*.jsonl')):
            reports.append(compare_question_file(repo_root, source_questions, question_file))
    return reports


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Report APIBench eval question drift between duplicated data files."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Repository root containing data/apibench and gorilla/eval/eval-data.",
    )
    parser.add_argument(
        "--dataset",
        action="append",
        choices=sorted(DATASET_PATHS),
        help="Dataset to check. Defaults to all APIBench eval datasets.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when any checked question file has drift.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    datasets = args.dataset or sorted(DATASET_PATHS)
    reports = build_report(args.repo_root, datasets)
    payload = {
        "ok": all(report.ok for report in reports),
        "reports": [asdict(report) for report in reports],
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 1 if args.strict and not payload["ok"] else 0


if __name__ == "__main__":
    sys.exit(main())
