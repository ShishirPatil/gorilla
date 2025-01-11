import os
from bfcl._llm_response_generation import parse_test_category_argument
from bfcl.constant import PROMPT_PATH
from bfcl.utils import is_java, is_js, load_file
import json
from pathlib import Path
from mappings import TYPE_MAP

"""
Script for resolving error type 36:
    - The enum value {repr(enum_value)} is not of type {param_details['type']}. Expected {TYPE_MAP[param_details['type']]}, got {type(enum_value)}.
The rules for fixing this error are:
1. If the default value is 'dontcare', set the default value to None.
2. If the actual type is a string
   - If the expected type is a boolean and the string is 'false'/'true', set the default value to False/True.
   - If the expected type is a list, set the default value to [default_value].
"""

def get_test_entries_require_fix():
    test_entries_require_fix = {}
    with open('../log/error_type_36_entries.txt', 'r') as file:
        for line in file:
            test_id, enum_value, param_type, expected_type, got_type = line.strip().split(',/ ')
            expected_type = expected_type.split("'")[1]
            got_type = got_type.split("'")[1]
            test_entries_require_fix[test_id] = enum_value, param_type, expected_type, got_type
    return test_entries_require_fix
  
def resolve_error(test_entry):
    modified_test_entry = test_entry.copy()
    for function in modified_test_entry['function']:
        for property_value in function['parameters']['properties'].values():
            if "enum" in property_value.keys():
                new_enum = []
                for enum_value in property_value['enum']:
                    if type(enum_value) != TYPE_MAP[property_value["type"]] and type(enum_value) == str:
                        try:
                            if enum_value == 'dontcare':
                                new_enum.append(None)
                            elif TYPE_MAP[property_value["type"]] == list:
                                new_enum.append([enum_value])
                            else:
                                new_enum.append(eval(enum_value))
                        except:
                            new_enum.append(enum_value)
                            print(f"Error: {enum_value}")
                    else:
                        new_enum.append(enum_value)
                property_value['enum'] = new_enum
    return modified_test_entry
  
test_entries_require_fix = get_test_entries_require_fix()
test_categories_total, test_filename_total = parse_test_category_argument(["single_turn"])
for test_category, file_path in zip(test_categories_total, test_filename_total):
    if is_java(test_category) or is_js(test_category):
        continue
    dataset_data = load_file(PROMPT_PATH / file_path)
    cleaned = []
    for test_entry in dataset_data:
        test_entry = resolve_error(test_entry)
        cleaned.append(test_entry)
  
    if os.path.exists(PROMPT_PATH / file_path):
        os.remove(PROMPT_PATH / file_path)
    for cleaned_entry in cleaned:
        with open(PROMPT_PATH / file_path, 'a') as f:
            json.dump(cleaned_entry, f)
            f.write('\n')
