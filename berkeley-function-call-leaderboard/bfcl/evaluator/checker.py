import os
import time
import json
from pathlib import Path
from typing import Dict, List

from tqdm import tqdm

from bfcl.types import LeaderboardExecutableCategory
from bfcl.evaluator.utils import display_api_status_error
from bfcl.evaluator.exceptions import BadAPIStatusError, NoAPIKeyError


class ExecutableChecker:
    REAL_TIME_MATCH_ALLOWED_DIFFERENCE = 0.2

    def __init__(self, cache_dir: str) -> None:
        self.cache_dir = cache_dir
        self.data_dir = Path(__file__, '..', '..', '..').resolve() / 'data'
        self.rest_api_ground_truth_file_path = self.data_dir / 'api_status_check_ground_truth_REST.jsonl'
        self.rest_eval_response_v5_file_path = self.data_dir / 'rest-eval-response_v5.jsonl'
        with open(self.rest_eval_response_v5_file_path, 'r') as file:
            self.rest_eval_response_data = [json.loads(line) for line in file]
        self.executable_ground_truth_file_path = self.data_dir / 'api_status_check_ground_truth_executable.jsonl'

    def perform_api_sanity_checks(self) -> None:
        print("---- Sanity checking API status ----")
        try:
            self.rest_api_status_sanity_check()
        except BadAPIStatusError as e:
            API_STATUS_ERROR_REST = e
        try:
            self.executable_api_status_sanity_check()
        except BadAPIStatusError as e:
            API_STATUS_ERROR_EXECUTABLE = e 
        display_api_status_error(API_STATUS_ERROR_REST, API_STATUS_ERROR_EXECUTABLE, display_success=True)

    def rest_api_status_sanity_check(self) -> None:
        # Use the ground truth data to make sure the API is working correctly
        ground_truth_replaced = self._get_updated_rest_ground_truth_data()
        correct_count = 0
        errors = []
        for idx, data in tqdm(
            enumerate(ground_truth_replaced),
            total=len(ground_truth_replaced),
            desc="API Status Test (REST)",
        ):
            status = self.rest_executable_checker(data["ground_truth"], self.rest_eval_response_data[idx])
            if status["valid"]:
                correct_count += 1
            else:
                errors.append((data, status))

        if correct_count != len(ground_truth_replaced):
            raise BadAPIStatusError(errors, f"{len(ground_truth_replaced) - correct_count} / {len(ground_truth_replaced)}")

    def executable_api_status_sanity_check(self) -> None:
        with open(self.executable_ground_truth_file_path, 'r') as file:
            ground_truth = [json.loads(line) for line in file]
        correct_count = 0
        errors = []
        for data in tqdm(ground_truth, total=len(ground_truth), desc="API Status Test (Non-REST)"):
            status = self._simple_executable_checker(
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

    def executable_checker(
        self, 
        decoded_result: List, 
        func_description: Dict, 
        test_category: LeaderboardExecutableCategory
    ):
        if 'multiple' in test_category.value or 'parallel' in test_category.value:
            return self._parallel_no_order_executable_checker(
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
            return self._simple_executable_checker(
                decoded_result[0],
                func_description["execution_result"][0],
                func_description["execution_result_type"][0],
                False,
            )

    def _get_updated_rest_ground_truth_data(self) -> List[Dict]:
        output_file_path = self.cache_dir / self.rest_api_ground_truth_file_path.name
        # Avoid loading the output file from the cache, since the api keys might change

        placeholders = {}
        env_vars = ('GEOCODE_API_KEY', 'RAPID_API_KEY', 'OMDB_API_KEY', 'EXCHANGERATE_API_KEY')
        for var in env_vars:
            assert (api_key := os.getenv(var)), f'Please provide your {var} in the `.env` file.'
            placeholders['YOUR-' + var.replace('_', '-')] = api_key
        print("All API keys are present.")

        def replace_placeholders(data):
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, (dict, list)):
                        replace_placeholders(value)
                    elif isinstance(value, str):
                        for placeholder, actual_value in placeholders.items():
                            if placeholder in value:  # Check if placeholder is in the string
                                data[key] = value.replace(placeholder, actual_value)
            elif isinstance(data, list):
                for idx, item in enumerate(data):
                    if isinstance(item, (dict, list)):
                        replace_placeholders(item)
                    elif isinstance(item, str):
                        for placeholder, actual_value in placeholders.items():
                            if placeholder in item:  # Check if placeholder is in the string
                                data[idx] = item.replace(placeholder, actual_value)
            return data
        
        modified_data = []
        with open(self.rest_api_ground_truth_file_path, 'r') as file:
            for line in file:
                try:
                    data = replace_placeholders(json.loads(line))
                    modified_data.append(data)
                except json.JSONDecodeError:
                    # Handle the case where a line is not a valid JSON object
                    print('Invalid JSON line!')
        
        with open(output_file_path, 'w') as f:
            for modified_line in modified_data:
                f.write(json.dumps(modified_line) + '\n')
        print(f'Saved REST API ground truth file with replaced placeholders at {output_file_path} 🦍.')

        return modified_data

    def rest_executable_checker(self, func_call, eval_ground_truth):
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
            if response.status_code != 200:
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
        try:
            if isinstance(eval_ground_truth, dict):
                if isinstance(response.json(), dict):
                    if set(eval_ground_truth.keys()) == set(response.json().keys()):
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

            elif isinstance(eval_ground_truth, list):
                if isinstance(response.json(), list):
                    if len(eval_ground_truth) != len(response.json()):
                        return {
                            "valid": False,
                            "error": [f"Response list length inconsistency."],
                            "error_type": "value_error:exec_result_rest_count",
                        }

                    else:
                        for i in range(len(eval_ground_truth)):
                            if set(eval_ground_truth[i].keys()) != set(
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
    
    def _simple_executable_checker(
        self,
        function_call: str,
        expected_result,
        expected_result_type: str,
        is_sanity_check=False,
    ):
        result = {"valid": True, "error": [], "error_type": "executable_checker:unclear"}

        exec_dict = {}

        try:
            exec(
                "from bfcl.evaluator.exec_python_functions import *" + "\nresult=" + function_call,
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
                    expected_result * (1 - ExecutableChecker.REAL_TIME_MATCH_ALLOWED_DIFFERENCE)
                    <= exec_output
                    <= expected_result * (1 + ExecutableChecker.REAL_TIME_MATCH_ALLOWED_DIFFERENCE)
                ):
                    result["valid"] = False
                    result["error"].append(
                        f"Wrong execution result for {repr(function_call)}. Expected: {expected_result}, "
                        f"but got: {exec_output}. {ExecutableChecker.REAL_TIME_MATCH_ALLOWED_DIFFERENCE * 100}% difference allowed."
                    )
                    result["error_type"] = "executable_checker:wrong_result_real_time"
                    result["model_executed_output"] = exec_output
                    return result
            else:
                result["valid"] = False
                result["error"].append(
                    f"Wrong execution result for {repr(function_call)}. Expected: {expected_result}, "
                    f"but got: {exec_output}. Type needs to be float or int for real time match criteria."
                )
                result["error_type"] = "executable_checker:wrong_result_real_time"
                result["model_executed_output"] = exec_output
                return result

        else:
            # Structural match
            pattern_match_result = self._pattern_matcher(exec_output, expected_result, function_call, is_sanity_check)
            if not pattern_match_result["valid"]:
                return pattern_match_result

        return result
    
    def _parallel_no_order_executable_checker(
        self, 
        decoded_result: List, 
        expected_exec_result: List, 
        expected_exec_result_type: List
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

                result = self._simple_executable_checker(
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
                    f"Could not find a matching function among index {considered_indices} of model " \
                    "output for index {i} of possible answers.",
                )
                return {
                    "valid": False,
                    "error": all_errors,
                    "error_type": "executable_checker:cannot_find_match",
                }

        return {"valid": True, "error": [], "error_type": "executable_checker:unclear"}

    @staticmethod
    def _pattern_matcher(exec_output, expected_result, function_call, is_sanity_check):
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