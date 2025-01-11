import os
from bfcl._llm_response_generation import parse_test_category_argument
from bfcl.constant import PROMPT_PATH
from bfcl.utils import is_java, is_js, load_file
import json
from pathlib import Path
from mappings import TYPE_MAP
from copy import deepcopy

"""
Script for resolving error type 37:
    - The default value {repr(param_details['default'])} for the parameter '{param_name}' is not of type {param_details['type']}. Expected {TYPE_MAP[param_details['type']]}, got {type(param_details['default'])}.
The rules for fixing this error are:
1. If the default value is 'dontcare' or 'optional', set the default value to None.
2. If the actual type is a string
   - If the expected type is a boolean and the string is 'false'/'true', set the default value to False/True.
   - If the expected type is a list, set the default value to [default_value].
   - Else, set the default value to eval(default_value).
3. If the actual type is an integer, but the expected type is a float, set the default value to float(default_value).
"""

def get_test_entries_require_fix():
    test_entries_require_fix = {}
    with open('../log/error_type_37_entries.txt', 'r') as file:
        for line in file:
            test_id, _, enum_value, param_type, expected_type, got_type = line.strip().split(',/ ')
            expected_type = expected_type.split("'")[1]
            got_type = got_type.split("'")[1]
            test_entries_require_fix[test_id] = enum_value, param_type, expected_type, got_type
    return test_entries_require_fix
  
def resolve_error(test_entry):
    modified_test_entry = deepcopy(test_entry)
    for function in modified_test_entry['function']:
        for property_value in function['parameters']['properties'].values():
            if "default" in property_value.keys():
                expected_type, actual_type = TYPE_MAP[property_value['type']], type(property_value['default'])
                if (
                    property_value["type"] != "any"
                    and property_value["default"] is not None
                    and type(property_value["default"]) != TYPE_MAP[property_value["type"]]
                ):
                    try:
                        default_value = property_value['default']
                        if default_value in ('dontcare', 'optional'):
                            property_value['default'] = None
                        elif actual_type == str:
                            if default_value == 'false':
                                property_value['default'] = False
                            elif default_value == 'true':
                                property_value['default'] = True
                            elif expected_type == list:
                                property_value['default'] = [default_value]
                            else:
                                property_value['default'] = eval(default_value)
                        elif expected_type == float and actual_type == int:
                            property_value['default'] = float(default_value)
                    except:
                        print(f"Error!! Test id: {test_entry['id']} --- {property_value['default']}")
    return modified_test_entry
  
test_entries_require_fix = get_test_entries_require_fix()
test_categories_total, test_filename_total = parse_test_category_argument(["single_turn"])
for test_category, file_path in zip(test_categories_total, test_filename_total):
    if is_java(test_category) or is_js(test_category):
        continue
    file_path = "BFCL_v3_" + file_path + ".json"
    dataset_data = load_file(PROMPT_PATH / file_path)
    cleaned = []
    for test_entry in dataset_data:
        test_entry = resolve_error(test_entry)
        cleaned.append(test_entry)
    if os.path.exists(PROMPT_PATH / file_path):
        os.remove(PROMPT_PATH / file_path)
    for cleaned_entry in cleaned:
        with open(PROMPT_PATH / file_path, 'a') as f:
            try:
                json.dump(cleaned_entry, f)
                f.write('\n')
            except Exception as e:
                print(f"Error!! File path: {PROMPT_PATH / file_path} --- {cleaned_entry['id']} --- {e}")
                print(cleaned_entry)
