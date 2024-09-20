import glob
import json
import os
import re
import statistics
import subprocess

import numpy as np
from bfcl.eval_checker.constant import *
from bfcl.eval_checker.executable_eval.custom_exception import BadAPIStatusError
from bfcl.eval_checker.model_metadata import *
from bfcl.constant import VERSION_PREFIX
from bfcl.model_handler.handler_map import handler_map
from tqdm import tqdm


def extract_test_category(input_string):
    pattern = fr".*{VERSION_PREFIX}_(\w+?)(?:_score|_result)?\.json"
    match = re.search(pattern, input_string)

    # Check if there's a match and extract the captured group
    if match:
        return match.group(1)  # the first captured group (\w+)
    else:
        raise ValueError(f"Could not extract the test category from the input string: {input_string}")


def find_file_with_suffix(folder_path, suffix):
    json_files_pattern = os.path.join(folder_path, "*.json")
    for json_file in glob.glob(json_files_pattern):
        if extract_test_category(json_file) == suffix:
            return json_file
    raise FileNotFoundError(f"No JSON file found with suffix: {suffix}")

def is_multi_turn(test_category):
    return "multi_turn" in test_category

def contain_multi_turn_irrelevance(test_category):
    return "miss_func" in test_category or "miss_param" in test_category

def is_executable(test_category):
    return "exec" in test_category or "rest" in test_category


def is_rest(test_category):
    return "rest" in test_category


def is_relevance_or_irrelevance(test_category):
    return "relevance" in test_category or "irrelevance" in test_category


def is_chatable(test_category):
    return "chatable" in test_category


def is_java(test_category):
    return "java" in test_category


def is_js(test_category):
    return "javascript" in test_category


def is_sql(test_category):
    return "sql" in test_category


def load_file(file_path):
    result = []
    with open(file_path) as f:
        file = f.readlines()
        for line in file:
            result.append(json.loads(line))
    return result


def get_handler(model_name):
    return handler_map[model_name](model_name, temperature=0)  #Temperature doesn't matter for evaluation


def write_list_of_dicts_to_file(filename, data, subdir=None):
    if subdir:
        # Ensure the subdirectory exists
        os.makedirs(subdir, exist_ok=True)

        # Construct the full path to the file
        filename = os.path.join(subdir, filename)

    # Write the list of dictionaries to the file in JSON format
    with open(filename, "w") as f:
        for i, entry in enumerate(data):
            json_str = json.dumps(entry)
            f.write(json_str)
            if i < len(data) - 1:
                f.write("\n")


def is_function_calling_format_output(decoded_output):
    # Ensure the output is a list of dictionaries
    if type(decoded_output) == list:
        for item in decoded_output:
            if type(item) != dict:
                return False
        return True
    return False


def is_executable_format_output(decoded_output):
    # Ensure the output is a list of strings (one or more strings)
    if type(decoded_output) == list:
        if len(decoded_output) == 0:
            return False
        for item in decoded_output:
            if type(item) != str:
                return False
        return True
    return False


def is_rest_format_output(decoded_output):
    # Ensure the output is a list of one string
    if type(decoded_output) == list:
        if len(decoded_output) == 1 and type(decoded_output[0]) == str:
            return True
    return False


def is_empty_output(decoded_output):
    # This function is a patch to the ast decoder for relevance detection
    # Sometimes the ast decoder will parse successfully, but the input doens't really have a function call
    # [], [{}], and anything that is not in function calling format is considered empty (and thus should be marked as correct)
    if not is_function_calling_format_output(decoded_output):
        return True
    if len(decoded_output) == 0:
        return True
    if len(decoded_output) == 1 and len(decoded_output[0]) == 0:
        return True
    return False

def api_status_sanity_check_rest():

    # We only need to import the executable_checker_rest in this function. So a local import is used.
    from bfcl.eval_checker.executable_eval.executable_checker import (
        executable_checker_rest,
    )

    ground_truth_dummy = load_file(REST_API_GROUND_TRUTH_FILE_PATH)

    # Use the ground truth data to make sure the API is working correctly
    command = f"cd ../.. ; python apply_function_credential_config.py --input-path ./bfcl/eval_checker/{REST_API_GROUND_TRUTH_FILE_PATH};"
    try:
        subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        write_list_of_dicts_to_file(REST_API_GROUND_TRUTH_FILE_PATH, ground_truth_dummy)
        raise RuntimeError(e.stderr) from e

    ground_truth_replaced = load_file(REST_API_GROUND_TRUTH_FILE_PATH)
    write_list_of_dicts_to_file(REST_API_GROUND_TRUTH_FILE_PATH, ground_truth_dummy)

    correct_count = 0
    errors = []
    for idx, data in tqdm(
        enumerate(ground_truth_replaced),
        total=len(ground_truth_replaced),
        desc="API Status Test (REST)",
    ):
        status = executable_checker_rest(data["ground_truth"], idx)
        if status["valid"]:
            correct_count += 1
        else:
            errors.append((data, status))

    if correct_count != len(ground_truth_replaced):
        raise BadAPIStatusError(errors, f"{len(ground_truth_replaced) - correct_count} / {len(ground_truth_replaced)}")


def api_status_sanity_check_executable():
    from bfcl.eval_checker.executable_eval.executable_checker import (
        executable_checker_simple,
    )

    ground_truth = load_file(EXECTUABLE_API_GROUND_TRUTH_FILE_PATH)
    correct_count = 0
    errors = []
    for data in tqdm(
        ground_truth, total=len(ground_truth), desc="API Status Test (Non-REST)"
    ):
        status = executable_checker_simple(
            data["ground_truth"][0],
            data["execution_result"][0],
            data["execution_result_type"][0],
            True,
        )
        if status["valid"]:
            correct_count += 1
        else:
            errors.append((data, status))

    if correct_count != len(ground_truth):
        raise BadAPIStatusError(errors, f"{len(ground_truth) - correct_count} / {len(ground_truth)}")


def display_api_status_error(rest_error, executable_error, display_success=False):
    if not rest_error and not executable_error:
        if display_success:
            print("🟢 All API Status Test Passed!")
        return None
    
    print(f"\n{RED_FONT}{'-' * 18} Executable Categories' Error Bounds Based on API Health Status {'-' * 18}{RESET}\n")

    if rest_error:
        print(f"❗️ Warning: Unable to verify health of executable APIs used in executable test category (REST). Please contact API provider.\n")
        print(f"{rest_error.error_rate} APIs affected:\n")
        for data, status in rest_error.errors:
            print(f"  - Test Case: {data['ground_truth']}")
            print(f"    Error Type: {status['error_type']}\n")

    if executable_error:
        print(f"❗️ Warning: Unable to verify health of executable APIs used in executable test categories (Non-REST). Please contact API provider.\n")
        print(f"{executable_error.error_rate} APIs affected:\n")
        for data, status in executable_error.errors:
            print(f"  - Test Case: {data['ground_truth'][0]}")
            print(f"    Error Type: {status['error_type']}\n")

    print(f"{RED_FONT}{'-' * 100}\n{RESET}")


def get_executable_expected_output(prompt_file_path):
    # Before we run the evaluation, we need to add the "execution_result" field to the prompt file, using the ground truth data.
    prompt_content = load_file(prompt_file_path)
    exec_dict = {}
    for item in tqdm(prompt_content, desc="Getting Executable Expected Output"):
        execution_result = []
        ground_truth = item["ground_truth"]
        for i in range(len(ground_truth)):
            exec(
                "from bfcl.eval_checker.executable_eval.data.executable_python_function import *"
                + "\nresult="
                + ground_truth[i],
                exec_dict,
            )
            execution_result.append(exec_dict["result"])
        item["execution_result"] = execution_result

    write_list_of_dicts_to_file(prompt_file_path, prompt_content)


def clean_up_executable_expected_output(prompt_path, categories):
    for category in categories:
        prompt_file = find_file_with_suffix(prompt_path, category)
        prompt_content = load_file(prompt_file)
        for item in prompt_content:
            del item["execution_result"]
        write_list_of_dicts_to_file(prompt_file, prompt_content)


def calculate_weighted_accuracy(accuracy_dict_list):
    total_count = 0
    total_accuracy = 0
    for accuracy_dict in accuracy_dict_list:
        total_count += accuracy_dict["total_count"]
        total_accuracy += accuracy_dict["accuracy"] * accuracy_dict["total_count"]

    if total_count == 0:
        return {"accuracy": 0, "total_count": 0}

    return {"accuracy": total_accuracy / total_count, "total_count": total_count}


def calculate_unweighted_accuracy(accuracy_dict_list):
    total_count = 0
    total_accuracy = 0
    for accuracy_dict in accuracy_dict_list:
        total_count += accuracy_dict["total_count"]
        total_accuracy += accuracy_dict["accuracy"]

    if len(accuracy_dict_list) == 0:
        return {"accuracy": 0, "total_count": 0}

    return {"accuracy": total_accuracy / len(accuracy_dict_list), "total_count": total_count}


def record_result(leaderboard_table, model_name, test_category, accuracy, total_count):
    if model_name not in leaderboard_table:
        leaderboard_table[model_name] = {}
    leaderboard_table[model_name][test_category] = {
        "accuracy": accuracy,
        "total_count": total_count,
    }


def record_cost_latency(leaderboard_table, model_name, model_output_data):
    def process_data(key, data, output_list):
        # All entries are either a list of list (in multi-turn), or a single value (in single-turn)
        if key in data:
            if isinstance(data[key], list) and all(isinstance(inner_item, list) for inner_item in data[key]):
                flattened_list = sum(data[key], [])
                output_list.extend([item for item in flattened_list if item != 0])
            else:
                if data[key] != 0:
                    output_list.append(data[key])

    if model_name not in leaderboard_table:
        leaderboard_table[model_name] = {}
        leaderboard_table[model_name]["cost"] = {"input_data": [], "output_data": []}
        leaderboard_table[model_name]["latency"] = {"data": []}

    input_token = []
    output_token = []
    latency = []
    for data in model_output_data:
        for data in model_output_data:
            process_data("latency", data, latency)
            process_data("input_token_count", data, input_token)
            process_data("output_token_count", data, output_token)

    leaderboard_table[model_name]["cost"]["input_data"].extend(input_token)
    leaderboard_table[model_name]["cost"]["output_data"].extend(output_token)
    leaderboard_table[model_name]["latency"]["data"].extend(latency)


def get_cost_letency_info(model_name, cost_data, latency_data):
    # TODO: Update the cost and latency calculation since some models cannot be evaluated using v100 and also there are more entries.
    cost, mean_latency, std_latency, percentile_95_latency = "N/A", "N/A", "N/A", "N/A"

    if (
        model_name in INPUT_PRICE_PER_MILLION_TOKEN
        and len(cost_data["input_data"]) > 0
        and len(cost_data["output_data"]) > 0
    ):

        mean_input_token = statistics.mean(cost_data["input_data"])
        mean_output_token = statistics.mean(cost_data["output_data"])
        cost = (
            mean_input_token * INPUT_PRICE_PER_MILLION_TOKEN[model_name]
            + mean_output_token * OUTPUT_PRICE_PER_MILLION_TOKEN[model_name]
        ) / 1000
        cost = round(cost, 2)

    if model_name in OSS_LATENCY:
        mean_latency, std_latency, percentile_95_latency = (
            OSS_LATENCY[model_name] / 1700,
            "N/A",
            "N/A",
        )
        mean_latency = round(mean_latency, 2)
        cost = mean_latency * 1000 * V100_x8_PRICE_PER_HOUR / 3600
        cost = round(cost, 2)

    elif len(latency_data["data"]) != 0:
        mean_latency = statistics.mean(latency_data["data"])
        std_latency = statistics.stdev(latency_data["data"])
        percentile_95_latency = np.percentile(latency_data["data"], 95)
        mean_latency = round(mean_latency, 2)
        std_latency = round(std_latency, 2)
        percentile_95_latency = round(percentile_95_latency, 2)

        if model_name not in INPUT_PRICE_PER_MILLION_TOKEN:
            cost = sum(latency_data["data"]) * V100_x8_PRICE_PER_HOUR / 3600
            cost = round(cost, 2)

    if model_name in NO_COST_MODELS:
        cost = "N/A"

    return cost, mean_latency, std_latency, percentile_95_latency

# TODO: Refactor this function to reduce code duplication
def generate_leaderboard_csv(
    leaderboard_table, output_path, eval_models=None, eval_categories=None
):
    print("📈 Aggregating data to generate leaderboard score table...")
    data_non_live = []
    data_live = []
    data_multi_turn = []
    data_combined = []
    for model_name, value in leaderboard_table.items():
        model_name_escaped = model_name.replace("_", "/")
        
        cost_data = value.get("cost", {"input_data": [], "output_data": []})
        latency_data = value.get("latency", {"data": []})
        cost, latency_mean, latency_std, percentile_95_latency = get_cost_letency_info(
            model_name_escaped, cost_data, latency_data
        )
        
        # Non-Live Score
        python_simple_ast_non_live = value.get("simple", {"accuracy": 0, "total_count": 0})
        python_multiple_ast_non_live = value.get(
            "multiple", {"accuracy": 0, "total_count": 0}
        )
        python_parallel_ast_non_live = value.get(
            "parallel", {"accuracy": 0, "total_count": 0}
        )
        python_parallel_multiple_ast_non_live = value.get(
            "parallel_multiple", {"accuracy": 0, "total_count": 0}
        )
        python_simple_exec_non_live = value.get(
            "exec_simple", {"accuracy": 0, "total_count": 0}
        )
        python_multiple_exec_non_live = value.get(
            "exec_multiple", {"accuracy": 0, "total_count": 0}
        )
        python_parallel_exec_non_live = value.get(
            "exec_parallel", {"accuracy": 0, "total_count": 0}
        )
        python_parallel_multiple_exec_non_live = value.get(
            "exec_parallel_multiple", {"accuracy": 0, "total_count": 0}
        )
        java_simple_ast_non_live = value.get("java", {"accuracy": 0, "total_count": 0})
        javascript_simple_ast_non_live = value.get(
            "javascript", {"accuracy": 0, "total_count": 0}
        )
        rest_simple_exec_non_live = value.get("rest", {"accuracy": 0, "total_count": 0})
        irrelevance_non_live = value.get("irrelevance", {"accuracy": 0, "total_count": 0})

        simple_ast_non_live = calculate_unweighted_accuracy(
            [python_simple_ast_non_live, java_simple_ast_non_live, javascript_simple_ast_non_live]
        )
        multiple_ast_non_live = python_multiple_ast_non_live
        parallel_ast_non_live = python_parallel_ast_non_live
        parallel_multiple_ast_non_live = python_parallel_multiple_ast_non_live
        simple_exec_non_live = calculate_unweighted_accuracy(
            [python_simple_exec_non_live, rest_simple_exec_non_live]
        )
        multiple_exec_non_live = python_multiple_exec_non_live
        parallel_exec_non_live = python_parallel_exec_non_live
        parallel_multiple_exec_non_live = python_parallel_multiple_exec_non_live

        summary_ast_non_live = calculate_unweighted_accuracy(
            [simple_ast_non_live, multiple_ast_non_live, parallel_ast_non_live, parallel_multiple_ast_non_live]
        )
        summary_exec_non_live = calculate_unweighted_accuracy(
            [simple_exec_non_live, multiple_exec_non_live, parallel_exec_non_live, parallel_multiple_exec_non_live]
        )
        overall_accuracy_non_live = calculate_unweighted_accuracy(
            [
                simple_ast_non_live,
                multiple_ast_non_live,
                parallel_ast_non_live,
                parallel_multiple_ast_non_live,
                simple_exec_non_live,
                multiple_exec_non_live,
                parallel_exec_non_live,
                parallel_multiple_exec_non_live,
                irrelevance_non_live,
            ]
        )

        data_non_live.append(
            [
                "N/A",
                MODEL_METADATA_MAPPING[model_name_escaped][0],
                overall_accuracy_non_live["accuracy"],
                summary_ast_non_live["accuracy"],
                summary_exec_non_live["accuracy"],
                simple_ast_non_live["accuracy"],
                python_simple_ast_non_live["accuracy"],
                java_simple_ast_non_live["accuracy"],
                javascript_simple_ast_non_live["accuracy"],
                multiple_ast_non_live["accuracy"],
                parallel_ast_non_live["accuracy"],
                parallel_multiple_ast_non_live["accuracy"],
                simple_exec_non_live["accuracy"],
                python_simple_exec_non_live["accuracy"],
                rest_simple_exec_non_live["accuracy"],
                multiple_exec_non_live["accuracy"],
                parallel_exec_non_live["accuracy"],
                parallel_multiple_exec_non_live["accuracy"],
                irrelevance_non_live["accuracy"],
            ]
        )
        
        # Live Score
        python_simple_ast_live = value.get(
            "live_simple", {"accuracy": 0, "total_count": 0}
        )
        python_multiple_ast_live = value.get(
            "live_multiple", {"accuracy": 0, "total_count": 0}
        )
        python_parallel_ast_live = value.get(
            "live_parallel", {"accuracy": 0, "total_count": 0}
        )
        python_parallel_multiple_ast_live = value.get(
            "live_parallel_multiple", {"accuracy": 0, "total_count": 0}
        )
        irrelevance_live = value.get(
            "live_irrelevance", {"accuracy": 0, "total_count": 0}
        )
        relevance_live = value.get("live_relevance", {"accuracy": 0, "total_count": 0})
        summary_ast_live = calculate_weighted_accuracy(
            [
                python_simple_ast_live,
                python_multiple_ast_live,
                python_parallel_ast_live,
                python_parallel_multiple_ast_live,
            ]
        )

        overall_accuracy_live = calculate_weighted_accuracy(
            [
                python_simple_ast_live,
                python_multiple_ast_live,
                python_parallel_ast_live,
                python_parallel_multiple_ast_live,
                irrelevance_live,
                relevance_live,
            ]
        )
        
        data_live.append(
            [
                "N/A",
                MODEL_METADATA_MAPPING[model_name_escaped][0],
                overall_accuracy_live["accuracy"],
                summary_ast_live["accuracy"],
                python_simple_ast_live["accuracy"],
                python_multiple_ast_live["accuracy"],
                python_parallel_ast_live["accuracy"],
                python_parallel_multiple_ast_live["accuracy"],
                irrelevance_live["accuracy"],
                relevance_live["accuracy"],
            ]
        )
        
        # Multi-Turn Score
        multi_turn_base = value.get("multi_turn_base", {"accuracy": 0, "total_count": 0})
        multi_turn_miss_func = value.get(
            "multi_turn_miss_func", {"accuracy": 0, "total_count": 0}
        )
        multi_turn_miss_param = value.get(
            "multi_turn_miss_param", {"accuracy": 0, "total_count": 0}
        )
        multi_turn_long_context = value.get(
            "multi_turn_long_context", {"accuracy": 0, "total_count": 0}
        )
        multi_turn_composite = value.get(
            "multi_turn_composite", {"accuracy": 0, "total_count": 0}
        )
        overall_accuracy_multi_turn = calculate_unweighted_accuracy(
            [
                multi_turn_base,
                multi_turn_miss_func,
                multi_turn_miss_param,
                multi_turn_long_context,
                # multi_turn_composite,  # Composite is currently not included in the leaderboard, because it takes too long to evaluate
            ]
        )

        data_multi_turn.append(
            [
                "N/A",
                MODEL_METADATA_MAPPING[model_name_escaped][0],
                overall_accuracy_multi_turn["accuracy"],
                multi_turn_base["accuracy"],
                multi_turn_miss_func["accuracy"],
                multi_turn_miss_param["accuracy"],
                multi_turn_long_context["accuracy"],
                # multi_turn_composite["accuracy"],
            ]
        )
        
        # Total Score
        single_turn_ast = calculate_unweighted_accuracy([overall_accuracy_live, overall_accuracy_non_live])
        total_irrelevance = calculate_unweighted_accuracy([irrelevance_non_live, irrelevance_live])
        total_relevance = relevance_live
        
        total_overall_accuracy = calculate_unweighted_accuracy(
            [
                overall_accuracy_live,
                overall_accuracy_non_live,
                overall_accuracy_multi_turn,
            ]
        )

        data_combined.append(
            [
                "N/A",
                total_overall_accuracy["accuracy"],
                MODEL_METADATA_MAPPING[model_name_escaped][0],
                MODEL_METADATA_MAPPING[model_name_escaped][1],
                cost,
                latency_mean,
                latency_std,
                percentile_95_latency,
                summary_ast_non_live["accuracy"],
                simple_ast_non_live["accuracy"],
                multiple_ast_non_live["accuracy"],
                parallel_ast_non_live["accuracy"],
                parallel_multiple_ast_non_live["accuracy"],
                summary_exec_non_live["accuracy"],
                simple_exec_non_live["accuracy"],
                multiple_exec_non_live["accuracy"],
                parallel_exec_non_live["accuracy"],
                parallel_multiple_exec_non_live["accuracy"],
                overall_accuracy_live["accuracy"],
                python_simple_ast_live["accuracy"],
                python_multiple_ast_live["accuracy"],
                python_parallel_ast_live["accuracy"],
                python_parallel_multiple_ast_live["accuracy"],
                overall_accuracy_multi_turn["accuracy"],
                multi_turn_base["accuracy"],
                multi_turn_miss_func["accuracy"],
                multi_turn_miss_param["accuracy"],
                multi_turn_long_context["accuracy"],
                'N/A',  # No composite score for now
                # multi_turn_composite["accuracy"],
                total_relevance["accuracy"],
                total_irrelevance["accuracy"],
                MODEL_METADATA_MAPPING[model_name_escaped][2],
                MODEL_METADATA_MAPPING[model_name_escaped][3],
            ]
        )
        
    # Write Non-Live Score File
    data_non_live.sort(key=lambda x: x[1], reverse=True)
    for i in range(len(data_non_live)):
        data_non_live[i][0] = str(i + 1)
        for j in range(2, len(data_non_live[i])):
            data_non_live[i][j] = "{:.2f}%".format(data_non_live[i][j] * 100)

    data_non_live.insert(0, COLUMNS_NON_LIVE)

    filepath = os.path.join(output_path, "data_non_live.csv")
    with open(filepath, "w") as f:
        for i, row in enumerate(data_non_live):
            if i < len(data_non_live) - 1:
                f.write(",".join(row) + "\n")
            else:
                f.write(",".join(row))
    
    # Write Live Score File
    data_live.sort(key=lambda x: x[1], reverse=True)
    for i in range(len(data_live)):
        data_live[i][0] = str(i + 1)
        for j in range(2, len(data_live[i])):
            data_live[i][j] = "{:.2f}%".format(data_live[i][j] * 100)

    data_live.insert(0, COLUMNS_LIVE)

    filepath = os.path.join(output_path, "data_live.csv")
    with open(filepath, "w") as f:
        for i, row in enumerate(data_live):
            if i < len(data_live) - 1:
                f.write(",".join(row) + "\n")
            else:
                f.write(",".join(row))

    # Write Total Score File
    data_combined.sort(key=lambda x: x[1], reverse=True)
    for i in range(len(data_combined)):
        data_combined[i][0] = str(i + 1)
        data_combined[i][1] = "{:.2f}%".format(data_combined[i][1] * 100)
        for j in range(4, 8):
            data_combined[i][j] = str(data_combined[i][j])
        for j in range(8, len(data_combined[i]) - 2):
            # TODO: Remove this after composite is added
            data_combined[i][j] = "{:.2f}%".format(data_combined[i][j] * 100) if data_combined[i][j] != 'N/A' else 'N/A'
        for j in range(len(data_combined[i]) - 2, len(data_combined[i])):
            data_combined[i][j] = str(data_combined[i][j])

    data_combined.insert(0, COLUMNS_OVERALL)

    filepath = os.path.join(output_path, "data_overall.csv")
    with open(filepath, "w") as f:
        for i, row in enumerate(data_combined):
            if i < len(data_combined) - 1:
                f.write(",".join(row) + "\n")
            else:
                f.write(",".join(row))

    # TODO: Update and optimize the logic
    # Check if all categories are present and evaluated for all models
    # if eval_models:
    #     category_status = check_model_category_status(score_path=output_path)
    #     check_all_category_present(
    #         category_status, eval_models=eval_models, eval_categories=eval_categories
    #     )


def check_model_category_status(score_path):
    result_path = score_path.replace("score", "result")

    leaderboard_categories = [
        "exec_simple",
        "exec_parallel",
        "exec_multiple",
        "exec_parallel_multiple",
        "simple",
        "irrelevance",
        "parallel",
        "multiple",
        "parallel_multiple",
        "java",
        "javascript",
        "rest",
        "live_simple",
        "live_multiple",
        "live_parallel",
        "live_parallel_multiple",
        "live_irrelevance",
        "live_relevance",
    ]

    category_status = {}

    # Check for all models in MODEL_METADATA_MAPPING
    for model_name in MODEL_METADATA_MAPPING.keys():
        category_status[model_name] = {
            category: {"generated": False, "evaluated": False}
            for category in leaderboard_categories
        }

        # Check result folder
        result_subdir = os.path.join(result_path, model_name)
        if os.path.exists(result_subdir):
            for result_file in os.listdir(result_subdir):
                if result_file.endswith('.json'):
                    test_category = extract_test_category(result_file)
                    if test_category in category_status[model_name]:
                        category_status[model_name][test_category]["generated"] = True

        # Check score folder
        score_subdir = os.path.join(score_path, model_name)
        if os.path.exists(score_subdir):
            for score_file in os.listdir(score_subdir):
                test_category = extract_test_category(score_file)
                if test_category in category_status[model_name]:
                    category_status[model_name][test_category]["evaluated"] = True

    return category_status


def check_all_category_present(category_status, eval_models=None, eval_categories=None):
    found_issues = False
    first_time = True
    commands = []

    for model_name, categories in category_status.items():
        if eval_models and model_name not in eval_models:
            continue

        not_generated = [
            cat
            for cat, status in categories.items()
            if not status["generated"]
            and (not eval_categories or cat in eval_categories)
        ]
        not_evaluated = [
            cat
            for cat, status in categories.items()
            if not status["evaluated"]
            and (not eval_categories or cat in eval_categories)
        ]

        if not_generated or not_evaluated:
            found_issues = True
            if first_time:
                print(f"We are checking models: {eval_models} and categories: {eval_categories}")
                print(f"\n{RED_FONT}{'=' * 30} Model Category Status {'=' * 30}{RESET}")
                first_time = False       
 
            print(f"{RED_FONT}Model: {model_name}{RESET}")
            if not_generated:
                print(f"\n  Missing results for {len(not_generated)} categories:")
                for cat in not_generated:
                    print(f"    - {cat}")
                commands.append("cd ..")
                commands.append(
                    f"python openfunctions_evaluation.py --model {model_name} --test-category {' '.join(not_generated)}"
                )

            if not_evaluated:
                print(f"\n  Unevaluated results for {len(not_evaluated)} categories:")
                for cat in not_evaluated:
                    print(f"    - {cat}")

            all_categories = set(not_generated + not_evaluated)
            if all_categories:
                commands.append("cd eval_checker")
                commands.append(
                    f"python eval_runner.py --model {model_name} --test-category {' '.join(all_categories)}"
                )

    if found_issues:
        print(f"\n{RED_FONT}{'=' * 40} Recommended Actions {'=' * 40}{RESET}\n")
        print(
            "To address these issues, run the following commands from the current directory:"
        )
        print("\n" + " && \\\n".join(commands))
        print(f"\n{RED_FONT}{'=' * 100}{RESET}\n")
    else:
        print("🎉 All categories are present and evaluated for all models!\n")

    return found_issues


def update_leaderboard_table_with_score_file(leaderboard_table, score_path):

    entries = os.scandir(score_path)

    # Filter out the subdirectories
    subdirs = [entry.path for entry in entries if entry.is_dir()]

    # Traverse each subdirectory
    for subdir in subdirs:
        # Pattern to match JSON files in this subdirectory
        json_files_pattern = os.path.join(subdir, "*.json")
        model_name = subdir.split(score_path)[1]
        # Find and process all JSON files in the subdirectory
        for model_score_json in glob.glob(json_files_pattern):
            metadata = load_file(model_score_json)[0]
            accuracy, total_count = metadata["accuracy"], metadata["total_count"]
            test_category = extract_test_category(model_score_json)
            if model_name not in leaderboard_table:
                leaderboard_table[model_name] = {}
            if test_category not in leaderboard_table[model_name]:
                leaderboard_table[model_name][test_category] = {
                    "accuracy": accuracy,
                    "total_count": total_count,
                }


def collapse_json_objects(file_path):
    with open(file_path, "r") as file:
        content = file.read()

    objects = []
    depth = 0
    obj_start = 0
    for i, char in enumerate(content):
        if char == "{":
            if depth == 0:
                obj_start = i
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                obj = content[obj_start : i + 1]
                objects.append(obj)

    with open(file_path, "w") as out_file:
        for obj in objects:
            json_obj = json.loads(obj)
            compact_json = json.dumps(json_obj, separators=(",", ":"))
            out_file.write(compact_json + "\n")
