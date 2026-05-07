import json
import tempfile
import unittest
from pathlib import Path

from check_apibench_eval_data import build_report, normalize_question_text


class APIBenchEvalDataCheckTest(unittest.TestCase):
    def test_normalizes_literal_newlines_and_context_suffix(self):
        text = " What is an API?\\n \n Use this API documentation: noisy context"

        self.assertEqual(normalize_question_text(text), "What is an API?")

    def test_reports_matching_fixture_as_ok(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "data/apibench/huggingface_eval.json"
            questions = (
                root
                / "gorilla/eval/eval-data/questions/huggingface"
                / "questions_huggingface_0_shot.jsonl"
            )
            source.parent.mkdir(parents=True)
            questions.parent.mkdir(parents=True)
            source.write_text(
                json.dumps(
                    {
                        "code": (
                            "###Instruction: Find a model for sentence similarity.\n"
                            "###Output: <<<api_call>>>: model()"
                        )
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            questions.write_text(
                json.dumps(
                    {
                        "question_id": 1,
                        "text": " Find a model for sentence similarity.\\n",
                        "category": "generic",
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            report = build_report(root, ["huggingface"])

        self.assertEqual(len(report), 1)
        self.assertTrue(report[0].ok)

    def test_reports_missing_and_mismatch(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "data/apibench/huggingface_eval.json"
            questions = (
                root
                / "gorilla/eval/eval-data/questions/huggingface"
                / "questions_huggingface_0_shot.jsonl"
            )
            source.parent.mkdir(parents=True)
            questions.parent.mkdir(parents=True)
            source.write_text(
                json.dumps(
                    {
                        "code": (
                            "###Instruction: Expected question.\n"
                            "###Output: <<<api_call>>>: model()"
                        )
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            questions.write_text(
                json.dumps(
                    {
                        "question_id": 1,
                        "text": "Different question.",
                        "category": "generic",
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            report = build_report(root, ["huggingface"])[0]

        self.assertFalse(report.ok)
        self.assertEqual(report.missing_count, 1)
        self.assertEqual(report.extra_count, 1)
        self.assertEqual(report.mismatched_count, 1)


if __name__ == "__main__":
    unittest.main()
