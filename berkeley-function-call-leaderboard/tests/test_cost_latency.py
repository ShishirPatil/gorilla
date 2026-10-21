import unittest

from bfcl_eval.constants.model_config import MODEL_CONFIG_MAPPING
from bfcl_eval.eval_checker.eval_runner_helper import (
    get_cost_latency_info,
    record_cost_latency,
)

API_MODEL = "gpt-4o-2024-11-20-FC"
LOCAL_MODEL = "meta-llama/Llama-3.1-8B-Instruct-FC"


class CostLatencyTests(unittest.TestCase):
    def test_latency_statistics(self):
        cases = [
            ([], ("N/A", "N/A", "N/A")),
            ([1.5], (1.5, "N/A", 1.5)),
            ([1.0, 3.0], (2.0, 1.41, 2.9)),
            ([1.0, 2.0, 3.0], (2.0, 1.0, 2.9)),
            ([1.5, 1.5], (1.5, 0.0, 1.5)),
        ]
        config = MODEL_CONFIG_MAPPING[API_MODEL]
        api_cost = round(config.input_price + config.output_price / 10, 2)
        for model in (API_MODEL, LOCAL_MODEL):
            for latencies, expected in cases:
                with self.subTest(model=model, latencies=latencies):
                    cost_data = {"input_data": [1_000_000], "output_data": [100_000]}
                    cost = api_cost
                    if model == LOCAL_MODEL:
                        cost = 0.0 if latencies else "N/A"
                    self.assertEqual(
                        get_cost_latency_info(model, cost_data, {"data": latencies}),
                        (cost, *expected),
                    )

    def test_single_latency_without_token_counts(self):
        self.assertEqual(
            get_cost_latency_info(
                API_MODEL, {"input_data": [], "output_data": []}, {"data": [1.5]}
            ),
            ("N/A", 1.5, "N/A", 1.5),
        )

    def test_collected_latency_statistics(self):
        cases = [
            ([{"latency": 1.5}], [1.5], (1.5, "N/A", 1.5)),
            ([{"latency": [[1.0], [3.0]]}], [1.0, 3.0], (2.0, 1.41, 2.9)),
            (
                [{"latency": 0}, {}, {"latency": "N/A"}, {"latency": 1.5}],
                [1.5],
                (1.5, "N/A", 1.5),
            ),
        ]
        for records, latencies, expected in cases:
            with self.subTest(records=records):
                table = {}
                record_cost_latency(table, API_MODEL, records)
                self.assertEqual(table[API_MODEL]["latency"]["data"], latencies)
                self.assertEqual(
                    get_cost_latency_info(
                        API_MODEL, table[API_MODEL]["cost"], table[API_MODEL]["latency"]
                    )[1:],
                    expected,
                )


if __name__ == "__main__":
    unittest.main()
