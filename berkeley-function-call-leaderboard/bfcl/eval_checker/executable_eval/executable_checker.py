import json
import time
from functools import lru_cache

import requests  # Do not remove this import even though it seems to be unused. It's used in the executable_checker_rest function.
from bfcl.eval_checker.constant import (
    REAL_TIME_MATCH_ALLOWED_DIFFERENCE,
    REST_EVAL_GROUND_TRUTH_PATH,
)
from bfcl.eval_checker.executable_eval.custom_exception import NoAPIKeyError

# Load the ground truth data for the `rest` test category
@lru_cache(maxsize=1)  # cache the result, effectively loading data once
def load_eval_ground_truth():
    with open(REST_EVAL_GROUND_TRUTH_PATH, "r") as f:
        return f.readlines()

#### Main function ####
def executable_checker_rest(func_call, idx):
    EVAL_GROUND_TRUTH = load_eval_ground_truth()
    
    if "https://geocode.maps.co" in func_call:
        time.sleep(2)
    if "requests_get" in func_call:
        func_call = func_call.replace("requests_get", "requests.get")
    try:
        response = eval(func_call)
    except Exception as e:
        return {
            "valid": False,
            "error": [f"Execution failed. {str(e)}"],
            "error_type": "executable_checker_rest:execution_error",
        }

    try:
        if response.status_code == 200:

            eval_GT_json = json.loads(EVAL_GROUND_TRUTH[idx])
            try:
                if isinstance(eval_GT_json, dict):
                    if isinstance(response.json(), dict):
                        if set(eval_GT_json.keys()) == set(response.json().keys()):
                            return {"valid": True, "error": [], "error_type": ""}
                        return {
                            "valid": False,
                            "error": ["Key inconsistency"],
                            "error_type": "executable_checker_rest:wrong_key",
                        }
                    return {
                        "valid": False,
                        "error": [
                            f"Expected dictionary, but got {type(response.json())}"
                        ],
                        "error_type": "executable_checker_rest:wrong_type",
                    }

                elif isinstance(eval_GT_json, list):
                    if isinstance(response.json(), list):
                        if len(eval_GT_json) != len(response.json()):
                            return {
                                "valid": False,
                                "error": [f"Response list length inconsistency."],
                                "error_type": "value_error:exec_result_rest_count",
                            }

                        else:
                            for i in range(len(eval_GT_json)):
                                if set(eval_GT_json[i].keys()) != set(
                                    response.json()[i].keys()
                                ):
                                    return {
                                        "valid": False,
                                        "error": [f"Key inconsistency"],
                                        "error_type": "executable_checker_rest:wrong_key",
                                    }

                            return {"valid": True, "error": []}
                    else:
                        return {
                            "valid": False,
                            "error": [
                                f"Expected list, but got {type(response.json())}"
                            ],
                            "error_type": "executable_checker_rest:wrong_type",
                        }
                return {
                    "valid": False,
                    "error": [
                        f"Expected dict or list, but got {type(response.json())}"
                    ],
                    "error_type": "executable_checker_rest:wrong_type",
                }
            except Exception as e:
                return {
                    "valid": False,
                    "error": [
                        f"Error in execution and type checking. Status code: {response.status_code}. Error: {str(e)}"
                    ],
                    "error_type": "executable_checker_rest:response_format_error",
                }
        else:
            return {
                "valid": False,
                "error": [
                    f"Execution result status code is not 200, got {response.status_code}"
                ],
                "error_type": "executable_checker_rest:wrong_status_code",
            }
    except Exception as e:
        return {
            "valid": False,
            "error": [f"Cannot get status code of the response. Error: {str(e)}"],
            "error_type": "executable_checker_rest:cannot_get_status_code",
        }


def executable_checker_non_rest(decoded_result: list, func_description: dict, test_category: str):
    if "multiple" in test_category or "parallel" in test_category:
        return executable_checker_parallel_no_order(
            decoded_result,
            func_description["execution_result"],
            func_description["execution_result_type"],
        )

    else:
        if len(decoded_result) != 1:
            return {
                "valid": False,
                "error": ["Wrong number of functions."],
                "error_type": "simple_exec_checker:wrong_count",
            }
        return executable_checker_simple(
            decoded_result[0],
            func_description["execution_result"][0],
            func_description["execution_result_type"][0],
            False,
        )


#### Helper functions for Exec ####
def patten_matcher(exec_output, expected_result, function_call, is_sanity_check):
    result = {"valid": True, "error": [], "error_type": "executable_checker:unclear"}

    if type(exec_output) != type(expected_result):
        return {
            "valid": False,
            "error": [
                f"Wrong execution result type for {repr(function_call)}. Expected type: {type(expected_result)}, but got: {type(exec_output)}."
            ],
            "error_type": "executable_checker:wrong_result_type",
            "model_executed_output": exec_output,
        }
    if type(exec_output) == dict:
        # We loose the requirement for the sanity check as the expected result used in the sanity check might not be the most up-to-date one.
        # This happens when the key is a timestamp or a random number.
        if is_sanity_check:
            if len(exec_output) != len(expected_result):
                return {
                    "valid": False,
                    "error": [
                        f"Wrong execution result pattern for {repr(function_call)}. Expect type Dict, but wrong number of elements in the output. Expected length: {len(expected_result)}, but got: {len(exec_output)}."
                    ],
                    "error_type": "executable_checker:wrong_result_type:dict_length",
                    "model_executed_output": exec_output,
                }
            else:
                return result

        for key, value in expected_result.items():
            if key not in exec_output:
                return {
                    "valid": False,
                    "error": [
                        f"Wrong execution result pattern for {repr(function_call)}. Expect type Dict, but key {repr(key)} not found in the model output."
                    ],
                    "error_type": "executable_checker:wrong_result_type:dict_key_not_found",
                    "model_executed_output": exec_output,
                }
        for key, value in exec_output.items():
            if key not in expected_result:
                return {
                    "valid": False,
                    "error": [
                        f"Wrong execution result pattern for {repr(function_call)}. Expect type Dict, but key {repr(key)} not expected in the model output."
                    ],
                    "error_type": "executable_checker:wrong_result_type:dict_extra_key",
                    "model_executed_output": exec_output,
                }
    if type(exec_output) == list:
        if len(exec_output) != len(expected_result):
            return {
                "valid": False,
                "error": [
                    f"Wrong execution result pattern for {repr(function_call)}. Expect type list, but wrong number of elements in the output. Expected length: {len(expected_result)}, but got: {len(exec_output)}."
                ],
                "error_type": "executable_checker:wrong_result_type:list_length",
                "model_executed_output": exec_output,
            }
    return result


def executable_checker_simple(
    function_call: str,
    expected_result,
    expected_result_type: str,
    is_sanity_check=False,
):
    result = {"valid": True, "error": [], "error_type": "executable_checker:unclear"}

    exec_dict = {}

    try:
        exec(
            "from bfcl.eval_checker.executable_eval.data.executable_python_function import *" + "\nresult=" + function_call,
            exec_dict,
        )
        exec_output = exec_dict["result"]
    except NoAPIKeyError as e:
        raise e
    except Exception as e:
        result["valid"] = False
        result["error"].append(
            f"Error in execution: {repr(function_call)}. Error: {str(e)}"
        )
        result["error_type"] = "executable_checker:execution_error"
        return result

    # We need to special handle the case where the execution result is a tuple and convert it to a list
    # Because when json is stored, the tuple is converted to a list, and so the expected result is a list when loaded from json
    if isinstance(exec_output, tuple):
        exec_output = list(exec_output)

    if expected_result_type == "exact_match":
        if exec_output != expected_result:
            result["valid"] = False
            result["error"].append(
                f"Wrong execution result for {repr(function_call)}. Expected: {expected_result}, but got: {exec_output}."
            )
            result["error_type"] = "executable_checker:wrong_result"
            result["model_executed_output"] = exec_output
            return result

    elif expected_result_type == "real_time_match":
        # Allow for 5% difference
        if (type(expected_result) == float or type(expected_result) == int) and (
            type(exec_output) == float or type(exec_output) == int
        ):
            if not (
                expected_result * (1 - REAL_TIME_MATCH_ALLOWED_DIFFERENCE)
                <= exec_output
                <= expected_result * (1 + REAL_TIME_MATCH_ALLOWED_DIFFERENCE)
            ):
                result["valid"] = False
                result["error"].append(
                    f"Wrong execution result for {repr(function_call)}. Expected: {expected_result}, but got: {exec_output}. {REAL_TIME_MATCH_ALLOWED_DIFFERENCE * 100}% difference allowed."
                )
                result["error_type"] = "executable_checker:wrong_result_real_time"
                result["model_executed_output"] = exec_output
                return result
        else:
            result["valid"] = False
            result["error"].append(
                f"Wrong execution result for {repr(function_call)}. Expected: {expected_result}, but got: {exec_output}. Type needs to be float or int for real time match criteria."
            )
            result["error_type"] = "executable_checker:wrong_result_real_time"
            result["model_executed_output"] = exec_output
            return result

    else:
        # structural match
        pattern_match_result = patten_matcher(
            exec_output, expected_result, function_call, is_sanity_check
        )
        if not pattern_match_result["valid"]:
            return pattern_match_result

    return result


def executable_checker_parallel_no_order(
    decoded_result: list, expected_exec_result: list, expected_exec_result_type: list
):

    if len(decoded_result) != len(expected_exec_result):
        return {
            "valid": False,
            "error": [
                f"Wrong number of functions provided. Expected {len(expected_exec_result)}, but got {len(decoded_result)}."
            ],
            "error_type": "value_error:exec_result_count",
        }

    matched_indices = []
    for i in range(len(expected_exec_result)):
        all_errors = []
        for index in range(len(decoded_result)):
            if index in matched_indices:
                continue

            result = executable_checker_simple(
                decoded_result[index],
                expected_exec_result[i],
                expected_exec_result_type[i],
                False,
            )

            if result["valid"]:
                matched_indices.append(index)
                break
            else:
                all_errors.append(
                    {
                        f"Model Result Index {index}": {
                            "sub_error": result["error"],
                            "sub_error_type": result["error_type"],
                            "model_executed_output": (
                                result["model_executed_output"]
                                if "model_executed_output" in result
                                else None
                            ),
                        }
                    }
                )

        if not result["valid"]:
            considered_indices = [
                i for i in range(len(decoded_result)) if i not in matched_indices
            ]
            all_errors.insert(
                0,
                f"Could not find a matching function among index {considered_indices} of model output for index {i} of possible answers.",
            )
            return {
                "valid": False,
                "error": all_errors,
                "error_type": "executable_checker:cannot_find_match",
            }

    return {"valid": True, "error": [], "error_type": "executable_checker:unclear"}
