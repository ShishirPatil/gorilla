import sys

sys.path.append("../")

from checker import ast_checker, executable_checker, executable_checker_rest
from eval_runner_helper import *
from tqdm import tqdm
import argparse


# NOTE: This file should be run in the `eval_checker` directory


def single_executable_file_runner(
    handler, model_result, prompt, model_name, test_category
):
    assert len(model_result) == len(prompt)

    result = []
    correct_count = 0
    for i in tqdm(range(len(model_result))):
        raw_result = model_result[i]["result"]
        try:
            decoded_result = handler.decode_execute(raw_result)
        except Exception as e:
            result.append(
                {
                    "id": i + 1,
                    "valid": False,
                    "model_name": model_name,
                    "test_category": test_category,
                    "error": [f"Failed to decode executable. {str(e)}"],
                    "error_type": "executable_decoder:decoder_failed",
                    "prompt": prompt[i],
                    "model_result_raw": raw_result,
                }
            )
            continue

        if "rest" in test_category:
            # REST is always single-functioned. Therefore we take the first one and pass it to the REST checker.
            if not is_rest_format_output(decoded_result):
                result.append(
                    {
                        "id": i + 1,
                        "valid": False,
                        "model_name": model_name,
                        "test_category": test_category,
                        "error": [
                            "Did not output in the specified format. Note: the model_result is wrapped in a string to ensure json serializability."
                        ],
                        "error_type": "executable_decoder:rest_wrong_output_format",
                        "prompt": prompt[i],
                        "model_result_raw": str(raw_result),
                        "model_result_decoded": str(decoded_result),
                    }
                )
                continue

            checker_result = executable_checker_rest(decoded_result[0], i)

        else:
            if not is_executable_format_output(decoded_result):
                result.append(
                    {
                        "id": i + 1,
                        "valid": False,
                        "model_name": model_name,
                        "test_category": test_category,
                        "error": [
                            "Did not output in the specified format. Note: the model_result is wrapped in a string to ensure json serializability."
                        ],
                        "error_type": "executable_decoder:wrong_output_format",
                        "prompt": prompt[i],
                        "model_result_raw": str(raw_result),
                        "model_result_decoded": str(decoded_result),
                    }
                )
                continue

            prompt_item = prompt[i]
            checker_result = executable_checker(decoded_result, prompt_item)

        if checker_result["valid"]:
            correct_count += 1
        else:
            temp = {}
            temp["id"] = i + 1
            temp["model_name"] = model_name
            temp["test_category"] = test_category
            temp["valid"] = checker_result["valid"]
            temp["error"] = checker_result["error"]
            temp["error_type"] = checker_result["error_type"]
            temp["prompt"] = prompt[i]
            temp["model_result_raw"] = raw_result
            temp["model_result_decoded"] = decoded_result
            result.append(temp)

    accuracy = correct_count / len(model_result)
    result.insert(
        0,
        {
            "accuracy": accuracy,
            "correct_count": correct_count,
            "total_count": len(model_result),
        },
    )
    output_file_name = test_category + "_score.json"
    output_file_dir = os.path.join(OUTPUT_PATH, model_name)
    write_list_of_dicts_to_file(output_file_dir, output_file_name, result)

    return accuracy, len(model_result)


def single_relevance_file_runner(handler, model_result, model_name, test_category):

    result = []
    correct_count = 0
    for i in range(len(model_result)):
        model_result_item = model_result[i]["result"]
        success = False
        decoded_result = None

        try:
            decoded_result = handler.decode_ast(model_result_item, language="Python")
            success = False
            if is_empty_output(decoded_result):
                success = True

        except Exception as e:
            success = True

        if success:
            correct_count += 1
        else:
            temp = {}
            temp["id"] = i + 1
            temp["model_name"] = model_name
            temp["test_category"] = test_category
            temp["valid"] = success
            temp["error"] = [
                f"Valid syntax. Successfully decode AST when it should not."
            ]
            temp["error_type"] = "relevance_error:decoder_success"
            temp["model_result"] = model_result_item
            temp["decoded_result"] = decoded_result

            result.append(temp)

    accuracy = correct_count / len(model_result)
    result.insert(
        0,
        {
            "accuracy": accuracy,
            "correct_count": correct_count,
            "total_count": len(model_result),
        },
    )
    output_file_name = test_category + "_score.json"
    output_file_dir = os.path.join(OUTPUT_PATH, model_name)
    write_list_of_dicts_to_file(output_file_dir, output_file_name, result)

    return accuracy, len(model_result)


def single_ast_file_runner(
    handler, model_result, prompt, possible_answer, language, test_category, model_name
):
    assert (
        len(model_result) == len(prompt) == len(possible_answer)
    ), "The length of the model result does not match the length of the prompt or possible answer. Please check the input files for completeness."

    result = []
    correct_count = 0
    for i in range(len(model_result)):
        model_result_item = model_result[i]["result"]
        prompt_item = prompt[i]["function"]
        possible_answer_item = possible_answer[i]

        try:
            model_result_item_raw = model_result_item
            model_result_item = handler.decode_ast(model_result_item, language)
        except Exception as e:
            result.append(
                {
                    "id": i + 1,
                    "model_name": model_name,
                    "test_category": test_category,
                    "valid": False,
                    "error": [f"Invalid syntax. Failed to decode AST. {str(e)}"],
                    "error_type": "ast_decoder:decoder_failed",
                    "prompt": prompt[i],
                    "model_result_raw": model_result_item_raw,
                    "possible_answer": possible_answer_item,
                }
            )
            continue

        decoder_output_valid = is_function_calling_format_output(model_result_item)
        if not decoder_output_valid:
            result.append(
                {
                    "id": i + 1,
                    "model_name": model_name,
                    "test_category": test_category,
                    "valid": False,
                    "error": [
                        "Did not output in the specified format. Note: the model_result is wrapped in a string to ensure json serializability."
                    ],
                    "error_type": "ast_decoder:decoder_wrong_output_format",
                    "prompt": prompt[i],
                    "model_result_raw": str(model_result_item_raw),
                    "model_result_decoded": str(model_result_item),
                    "possible_answer": possible_answer_item,
                }
            )
            continue

        checker_result = ast_checker(
            prompt_item,
            model_result_item,
            possible_answer_item,
            language,
            test_category,
            model_name,
        )

        if checker_result["valid"]:
            correct_count += 1
        else:
            temp = {}
            temp["id"] = i + 1
            temp["model_name"] = model_name
            temp["test_category"] = test_category
            temp["valid"] = checker_result["valid"]
            temp["error"] = checker_result["error"]
            temp["error_type"] = checker_result["error_type"]
            temp["prompt"] = prompt[i]
            temp["model_result_raw"] = model_result_item_raw
            temp["model_result_decoded"] = model_result_item
            temp["possible_answer"] = possible_answer_item
            result.append(temp)

    accuracy = correct_count / len(model_result)
    result.insert(
        0,
        {
            "accuracy": accuracy,
            "correct_count": correct_count,
            "total_count": len(model_result),
        },
    )
    output_file_name = test_category + "_score.json"
    output_file_dir = os.path.join(OUTPUT_PATH, model_name)
    write_list_of_dicts_to_file(output_file_dir, output_file_name, result)

    return accuracy, len(model_result)


#### Main runner function ####
def runner(model_names, test_categories):
    # Get a list of all entries in the folder
    entries = os.scandir(INPUT_PATH)

    # Filter out the subdirectories
    subdirs = [entry.path for entry in entries if entry.is_dir()]

    # Traverse each subdirectory
    for subdir in subdirs:

        model_name = subdir.split(INPUT_PATH)[1]
        if model_names is not None and model_name not in model_names:
            continue

        model_name_escaped = model_name.replace("_", "/")

        files = [
            f
            for f in os.listdir(subdir)
            if os.path.isfile(os.path.join(subdir, f)) and not f.startswith(".")
        ]  
        # Check if there is only one file and that file is 'result.json'
        # If so, this is an OSS model result file and we need to special process it first
        if len(files) == 1 and files[0] == "result.json":
            result_json_file_path = os.path.join(subdir, "result.json")
            oss_file_formatter(result_json_file_path, subdir)
            print(f"Detected OSS model: {model_name}. result.json has been split into individual test category files.")

        # Pattern to match JSON files in this subdirectory
        json_files_pattern = os.path.join(subdir, "*.json")

        # Find and process all JSON files in the subdirectory
        for model_result_json in glob.glob(json_files_pattern):

            if os.path.basename(model_result_json) == "result.json":
                continue

            test_category = extract_after_test(model_result_json)
            if test_categories is not None and test_category not in test_categories:
                continue

            handler = get_handler(model_name_escaped)

            # We don't evaluate chatable and SQL models in our current leaderboard
            if is_chatable(test_category) or is_sql(test_category):
                continue

            language = "Python"
            if is_java(test_category):
                language = "Java"
            if is_js(test_category):
                language = "JavaScript"

            print("-" * 100)
            print(f"Test category: {test_category}")
            print(f"Model name: {model_name}")
            print(f"Language: {language}")
            print("-" * 100)

            model_result = load_file(model_result_json)
            record_cost_latency(LEADERBOARD_TABLE, model_name, model_result)

            if is_relevance(test_category):
                accuracy, total_count = single_relevance_file_runner(
                    handler, model_result, model_name, test_category
                )
                record_result(
                    LEADERBOARD_TABLE, model_name, test_category, accuracy, total_count
                )
                continue

            # Find the corresponding test file
            prompt_file = find_file_with_suffix(PROMPT_PATH, test_category)
            prompt = load_file(prompt_file)

            if is_executable(test_category):
                accuracy, total_count = single_executable_file_runner(
                    handler, model_result, prompt, model_name, test_category
                )
                record_result(
                    LEADERBOARD_TABLE, model_name, test_category, accuracy, total_count
                )
                continue

            # Find the corresponding possible answer file
            possible_answer_file = find_file_with_suffix(
                POSSIBLE_ANSWER_PATH, test_category
            )
            possible_answer = load_file(possible_answer_file)
            accuracy, total_count = single_ast_file_runner(
                handler,
                model_result,
                prompt,
                possible_answer,
                language,
                test_category,
                model_name,
            )
            record_result(
                LEADERBOARD_TABLE, model_name, test_category, accuracy, total_count
            )

    # This function reads all the score files from local folder and updates the leaderboard table.
    # This is helpful when you only want to run the evaluation for a subset of models and test categories.
    update_leaderboard_table_with_score_file(LEADERBOARD_TABLE, OUTPUT_PATH)
    # Write the leaderboard table to a file
    generate_leaderboard_csv(LEADERBOARD_TABLE, OUTPUT_PATH)


ARG_PARSE_MAPPING = {
    "ast": [
        "simple",
        "multiple_function",
        "parallel_function",
        "parallel_multiple_function",
        "java",
        "javascript",
        "relevance",
    ],
    "executable": [
        "executable_simple",
        "executable_multiple_function",
        "executable_parallel_function",
        "executable_parallel_multiple_function",
        "rest",
    ],
    "all": [
        "simple",
        "multiple_function",
        "parallel_function",
        "parallel_multiple_function",
        "java",
        "javascript",
        "relevance",
        "executable_simple",
        "executable_multiple_function",
        "executable_parallel_function",
        "executable_parallel_multiple_function",
        "rest",
    ],
    "non-python": [
        "java",
        "javascript",
    ],
    "python": [
        "simple",
        "multiple_function",
        "parallel_function",
        "parallel_multiple_function",
        "relevance",
        "executable_simple",
        "executable_multiple_function",
        "executable_parallel_function",
        "executable_parallel_multiple_function",
        "rest",
    ],
}


INPUT_PATH = "../result/"
PROMPT_PATH = "../data/"
POSSIBLE_ANSWER_PATH = "../data/possible_answer/"
OUTPUT_PATH = "../score/"

# A dictionary to store the results
# Key is model name, value is a dictionary with keys as test category and values as a dictionary with accuracy and total count
LEADERBOARD_TABLE = {}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process two lists of strings.")

    # Add arguments for two lists of strings
    parser.add_argument(
        "--model", nargs="+", type=str, help="A list of model names to evaluate"
    )
    parser.add_argument(
        "--test_category",
        nargs="+",
        type=str,
        help="A list of test categories to run the evaluation on",
    )

    args = parser.parse_args()

    model_names = args.model
    test_categories = None
    if args.test_category is not None:
        test_categories = []
        for test_category in args.test_category:
            if test_category in ARG_PARSE_MAPPING:
                test_categories.extend(ARG_PARSE_MAPPING[test_category])
            else:
                test_categories.append(test_category)

    runner(model_names, test_categories)
