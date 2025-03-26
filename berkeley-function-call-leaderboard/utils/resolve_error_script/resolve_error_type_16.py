import os
from bfcl._llm_response_generation import parse_test_category_argument
from bfcl.constant import PROMPT_PATH
from bfcl.utils import is_java, is_js, load_file
        
def search_for_param(list_of_functions, param_name):
    return_list = []
    for function in list_of_functions:
        if param_name in function['parameters']['properties'].keys():
            return_list.append(function)
    return return_list
  
def write_descriptions():
    test_entries_require_fix = {}
    with open('error_type_16_entries.txt', 'r') as file:
        for line in file:
            test_id, param = line.strip().split(', ')
            test_entries_require_fix[test_id] = param
    test_categories_total, test_filename_total = parse_test_category_argument(["single_turn"])
    for test_category, file_path in zip(test_categories_total, test_filename_total):
        if is_java(test_category) or is_js(test_category):
              continue
        dataset_data = load_file(PROMPT_PATH / file_path)
        for test_entry in dataset_data:
            if test_entry['id'] in test_entries_require_fix.keys():
                param_name = test_entries_require_fix[test_entry['id']]
                for function in search_for_param(test_entry['function'], param_name):
                    type = function['parameters']['properties'][param_name]['type']
                    description = function['parameters']['properties'][param_name]['description']
                    with open('descriptions.txt', 'a') as f:
                        f.write(f"{test_entry['id']},/{param_name},/{type},/{description}\n")

write_descriptions()
  
# def run():
#     assert os.path.exists('descriptions.txt'), "File 'descriptions.txt' does not exist."
#     test_categories_total, test_filename_total = parse_test_category_argument(["single_turn"])
#     for test_category, file_path in zip(test_categories_total, test_filename_total):
#         if is_java(test_category) or is_js(test_category):
#               continue
#         dataset_data = load_file(PROMPT_PATH / file_path)
#         for test_entry in dataset_data:
#             if test_entry['id'] in test_entries_require_fix.keys():
#                 param_name = test_entries_require_fix[test_entry['id']]
#                 for function in search_for_param(test_entry['function'], param_name):
#                     description = function['parameters']['properties'][param_name]['description']
#                     updated_description, default_value = parse_description(description)
#                     function['parameters']['properties'][param_name]['description'] = updated_description
#                     function['parameters']['properties'][param_name]['default'] = default_value

        
        

