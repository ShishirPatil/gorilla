"""Value-preserving conversion of JSON-compatible JavaScript string literals."""

import json
from pathlib import Path
import unittest

from bfcl_eval.eval_checker.ast_eval.type_convertor.js_type_converter import (
    js_type_converter,
)
from bfcl_eval.model_handler.parser.js_parser import parse_javascript_function_call


class JavaScriptStringLiteralTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        data = Path(__file__).resolve().parents[1] / "bfcl_eval" / "data"
        cls.questions = cls.read_rows(data / "BFCL_v4_simple_javascript.json")
        cls.answers = cls.read_rows(
            data / "possible_answer" / "BFCL_v4_simple_javascript.json"
        )

    @staticmethod
    def read_rows(path):
        return {
            row["id"]: row
            for row in map(json.loads, path.read_text(encoding="utf-8").splitlines())
        }

    def convert_task_array(self, task_id, parameter, literal):
        description = self.questions[task_id]["function"][0]
        name = description["name"]
        properties = description["parameters"]["properties"]
        answers = self.answers[task_id]["ground_truth"][0][name]
        arguments = []
        for key in description["parameters"]["required"]:
            if key == parameter:
                value = literal
            elif properties[key]["type"] == "any":
                value = answers[key][0]
            else:
                value = json.dumps(answers[key][0])
            arguments.append(f"{key}={value}")
        parsed = parse_javascript_function_call(f"{name}({', '.join(arguments)})")
        converted = js_type_converter(parsed[0][name][parameter], "array", "String")
        return converted, answers[parameter]

    def test_current_status_array(self):
        actual, answers = self.convert_task_array(
            "simple_javascript_2", "status", '["completed", "failed"]'
        )
        self.assertEqual(actual, answers[0])

    def test_equivalent_status_unicode_literals(self):
        actual, answers = self.convert_task_array(
            "simple_javascript_2", "status", r'["\u0063ompleted", "\u0066ailed"]'
        )
        self.assertEqual(actual, answers[0])

    def test_current_product_array(self):
        actual, answers = self.convert_task_array(
            "simple_javascript_21", "products", '["Product A", "Product B", "Product C"]'
        )
        self.assertEqual(actual, answers[0])

    def test_equivalent_product_unicode_literals(self):
        actual, answers = self.convert_task_array(
            "simple_javascript_21",
            "products",
            r'["\u0050roduct A", "\u0050roduct B", "\u0050roduct C"]',
        )
        self.assertEqual(actual, answers[0])

    def test_wrong_status_stays_wrong(self):
        actual, answers = self.convert_task_array(
            "simple_javascript_2", "status", '["pending", "failed"]'
        )
        self.assertEqual(actual, ["pending", "failed"])
        self.assertNotIn(actual, answers)

    def test_wrong_product_stays_wrong(self):
        actual, answers = self.convert_task_array(
            "simple_javascript_21", "products", '["Other", "Product B", "Product C"]'
        )
        self.assertEqual(actual, ["Other", "Product B", "Product C"])
        self.assertNotIn(actual, answers)

    def test_array_literal_backslash_u_is_decoded_once(self):
        self.assertEqual(
            js_type_converter(r'["\\u0063ompleted"]', "array", "String"),
            [r"\u0063ompleted"],
        )

    def test_array_escaped_backslashes(self):
        self.assertEqual(
            js_type_converter(r'["C:\\temp\\file"]', "array", "String"),
            [r"C:\temp\file"],
        )

    def test_raw_unicode_array(self):
        self.assertEqual(
            js_type_converter('["café", "猫"]', "array", "String"), ["café", "猫"]
        )

    def test_unquoted_array_references_unchanged(self):
        self.assertEqual(
            js_type_converter("[first, second]", "array", "String"), ["first", "second"]
        )

    def test_single_quoted_array_fallback_unchanged(self):
        self.assertEqual(
            js_type_converter(r"['\u0041', 'plain']", "array", "String"),
            [r"\u0041", "plain"],
        )

    def test_scalar_plain_quoted_string(self):
        self.assertEqual(js_type_converter('"plain"', "String"), "plain")

    def test_scalar_unicode_literal(self):
        self.assertEqual(js_type_converter(r'"caf\u00e9"', "String"), "café")

    def test_scalar_raw_unicode(self):
        self.assertEqual(js_type_converter('"café猫"', "String"), "café猫")

    def test_scalar_literal_backslash_u_is_decoded_once(self):
        self.assertEqual(js_type_converter(r'"\\u0041"', "String"), r"\u0041")

    def test_unquoted_scalar_reference_unchanged(self):
        self.assertEqual(js_type_converter("someVariable", "String"), "someVariable")

    def test_unquoted_scalar_backslash_unchanged(self):
        self.assertEqual(js_type_converter(r"\u0041", "String"), r"\u0041")

    def test_single_quoted_scalar_fallback_unchanged(self):
        self.assertEqual(js_type_converter(r"'\u0041'", "String"), r"\u0041")

    def test_non_json_js_escape_fallback_unchanged(self):
        self.assertEqual(js_type_converter(r'"\x41"', "String"), r"\x41")


if __name__ == "__main__":
    unittest.main()
