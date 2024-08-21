from checker import ast_checker, exec_checker, executable_checker_rest
from custom_exception import BadAPIStatusError
from eval_runner_helper import *
from eval_checker_constant import TEST_COLLECTION_MAPPING
from tqdm import tqdm
import argparse


# NOTE: This file should be run in the `eval_checker` directory


def single_executable_file_runner(
    handler, model_result, prompt, model_name, test_category
):
    assert len(model_result) == len(prompt)

    result = []
    correct_count = 0
    for i in tqdm(range(len(model_result)), desc="Running tests"):
        raw_result = model_result[i]["result"]
        try:
            decoded_result = handler.decode_execute(raw_result)
        except Exception as e:
            result.append(
                {
                    "id": i + 1,
                    "model_name": model_name,
                    "test_category": test_category,
                    "valid": False,
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
                        "model_name": model_name,
                        "test_category": test_category,
                        "valid": False,
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
                        "model_name": model_name,
                        "test_category": test_category,
                        "valid": False,
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
            checker_result = exec_checker(decoded_result, prompt_item, test_category)

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
            if "model_executed_output" in checker_result:
                temp["model_executed_output"] = checker_result["model_executed_output"]
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
    output_file_name = f"BFCL_v2_{test_category}_score.json"
    output_file_dir = os.path.join(OUTPUT_PATH, model_name)
    write_list_of_dicts_to_file(output_file_name, result, output_file_dir)

    return accuracy, len(model_result)


def single_relevance_file_runner(handler, model_result, prompt, model_name, test_category):
    # This function serves for both relevance and irrelevance tests, which share the exact opposite logic.
    # If `test_category` is "irrelevance", the model is expected to output no function call. 
    # No function call means either the AST decoding fails (a error message is generated) or the decoded AST does not contain any function call (such as a empty list, `[]`).
    # If `test_category` is "relevance", the model is expected to output to a function call, and empty list doesn't count as a function call.
    result = []
    correct_count = 0
    for i in range(len(model_result)):
        model_result_item = model_result[i]["result"]
        contain_func_call = False
        decoded_result = None
        decode_error = None

        try:
            decoded_result = handler.decode_ast(model_result_item, language="Python")
            # Decode successfully, which means the model output is in valid function call format
            contain_func_call = True
            if is_empty_output(decoded_result):
                # Empty output is not considered as a valid function call
                contain_func_call = False

        except Exception as e:
            # Decode failed, which means the model output is not in valid function call format
            contain_func_call = False
            decode_error = str(e)

        # irrelevance test means no function call outputted
        if "irrelevance" in test_category:
            success = not contain_func_call
        else:
            success = contain_func_call

        if success:
            correct_count += 1
        else:
            temp = {}
            temp["id"] = i + 1
            temp["model_name"] = model_name
            temp["test_category"] = test_category
            temp["valid"] = success
            if "irrelevance" in test_category:
                temp["error"] = [
                    f"Valid syntax. Successfully decode AST when it should not."
                ]
                temp["error_type"] = "irrelevance_error:decoder_success"
            else: 
                temp["error"] = [
                    f"Invalid syntax. Failed to decode AST when it should have. {decode_error}"
                ]
                temp["error_type"] = "relevance_error:decoder_failed"
            temp["prompt"] = prompt[i]
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
    output_file_name = f"BFCL_v2_{test_category}_score.json"
    output_file_dir = os.path.join(OUTPUT_PATH, model_name)
    write_list_of_dicts_to_file(output_file_name, result, output_file_dir)

    return accuracy, len(model_result)


def single_ast_file_runner(
    handler, model_result, prompt, possible_answer, language, test_category, model_name
):
    assert (
        len(model_result) == len(prompt) == len(possible_answer)
    ), f"The length of the model result ({len(model_result)}) does not match the length of the prompt ({len(prompt)}) or possible answer ({len(possible_answer)}). Please check the input files for completeness."

    result = []
    correct_count = 0
    for i in range(len(model_result)):
        model_result_item = model_result[i]["result"]
        prompt_item = prompt[i]["function"]
        possible_answer_item = possible_answer[i]["ground_truth"]

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
    output_file_name = f"BFCL_v2_{test_category}_score.json"
    output_file_dir = os.path.join(OUTPUT_PATH, model_name)
    write_list_of_dicts_to_file(output_file_name, result, output_file_dir)

    return accuracy, len(model_result)


#### Main runner function ####
def runner(model_names, test_categories, api_sanity_check):

    # A flag to indicate if the API has been tested.
    # We should always test the API with ground truth first before running the executable tests.
    # Sometimes the API may not be working as expected and we want to catch that before running the evaluation to ensure the results are accurate.
    API_TESTED = False
    API_STATUS_ERROR_REST = None
    API_STATUS_ERROR_EXECUTABLE = None

    # Before running the executable evaluation, we need to get the expected output from the ground truth.
    # So we need a list of all the test categories that we have ran the ground truth evaluation on.
    # We only get the expected output once for each test category.
    EXECUTABLE_TEST_CATEGORIES_HAVE_RUN = []

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

        # Pattern to match JSON files in this subdirectory
        json_files_pattern = os.path.join(subdir, "*.json")

        print(f"🦍 Model: {model_name}")

        # Find and process all JSON files in the subdirectory
        for model_result_json in glob.glob(json_files_pattern):

            test_category = extract_test_category(model_result_json)
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

            print(f"🔍 Running test: {test_category}")

            model_result = load_file(model_result_json)
            record_cost_latency(LEADERBOARD_TABLE, model_name, model_result)

            # Find the corresponding test file
            prompt_file = find_file_with_suffix(PROMPT_PATH, test_category)
            prompt = load_file(prompt_file)

            if is_relevance_or_irrelevance(test_category):
                accuracy, total_count = single_relevance_file_runner(
                    handler, model_result, prompt, model_name, test_category
                )
                record_result(
                    LEADERBOARD_TABLE, model_name, test_category, accuracy, total_count
                )
                print(f"✅ Test completed: {test_category}. 🎯 Accuracy: {accuracy}")
                continue

            if is_executable(test_category):
                # We only test the API with ground truth once
                if not API_TESTED and api_sanity_check:
                    print("---- Sanity checking API status ----")
                    try:
                        api_status_sanity_check_rest()
                    except BadAPIStatusError as e:
                        API_STATUS_ERROR_REST = e

                    try:
                        api_status_sanity_check_executable()
                    except BadAPIStatusError as e:
                        API_STATUS_ERROR_EXECUTABLE = e    

                    display_api_status_error(API_STATUS_ERROR_REST, API_STATUS_ERROR_EXECUTABLE, display_success=True)
                    print("Continuing evaluation...")
                    
                    API_TESTED = True

                if (
                    test_category not in EXECUTABLE_TEST_CATEGORIES_HAVE_RUN
                    and not is_rest(test_category)
                ):
                    print(
                        f"---- Getting real-time execution result from ground truth for {test_category} ----"
                    )
                    get_executable_expected_output(prompt_file)
                    print(
                        f"---- Ground truth real-time execution result obtained for {test_category} 🌟 ----"
                    )
                    EXECUTABLE_TEST_CATEGORIES_HAVE_RUN.append(test_category)
                    # Need to re-load the prompt file after getting the expected output, as the prompt file has been updated
                    prompt = load_file(prompt_file)

                accuracy, total_count = single_executable_file_runner(
                    handler, model_result, prompt, model_name, test_category
                )
                record_result(
                    LEADERBOARD_TABLE, model_name, test_category, accuracy, total_count
                )
                print(f"✅ Test completed: {test_category}. 🎯 Accuracy: {accuracy}")

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
            print(f"✅ Test completed: {test_category}. 🎯 Accuracy: {accuracy}")

    # This function reads all the score files from local folder and updates the leaderboard table.
    # This is helpful when you only want to run the evaluation for a subset of models and test categories.
    update_leaderboard_table_with_score_file(LEADERBOARD_TABLE, OUTPUT_PATH)
    # Write the leaderboard table to a file
    generate_leaderboard_csv(LEADERBOARD_TABLE, OUTPUT_PATH, model_names, test_categories)

    # Clean up the executable expected output files
    # They should be re-generated the next time the evaluation is run
    clean_up_executable_expected_output(
        PROMPT_PATH, EXECUTABLE_TEST_CATEGORIES_HAVE_RUN
    )
    
    display_api_status_error(API_STATUS_ERROR_REST, API_STATUS_ERROR_EXECUTABLE, display_success=False)
    
    print(
        f"🏁 Evaluation completed. See {os.path.abspath(OUTPUT_PATH + 'data_combined.csv')} for evaluation results on BFCL V2."
    )
    print(
        f"See {os.path.abspath(OUTPUT_PATH + 'data_live.csv')} and {os.path.abspath(OUTPUT_PATH + 'data_non_live.csv')} for evaluation results on BFCL V2 Live and Non-Live categories respectively."
    )


INPUT_PATH = "../../result/"
PROMPT_PATH = "../../data/"
POSSIBLE_ANSWER_PATH = "../../data/possible_answer/"
OUTPUT_PATH = "../../score/"

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
        "--test-category",
        nargs="+",
        type=str,
        help="A list of test categories to run the evaluation on",
    )
    parser.add_argument(
        "-c",
        "--api-sanity-check",
        action="store_true",
        default=False,  # Default value is False, meaning the sanity check is skipped unless the flag is specified
        help="Perform the REST API status sanity check before running the evaluation. By default, the sanity check is skipped.",
    )

    args = parser.parse_args()

    api_sanity_check = args.api_sanity_check
    test_categories = None
    if args.test_category is not None:
        test_categories = []
        for test_category in args.test_category:
            if test_category in TEST_COLLECTION_MAPPING:
                test_categories.extend(TEST_COLLECTION_MAPPING[test_category])
            else:
                test_categories.append(test_category)

    model_names = args.model
    if args.model is not None:
        model_names = []
        for model_name in args.model:
            # Runner takes in the model name that contains "_", instead of "/", for the sake of file path issues.
            # This is differnet than the model name format that the generation script "openfunctions_evaluation.py" takes in (where the name contains "/").
            # We patch it here to avoid confusing the user.
            model_names.append(model_name.replace("/", "_"))

    runner(model_names, test_categories, api_sanity_check)
