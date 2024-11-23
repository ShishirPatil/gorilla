from keyword import kwlist

from bfcl._llm_response_generation import (
    parse_test_category_argument,
    process_multi_turn_test_case,
)
from bfcl.constant import PROMPT_PATH
from bfcl.utils import load_file, is_java, is_js

"""
This script checks for illegal function parameter names in Python.
Credit to Pan Yinxu (@Cppowboy) for the original idea and implementation
"""

def rename_tool(tool, model_name):
    properties = {}
    for key, value in tool["parameters"]["properties"].items():
        if key in kwlist:
            properties["_" + key] = value
        else:
            properties[key] = value
    tool["parameters"]["properties"] = properties
    return tool


test_categories_total, test_filename_total = parse_test_category_argument(["all"])

for test_category, file_path in zip(test_categories_total, test_filename_total):
    # We only care about Python test cases; Java and JavaScript test cases have different rules
    if is_java(test_category) or is_js(test_category):
        continue
    dataset_data = load_file(PROMPT_PATH / file_path)
    dataset_data = process_multi_turn_test_case(
        dataset_data, test_category
    )
    for test_entry in dataset_data:
        for function in test_entry["function"]:
            if "parameters" in function and "properties" in function["parameters"]:
                for param_name, param_description in function["parameters"]["properties"].items():
                    if param_name in kwlist:
                        print("--------------------")
                        print(f"Illegal parameter name: {param_name}")
                        print(f"Entry ID: {test_entry['id']}")
                        print(f"Function: {function['name']}")
