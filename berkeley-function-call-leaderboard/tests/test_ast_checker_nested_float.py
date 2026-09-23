"""Nested float arrays should accept ints the same way scalar floats already do."""

import unittest

from bfcl_eval.constants.enums import Language
from bfcl_eval.eval_checker.ast_eval.ast_checker import ast_checker


def _array_func(name: str, param: str, item_type: str) -> dict:
    return {
        "name": name,
        "description": "test",
        "parameters": {
            "type": "dict",
            "properties": {
                param: {
                    "type": "array",
                    "items": {"type": item_type},
                    "description": "values",
                }
            },
            "required": [param],
        },
    }


def _scalar_func(name: str, param: str) -> dict:
    return {
        "name": name,
        "description": "test",
        "parameters": {
            "type": "dict",
            "properties": {
                param: {"type": "float", "description": "value"},
            },
            "required": [param],
        },
    }


class NestedFloatCoercionTest(unittest.TestCase):
    def test_scalar_int_still_accepted_as_float(self):
        result = ast_checker(
            func_description=[_scalar_func("area", "radius")],
            model_output=[{"area": {"radius": 4}}],
            possible_answer=[{"area": {"radius": [4.0]}}],
            language=Language.PYTHON,
            test_category="simple_python",
            model_name="gorilla-openfunctions-v2",
        )
        self.assertTrue(result["valid"], result)

    def test_nested_int_list_accepted_as_float_array(self):
        result = ast_checker(
            func_description=[_array_func("sum_numbers", "numbers_list", "float")],
            model_output=[{"sum_numbers": {"numbers_list": [133, 34]}}],
            possible_answer=[{"sum_numbers": {"numbers_list": [[133.0, 34.0]]}}],
            language=Language.PYTHON,
            test_category="simple_python",
            model_name="gorilla-openfunctions-v2",
        )
        self.assertTrue(result["valid"], result)

    def test_null_in_int_array_still_fails(self):
        result = ast_checker(
            func_description=[_array_func("purchase", "pack_size", "integer")],
            model_output=[{"purchase": {"pack_size": [None, None, 12]}}],
            possible_answer=[{"purchase": {"pack_size": [[1, 1, 12]]}}],
            language=Language.PYTHON,
            test_category="simple_python",
            model_name="gorilla-openfunctions-v2",
        )
        self.assertFalse(result["valid"], result)
        self.assertIn("nested", result["error_type"])


if __name__ == "__main__":
    unittest.main()
