import glob
import json
import os
import statistics
import subprocess

import numpy as np
from custom_exception import BadAPIStatusError
from model_handler.handler_map import handler_map
from tqdm import tqdm
from eval_checker_constant import FILENAME_INDEX_MAPPING

REST_API_GROUND_TRUTH_FILE_PATH = "api_status_check_ground_truth_REST.json"
EXECTUABLE_API_GROUND_TRUTH_FILE_PATH = "api_status_check_ground_truth_executable.json"

COLUMNS = [
    "Rank",
    "Overall Acc",
    "Model",
    "Model Link",
    "Organization",
    "License",
    "AST Summary",
    "Exec Summary",
    "Simple Function AST",
    "Python Simple Function AST",
    "Java Simple Function AST",
    "JavaScript Simple Function AST",
    "Multiple Functions AST",
    "Parallel Functions AST",
    "Parallel Multiple AST",
    "Simple Function Exec",
    "Python Simple Function Exec",
    "REST Simple Function Exec",
    "Multiple Functions Exec",
    "Parallel Functions Exec",
    "Parallel Multiple Exec",
    "Relevance Detection",
    "Cost ($ Per 1k Function Calls)",
    "Latency Mean (s)",
    "Latency Standard Deviation (s)",
    "Latency 95th Percentile (s)",
]

# Note that we don't need to substitute `_` with `/` in the model name here.
MODEL_METADATA_MAPPING = {
    "gpt-4o-2024-05-13-FC": [
        "GPT-4o-2024-05-13 (FC)",
        "https://openai.com/index/hello-gpt-4o/",
        "OpenAI",
        "Proprietary",
    ],
    "gpt-4o-2024-05-13": [
        "GPT-4o-2024-05-13 (Prompt)",
        "https://openai.com/index/hello-gpt-4o/",
        "OpenAI",
        "Proprietary",
    ],
    "gpt-4-1106-preview-FC": [
        "GPT-4-1106-Preview (FC)",
        "https://platform.openai.com/docs/models/gpt-4-and-gpt-4-turbo",
        "OpenAI",
        "Proprietary",
    ],
    "gpt-4-1106-preview": [
        "GPT-4-1106-Preview (Prompt)",
        "https://platform.openai.com/docs/models/gpt-4-and-gpt-4-turbo",
        "OpenAI",
        "Proprietary",
    ],
    "gpt-4-0125-preview-FC": [
        "GPT-4-0125-Preview (FC)",
        "https://platform.openai.com/docs/models/gpt-4-and-gpt-4-turbo",
        "OpenAI",
        "Proprietary",
    ],
    "gpt-4-0125-preview": [
        "GPT-4-0125-Preview (Prompt)",
        "https://platform.openai.com/docs/models/gpt-4-and-gpt-4-turbo",
        "OpenAI",
        "Proprietary",
    ],
    "gpt-4-turbo-2024-04-09-FC": [
        "GPT-4-turbo-2024-04-09 (FC)",
        "https://platform.openai.com/docs/models/gpt-4-and-gpt-4-turbo",
        "OpenAI",
        "Proprietary",
    ],
    "gpt-4-turbo-2024-04-09": [
        "GPT-4-turbo-2024-04-09 (Prompt)",
        "https://platform.openai.com/docs/models/gpt-4-and-gpt-4-turbo",
        "OpenAI",
        "Proprietary",
    ],
    "gorilla-openfunctions-v2": [
        "Gorilla-OpenFunctions-v2 (FC)",
        "https://gorilla.cs.berkeley.edu/blogs/7_open_functions_v2.html",
        "Gorilla LLM",
        "Apache 2.0",
    ],
    "claude-3-opus-20240229-FC": [
        "Claude-3-Opus-20240229 (FC tools-2024-04-04)",
        "https://www.anthropic.com/news/claude-3-family",
        "Anthropic",
        "Proprietary",
    ],
    "claude-3-opus-20240229": [
        "Claude-3-Opus-20240229 (Prompt)",
        "https://www.anthropic.com/news/claude-3-family",
        "Anthropic",
        "Proprietary",
    ],
    "mistral-medium-2312": [
        "Mistral-Medium-2312 (Prompt)",
        "https://docs.mistral.ai/guides/model-selection/",
        "Mistral AI",
        "Proprietary",
    ],
    "mistral-small-2402": [
        "Mistral-Small-2402 (Prompt)",
        "https://docs.mistral.ai/guides/model-selection/",
        "Mistral AI",
        "Proprietary",
    ],
    "mistral-large-2402": [
        "Mistral-Large-2402 (Prompt)",
        "https://docs.mistral.ai/guides/model-selection/",
        "Mistral AI",
        "Proprietary",
    ],
    "claude-3-sonnet-20240229-FC": [
        "Claude-3-Sonnet-20240229 (FC tools-2024-04-04)",
        "https://www.anthropic.com/news/claude-3-family",
        "Anthropic",
        "Proprietary",
    ],
    "claude-3-sonnet-20240229": [
        "Claude-3-Sonnet-20240229 (Prompt)",
        "https://www.anthropic.com/news/claude-3-family",
        "Anthropic",
        "Proprietary",
    ],
    "claude-3-haiku-20240307-FC": [
        "Claude-3-Haiku-20240307 (FC tools-2024-04-04)",
        "https://www.anthropic.com/news/claude-3-family",
        "Anthropic",
        "Proprietary",
    ],
    "claude-3-haiku-20240307": [
        "Claude-3-Haiku-20240307 (Prompt)",
        "https://www.anthropic.com/news/claude-3-family",
        "Anthropic",
        "Proprietary",
    ],
    "gpt-3.5-turbo-0125-FC": [
        "GPT-3.5-Turbo-0125 (FC)",
        "https://platform.openai.com/docs/models/gpt-3-5-turbo",
        "OpenAI",
        "Proprietary",
    ],
    "gpt-3.5-turbo-0125": [
        "GPT-3.5-Turbo-0125 (Prompting)",
        "https://platform.openai.com/docs/models/gpt-3-5-turbo",
        "OpenAI",
        "Proprietary",
    ],
    "meetkai_functionary-small-v2.2-FC": [
        "Functionary-Small-v2.2 (FC)",
        "https://huggingface.co/meetkai/functionary-small-v2.2",
        "MeetKai",
        "MIT",
    ],
    "meetkai_functionary-medium-v2.2-FC": [
        "Functionary-Medium-v2.2 (FC)",
        "https://huggingface.co/meetkai/functionary-medium-v2.2",
        "MeetKai",
        "MIT",
    ],
    "meetkai_functionary-small-v2.4-FC": [
        "Functionary-Small-v2.4 (FC)",
        "https://huggingface.co/meetkai/functionary-small-v2.4",
        "MeetKai",
        "MIT",
    ],
    "meetkai_functionary-medium-v2.4-FC": [
        "Functionary-Medium-v2.4 (FC)",
        "https://huggingface.co/meetkai/functionary-medium-v2.4",
        "MeetKai",
        "MIT",
    ],
    "claude-2.1": [
        "Claude-2.1 (Prompt)",
        "https://www.anthropic.com/news/claude-2-1",
        "Anthropic",
        "Proprietary",
    ],
    "mistral-tiny-2312": [
        "Mistral-tiny-2312 (Prompt)",
        "https://docs.mistral.ai/guides/model-selection/",
        "Mistral AI",
        "Proprietary",
    ],
    "claude-instant-1.2": [
        "Claude-instant-1.2 (Prompt)",
        "https://www.anthropic.com/news/releasing-claude-instant-1-2",
        "Anthropic",
        "Proprietary",
    ],
    "mistral-small-2402-FC-Auto": [
        "Mistral-small-2402 (FC Auto)",
        "https://docs.mistral.ai/guides/model-selection/",
        "Mistral AI",
        "Proprietary",
    ],
    "mistral-large-2402-FC-Any": [
        "Mistral-large-2402 (FC Any)",
        "https://docs.mistral.ai/guides/model-selection/",
        "Mistral AI",
        "Proprietary",
    ],
    "mistral-small-2402-FC-Any": [
        "Mistral-small-2402 (FC Any)",
        "https://docs.mistral.ai/guides/model-selection/",
        "Mistral AI",
        "Proprietary",
    ],
    "mistral-large-2402-FC-Auto": [
        "Mistral-large-2402 (FC Auto)",
        "https://docs.mistral.ai/guides/model-selection/",
        "Mistral AI",
        "Proprietary",
    ],
    "Nexusflow-Raven-v2": [
        "Nexusflow-Raven-v2 (FC)",
        "https://huggingface.co/Nexusflow/NexusRaven-V2-13B",
        "Nexusflow",
        "Apache 2.0",
    ],
    "firefunction-v1-FC": [
        "FireFunction-v1 (FC)",
        "https://huggingface.co/fireworks-ai/firefunction-v1",
        "Fireworks",
        "Apache 2.0",
    ],
    "firefunction-v2-FC": [
        "FireFunction-v2 (FC)",
        "https://huggingface.co/fireworks-ai/firefunction-v2",
        "Fireworks",
        "Apache 2.0",
    ],
    "gemini-1.5-pro-preview-0514": [
        "Gemini-1.5-Pro-Preview-0514 (FC)",
        "https://deepmind.google/technologies/gemini/pro/",
        "Google",
        "Proprietary",
    ],
    "gemini-1.5-flash-preview-0514": [
        "Gemini-1.5-Flash-Preview-0514 (FC)",
        "https://deepmind.google/technologies/gemini/flash/",
        "Google",
        "Proprietary",
    ],
    "gemini-1.5-pro-preview-0409": [
        "Gemini-1.5-Pro-Preview-0409 (FC)",
        "https://deepmind.google/technologies/gemini/#introduction",
        "Google",
        "Proprietary",
    ],
    "gemini-1.0-pro": [
        "Gemini-1.0-Pro-001 (FC)",
        "https://deepmind.google/technologies/gemini/#introduction",
        "Google",
        "Proprietary",
    ],
    "gpt-4-0613-FC": [
        "GPT-4-0613 (FC)",
        "https://platform.openai.com/docs/models/gpt-4-and-gpt-4-turbo",
        "OpenAI",
        "Proprietary",
    ],
    "gpt-4-0613": [
        "GPT-4-0613 (Prompt)",
        "https://platform.openai.com/docs/models/gpt-4-and-gpt-4-turbo",
        "OpenAI",
        "Proprietary",
    ],
    "deepseek-ai_deepseek-coder-6.7b-instruct": [
        "Deepseek-v1.5 (Prompt)",
        "https://huggingface.co/deepseek-ai/deepseek-coder-7b-instruct-v1.5",
        "Deepseek",
        "Deepseek License",
    ],
    "google_gemma-7b-it": [
        "Gemma-7b-it (Prompt)",
        "https://blog.google/technology/developers/gemma-open-models/",
        "Google",
        "gemma-terms-of-use",
    ],
    "glaiveai_glaive-function-calling-v1": [
        "Glaive-v1 (FC)",
        "https://huggingface.co/glaiveai/glaive-function-calling-v1",
        "Glaive",
        "cc-by-sa-4.0",
    ],
    "databricks-dbrx-instruct": [
        "DBRX-Instruct (Prompt)",
        "https://www.databricks.com/blog/introducing-dbrx-new-state-art-open-llm",
        "Databricks",
        "Databricks Open Model",
    ],
    "NousResearch_Hermes-2-Pro-Mistral-7B": [
        "Hermes-2-Pro-Mistral-7B (FC)",
        "https://huggingface.co/NousResearch/Hermes-2-Pro-Mistral-7B",
        "NousResearch",
        "apache-2.0",
    ],
    "meta-llama_Meta-Llama-3-8B-Instruct": [
        "Meta-Llama-3-8B-Instruct (Prompt)",
        "https://llama.meta.com/llama3",
        "Meta",
        "Meta Llama 3 Community",
    ],
    "meta-llama_Meta-Llama-3-70B-Instruct": [
        "Meta-Llama-3-70B-Instruct (Prompt)",
        "https://llama.meta.com/llama3",
        "Meta",
        "Meta Llama 3 Community",
    ],
    "command-r-plus-FC": [
        "Command-R-Plus (FC) (Original)",
        "https://txt.cohere.com/command-r-plus-microsoft-azure",
        "Cohere For AI",
        "cc-by-nc-4.0",
    ],
    "command-r-plus": [
        "Command-R-Plus (Prompt) (Original)",
        "https://txt.cohere.com/command-r-plus-microsoft-azure",
        "Cohere For AI",
        "cc-by-nc-4.0",
    ],
    "command-r-plus-FC-optimized": [
        "Command-R-Plus (FC) (Optimized)",
        "https://txt.cohere.com/command-r-plus-microsoft-azure",
        "Cohere For AI",
        "cc-by-nc-4.0",
    ],
    "command-r-plus-optimized": [
        "Command-R-Plus (Prompt) (Optimized)",
        "https://txt.cohere.com/command-r-plus-microsoft-azure",
        "Cohere For AI",
        "cc-by-nc-4.0",
    ],
    "snowflake_arctic": [
        "Snowflake/snowflake-arctic-instruct (Prompt)",
        "https://huggingface.co/Snowflake/snowflake-arctic-instruct",
        "Snowflake",
        "apache-2.0",
    ],
}

INPUT_PRICE_PER_MILLION_TOKEN = {
    "claude-3-opus-20240229-FC": 15,
    "claude-3-opus-20240229": 15,
    "claude-3-sonnet-20240229-FC": 3,
    "claude-3-sonnet-20240229": 3,
    "claude-3-haiku-20240307-FC": 0.25,
    "claude-3-haiku-20240307": 0.25,
    "claude-2.1": 8,
    "claude-instant-1.2": 0.8,
    "mistral-large-2402-FC-Any": 4,
    "mistral-large-2402-FC-Auto": 4,
    "mistral-medium-2312": 2.7,
    "mistral-small-2402-FC-Any": 1,
    "mistral-small-2402-FC-Auto": 1,
    "mistral-small-2402": 1,
    "mistral-tiny-2312": 0.25,
    "gpt-4o-2024-05-13-FC": 5,
    "gpt-4o-2024-05-13": 5,
    "gpt-4-1106-preview-FC": 10,
    "gpt-4-1106-preview": 10,
    "gpt-4-0125-preview": 10,
    "gpt-4-0125-preview-FC": 10,
    "gpt-4-turbo-2024-04-09-FC": 10,
    "gpt-4-turbo-2024-04-09": 10,
    "gpt-4-0613": 30,
    "gpt-4-0613-FC": 30,
    "gpt-3.5-turbo-0125": 0.5,
    "gpt-3.5-turbo-0125-FC": 0.5,
    "gemini-1.0-pro": 0.5,
    "gemini-1.5-pro-preview-0409": 3.5,
    "gemini-1.5-pro-preview-0514": 3.5,
    "gemini-1.5-flash-preview-0514": 0.35,
    "databricks-dbrx-instruct": 2.25,
    "command-r-plus-FC": 3,
    "command-r-plus": 3,
    "command-r-plus-FC-optimized": 3,
    "command-r-plus-optimized": 3,
}

OUTPUT_PRICE_PER_MILLION_TOKEN = {
    "claude-3-opus-20240229-FC": 75,
    "claude-3-opus-20240229": 75,
    "claude-3-sonnet-20240229-FC": 15,
    "claude-3-sonnet-20240229": 15,
    "claude-3-haiku-20240307-FC": 1.25,
    "claude-3-haiku-20240307": 1.25,
    "claude-2.1": 24,
    "claude-instant-1.2": 2.4,
    "mistral-large-2402-FC-Any": 12,
    "mistral-large-2402-FC-Auto": 12,
    "mistral-small-2402": 3,
    "mistral-medium-2312": 8.1,
    "mistral-small-2402-FC-Any": 3,
    "mistral-small-2402-FC-Auto": 3,
    "mistral-tiny-2312": 0.25,
    "gpt-4o-2024-05-13-FC": 15,
    "gpt-4o-2024-05-13": 15,
    "gpt-4-turbo-2024-04-09-FC": 30,
    "gpt-4-turbo-2024-04-09": 30,
    "gpt-4-1106-preview": 30,
    "gpt-4-1106-preview-FC": 30,
    "gpt-4-0125-preview-FC": 30,
    "gpt-4-0125-preview": 30,
    "gpt-4-0613": 60,
    "gpt-4-0613-FC": 60,
    "gpt-3.5-turbo-0125": 1.5,
    "gpt-3.5-turbo-0125-FC": 1.5,
    "gemini-1.0-pro": 1.5,
    "gemini-1.5-pro-preview-0409": 10.50,
    "gemini-1.5-pro-preview-0514": 10.50,
    "gemini-1.5-flash-preview-0514": 0.53,
    "databricks-dbrx-instruct": 6.75,
    "command-r-plus-FC": 15,
    "command-r-plus": 15,
    "command-r-plus-FC-optimized": 15,
    "command-r-plus-optimized": 15,
}

# The latency of the open-source models are hardcoded here.
# Because we do batching when generating the data, so the latency is not accurate from the result data.
# This is the latency for the whole batch of data, when using 8 V100 GPUs.
OSS_LATENCY = {
    "deepseek-ai/deepseek-coder-6.7b-instruct": 909,
    "google/gemma-7b-it": 95,
    "NousResearch/Hermes-2-Pro-Mistral-7B": 135,
    "meta-llama/Meta-Llama-3-8B-Instruct": 73,
    "meta-llama/Meta-Llama-3-70B-Instruct": 307,
    "gorilla-openfunctions-v2": 83,
}


NO_COST_MODELS = [
    "Nexusflow-Raven-v2",
    "firefunction-v1-FC",
    "firefunction-v2-FC",
    "meetkai/functionary-medium-v2.4-FC",
    "meetkai/functionary-small-v2.2-FC",
    "meetkai/functionary-small-v2.4-FC",
    "snowflake/arctic",
]

# Price got from AZure, 22.032 per hour for 8 V100, Pay As You Go Total Price
# Reference: https://azure.microsoft.com/en-us/pricing/details/machine-learning/
V100_x8_PRICE_PER_HOUR = 22.032


def extract_after_test(input_string):
    parts = input_string.split("_test_")[1].split("_result")[0].split(".json")[0]
    return parts


def find_file_with_suffix(folder_path, suffix):
    json_files_pattern = os.path.join(folder_path, "*.json")
    for json_file in glob.glob(json_files_pattern):
        if extract_after_test(json_file) == suffix:
            return json_file


def is_executable(test_category):
    return "executable" in test_category or "rest" in test_category


def is_rest(test_category):
    return "rest" in test_category


def is_relevance(test_category):
    return "relevance" in test_category


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
    return handler_map[model_name](model_name)


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


def api_status_sanity_check_rest():

    # We only need to import the executable_checker_rest in this function. So a local import is used.
    from checker import executable_checker_rest

    ground_truth_dummy = load_file(REST_API_GROUND_TRUTH_FILE_PATH)

    # Use the ground truth data to make sure the API is working correctly
    command = f"cd .. ; python apply_function_credential_config.py --input-file ./eval_checker/{REST_API_GROUND_TRUTH_FILE_PATH};"
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
        [print("Data:", data, "\nError:", status["error"]) for data, status in errors]
        error_msg = f"API Status Test Failed for REST Section. {len(ground_truth_replaced) - correct_count} out of {len(ground_truth_replaced)} API behaviors are not as expected. Be careful with executable test category results; they may be inaccurate."
        raise BadAPIStatusError(error_msg)


def api_status_sanity_check_executable():
    from checker import executable_checker_simple

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
        [print("Data:", data, "\nError:", status["error"]) for data, status in errors]
        error_msg = f"API Status Test Failed for Executable Section. {len(ground_truth) - correct_count} out of {len(ground_truth)} API behaviors are not as expected. Be careful with executable test category results; they may be inaccurate."
        raise BadAPIStatusError(error_msg)


def get_executable_expected_output(prompt_file_path):
    # Before we run the evaluation, we need to add the "execution_result" field to the prompt file, using the ground truth data.
    prompt_content = load_file(prompt_file_path)
    exec_dict = {}
    for item in tqdm(prompt_content, desc="Getting Executable Expected Output"):
        execution_result = []
        ground_truth = item["ground_truth"]
        for i in range(len(ground_truth)):
            exec(
                "from executable_python_function import *"
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
    total_accuracy = 0
    for accuracy_dict in accuracy_dict_list:
        total_accuracy += accuracy_dict["accuracy"]

    if len(accuracy_dict_list) == 0:
        return {"accuracy": 0, "total_count": 0}

    return {"accuracy": total_accuracy / len(accuracy_dict_list), "total_count": 0}


def record_result(leaderboard_table, model_name, test_category, accuracy, total_count):
    if model_name not in leaderboard_table:
        leaderboard_table[model_name] = {}
    leaderboard_table[model_name][test_category] = {
        "accuracy": accuracy,
        "total_count": total_count,
    }


def record_cost_latency(leaderboard_table, model_name, model_output_data):
    if model_name not in leaderboard_table:
        leaderboard_table[model_name] = {}
        leaderboard_table[model_name]["cost"] = {"input_data": [], "output_data": []}
        leaderboard_table[model_name]["latency"] = {"data": []}

    input_token = []
    output_token = []
    latency = []
    for data in model_output_data:
        if "latency" in data:
            latency.append(data["latency"])
            if data["latency"] > 60:
                print("*" * 100)
                print(
                    f"❗️Warning: Latency for one of {model_name} response is {data['latency']}."
                )
                print("*" * 100)
        if "input_token_count" in data:
            if data["input_token_count"] != 0:
                input_token.append(data["input_token_count"])
        if "output_token_count" in data:
            if data["output_token_count"] != 0:
                output_token.append(data["output_token_count"])

    leaderboard_table[model_name]["cost"]["input_data"].extend(input_token)
    leaderboard_table[model_name]["cost"]["output_data"].extend(output_token)
    leaderboard_table[model_name]["latency"]["data"].extend(latency)


def get_metric(model_name, cost_data, latency_data):

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


def generate_leaderboard_csv(leaderboard_table, output_path):
    data = []
    for model_name, value in leaderboard_table.items():
        model_name_escaped = model_name.replace("_", "/")
        python_simple_ast = value.get("simple", {"accuracy": 0, "total_count": 0})
        python_multiple_ast = value.get(
            "multiple_function", {"accuracy": 0, "total_count": 0}
        )
        python_parallel_ast = value.get(
            "parallel_function", {"accuracy": 0, "total_count": 0}
        )
        python_parallel_multiple_ast = value.get(
            "parallel_multiple_function", {"accuracy": 0, "total_count": 0}
        )
        python_simple_exec = value.get(
            "executable_simple", {"accuracy": 0, "total_count": 0}
        )
        python_multiple_exec = value.get(
            "executable_multiple_function", {"accuracy": 0, "total_count": 0}
        )
        python_parallel_exec = value.get(
            "executable_parallel_function", {"accuracy": 0, "total_count": 0}
        )
        python_parallel_multiple_exec = value.get(
            "executable_parallel_multiple_function", {"accuracy": 0, "total_count": 0}
        )
        java_simple_ast = value.get("java", {"accuracy": 0, "total_count": 0})
        javascript_simple_ast = value.get(
            "javascript", {"accuracy": 0, "total_count": 0}
        )
        rest_simple_exec = value.get("rest", {"accuracy": 0, "total_count": 0})
        relevance = value.get("relevance", {"accuracy": 0, "total_count": 0})

        cost_data = value.get("cost", {"input_data": [], "output_data": []})
        latency_data = value.get("latency", {"data": []})

        simple_ast = calculate_weighted_accuracy(
            [python_simple_ast, java_simple_ast, javascript_simple_ast]
        )
        multiple_ast = python_multiple_ast
        parallel_ast = python_parallel_ast
        parallel_multiple_ast = python_parallel_multiple_ast
        simple_exec = calculate_weighted_accuracy(
            [python_simple_exec, rest_simple_exec]
        )
        multiple_exec = python_multiple_exec
        parallel_exec = python_parallel_exec
        parallel_multiple_exec = python_parallel_multiple_exec

        summary_ast = calculate_unweighted_accuracy(
            [simple_ast, multiple_ast, parallel_ast, parallel_multiple_ast]
        )
        summary_exec = calculate_unweighted_accuracy(
            [simple_exec, multiple_exec, parallel_exec, parallel_multiple_exec]
        )
        overall_accuracy = calculate_weighted_accuracy(
            [
                simple_ast,
                multiple_ast,
                parallel_ast,
                parallel_multiple_ast,
                simple_exec,
                multiple_exec,
                parallel_exec,
                parallel_multiple_exec,
                relevance,
            ]
        )

        cost, latency_mean, latency_std, percentile_95_latency = get_metric(
            model_name_escaped, cost_data, latency_data
        )

        if overall_accuracy["total_count"] != 1700:
            print("-" * 100)
            print(
                f"❗️Warning: Total count for {model_name} is {overall_accuracy['total_count']}"
            )

        data.append(
            [
                "N/A",
                overall_accuracy["accuracy"],
                MODEL_METADATA_MAPPING[model_name][0],
                MODEL_METADATA_MAPPING[model_name][1],
                MODEL_METADATA_MAPPING[model_name][2],
                MODEL_METADATA_MAPPING[model_name][3],
                summary_ast["accuracy"],
                summary_exec["accuracy"],
                simple_ast["accuracy"],
                python_simple_ast["accuracy"],
                java_simple_ast["accuracy"],
                javascript_simple_ast["accuracy"],
                multiple_ast["accuracy"],
                parallel_ast["accuracy"],
                parallel_multiple_ast["accuracy"],
                simple_exec["accuracy"],
                python_simple_exec["accuracy"],
                rest_simple_exec["accuracy"],
                multiple_exec["accuracy"],
                parallel_exec["accuracy"],
                parallel_multiple_exec["accuracy"],
                relevance["accuracy"],
                cost,
                latency_mean,
                latency_std,
                percentile_95_latency,
            ]
        )

    data.sort(key=lambda x: x[1], reverse=True)
    for i in range(len(data)):
        data[i][0] = str(i + 1)
        data[i][1] = "{:.2f}%".format(data[i][1] * 100)
        for j in range(6, len(data[i]) - 4):
            data[i][j] = "{:.2f}%".format(data[i][j] * 100)
        for j in range(len(data[i]) - 4, len(data[i])):
            data[i][j] = str(data[i][j])

    data.insert(0, COLUMNS)

    filepath = os.path.join(output_path, "data.csv")
    with open(filepath, "w") as f:
        for i, row in enumerate(data):
            if i < len(data) - 1:
                f.write(",".join(row) + "\n")
            else:
                f.write(",".join(row))


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
            test_category = model_score_json.split("_score.json")[0].split("/")[-1]
            if model_name not in leaderboard_table:
                leaderboard_table[model_name] = {}
            if test_category not in leaderboard_table[model_name]:
                leaderboard_table[model_name][test_category] = {
                    "accuracy": accuracy,
                    "total_count": total_count,
                }


def oss_file_formatter(input_file_path, output_dir):
    data = load_file(input_file_path)
    assert len(data) == 2000, "OSS result.json file should have 2000 entries."

    for key, value in FILENAME_INDEX_MAPPING.items():
        start, end = value
        output_file = os.path.join(
            output_dir, f"gorilla_openfunctions_v1_test_{key}_result.json"
        )
        with open(output_file, "w") as f:
            original_idx = 0
            for i in range(start, end + 1):
                new_json = {"id": original_idx, "result": data[i]["text"]}
                f.write(json.dumps(new_json) + "\n")
                original_idx += 1


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
