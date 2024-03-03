import ast
import os 
import argparse
from tqdm import tqdm
"""
    This script is used to check the correctness of the outputs of the models for the given test categories.
    The input:
        --model: The model name. It is used to specify the model that will be used for the tests.
        --test_category: The test category. It is used to specify the test category that will be used for the tests.
    The output:
        The script will output the correctness of the outputs of the models for the given test categories.
    
    For example:
        `python3 openfunctions_checker.py --model gorilla-openfunctions-v2 --test_category ast` will check the correctness of the outputs of the model gorilla-openfunctions-v2 for the ast test category.
        `python3 openfunctions_checker.py --model gorilla-openfunctions-v2 --test_category executable` will check the correctness of the outputs of the model gorilla-openfunctions-v2 for the executable test category.
        `python3 openfunctions_checker.py --model gorilla-openfunctions-v2 --test_category all` will check the correctness of the outputs of the model gorilla-openfunctions-v2 for all the test categories.
    Here is a possible list of test categories:
        - simple
        - executable_simple
        - executable_parallel_function
        - parallel_function
        - multiple_function
        - parallel_multiple_function
        - executable_multiple_function
        - executable_parallel_multiple_function
        - chatable
        - relevance
        - sql
        - java
        - javascript
        - all
        - executable
        - ast
"""
def get_args():
    parser = argparse.ArgumentParser()
    # Refer to model_choice for supported models.
    parser.add_argument("--model", type=str, default="gpt-4-0125-preview")
    # Refer to test_categories for supported categories.
    parser.add_argument("--test_category", type=str, default="ast")

    # If file name, that means we are testing it. It has the highest priority.
    parser.add_argument("--file_name", type=str, default=None)
    # Whether the run will be used for output analysis. 
    parser.add_argument("--output_analysis", action="store_true", default=False)
    #Store the log whether each eval data is correct or not
    parser.add_argument("--log_store", action="store_true", default=False)

    args = parser.parse_args()
    return args
args = get_args() 

# If the test category is all, we will check all the tests categories.
if args.test_category == "all":
    test_categories = ["simple", 
                       "executable_simple", 
                       "executable_parallel_function", 
                       "parallel_function",
                       "multiple_function",
                       "parallel_multiple_function",
                       "executable_multiple_function"
                       "executable_parallel_multiple_function",
                       "chatable",
                       "relevance",
                       "sql",
                       "java",
                       "javascript",
                       ]

# If the test category is executable, we will check all the executable tests categories.    
elif args.test_category == "executable":
    test_categories = ["executable_simple", 
                       "executable_parallel_function", 
                       "executable_multiple_function",
                       "executable_parallel_multiple_function",
                       "rest"]
    
# If the test category is ast, we will check all the ast tests categories.
elif args.test_category == "ast":
    test_categories = ["simple", 
                       "parallel_function",
                       "multiple_function",
                       "parallel_multiple_function",
                       "chatable",
                       "relevance",
                       "sql",
                       "java",
                       "javascript",]
else:
    # If the test category is not all, executable, or ast, we will check the specific test category.
    test_categories = [args.test_category]

for test_category in test_categories:
    append_string = ""
    if args.output_analysis:
        append_string += " --output_analysis"
    if args.log_store:
        append_string += " --log_store"
    if "executable" in test_category or "rest" in test_category:
        # If the test category is executable, we will use openfunctions_executable_checker.py.
        print(f"Executable test category: {test_category} in progress...🦍")
        if args.file_name is not None:
            os.system(f"python openfunctions_executable_checker.py --model {args.model} --test_category {test_category} --input_file {args.file_name}" + append_string)
        else:
            os.system(f"python openfunctions_executable_checker.py --model {args.model} --test_category {test_category}" + append_string)
    else:
        # If the test category is ast, we will use openfunctions_ast_checker.py.
        if args.file_name:
            os.system(f"python openfunctions_ast_checker.py --model {args.model} --test_category {test_category} --file_name {args.file_name}" + append_string)
        else:
            os.system(f"python openfunctions_ast_checker.py --model {args.model} --test_category {test_category}" + append_string)