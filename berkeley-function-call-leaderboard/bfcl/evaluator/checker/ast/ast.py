import re
import json
from typing import List, Dict
from pathlib import Path

from bfcl.evaluator.checker.types import CheckerResult
from bfcl.types import LeaderboardAstCategory, Leaderboard
from bfcl.model_handler import constants
from bfcl.evaluator.checker.ast import type_converter, utils


class AstChecker:
    NESTED_CONVERSION_TYPE_LIST = ["Array", "ArrayList", "array"]
    PYTHON_TYPE_MAPPING = {
        "string": str,
        "integer": int,
        "float": float,
        "boolean": bool,
        "array": list,
        "tuple": list,
        "dict": dict,
        "any": str,
    }
    # This is the list of types that we need to recursively check its values
    PYTHON_NESTED_TYPE_CHECK_LIST = ["array", "tuple"]

    def __init__(self, model_name: str, leaderboard: Leaderboard) -> None:
        self.model_name = model_name
        self.leaderboard = leaderboard
        self.possible_ans_dir = Path(__file__, '../../../../..').resolve() / 'data/possible_answer'
        self.test_category_to_possible_ans = {}

    def load_possible_answers(self, test_category: LeaderboardAstCategory) -> None:
        if test_category not in self.test_category_to_possible_ans:
            file_name = self.leaderboard.get_file_name(test_category)
            with open(self.possible_ans_dir / file_name, 'r') as file:
                self.test_category_to_possible_ans[test_category] = [json.loads(line) for line in file]

    def __call__(
        self,
        idx: int,
        func_description, 
        model_output: List, 
        test_category: LeaderboardAstCategory, 
    ) -> CheckerResult:
        
        language = self.get_language(test_category)
        self.load_possible_answers(test_category)
        possible_answers = self.test_category_to_possible_ans[test_category][idx]

        if 'multiple' in test_category.value or 'parallel' in test_category.value:
            # Some formatting issues that needs to be handled
            if test_category == "parallel_function":
                func_description = [func_description]
            return self._parallel_function_no_order_checker(
                func_description, 
                model_output, 
                possible_answers,
                language,
            )
        else:
            if len(model_output) != 1:
                return CheckerResult(
                    is_valid=False,
                    error_type="simple_function_checker:wrong_count",
                    error_message="Wrong number of functions."
                )
            model_output = model_output[0]
            return self._simple_function_checker(
                func_description, 
                model_output, 
                possible_answers,
                language,
            )

    def _parallel_function_no_order_checker(
        self,
        func_descriptions: List,
        model_output: List,
        possible_answers: Dict,
        language: str,
    ) -> CheckerResult:
        
        if len(model_output) != len(possible_answers):
            return CheckerResult(
                is_valid=False,
                error_type='parallel_function_checker_no_order:wrong_count',
                error_message='Wrong number of functions.'
            )

        func_name_list = list(possible_answers.keys())
        possible_answers_list = [{key: value} for key, value in possible_answers.items()]
        matched_indices = []
        # We go throught the possible answers one by one, and eliminate the model output that matches the possible answer.
        # It must be this way because we need ground truth to fetch the correct function description.
        for i in range(len(possible_answers_list)):
            func_description = utils.find_description(func_descriptions, func_name_list[i])
            # This should not happen. As possible_answers is the ground truth, and it should have the correct function name.
            if func_description is None:
                return CheckerResult(
                    is_valid=False,
                    error_type='parallel_function_checker_no_order:cannot_find_description',
                    error_message=f"Function doc description not found for function name: {repr(func_name_list[i])}."
                )

            all_errors = []
            for index in range(len(model_output)):
                if index in matched_indices:
                    continue

                result = self._simple_function_checker(
                    func_description,
                    model_output[index],
                    possible_answers_list[i],
                    language,
                )
                if result.is_valid:
                    matched_indices.append(index)
                    break
                else:
                    all_errors.append(
                        {
                            f"Model Result Index {index}": {
                                "sub_error": result.error_message,
                                "sub_error_type": result.error_type,
                                "model_output_item": model_output[index],
                                "possible_answer_item": possible_answers_list[i],
                            }
                        }
                    )

            if not result.is_valid:
                considered_indices = [i for i in range(len(model_output)) if i not in matched_indices]
                error_message = (
                    f"Could not find a matching function among index {considered_indices} of model "
                    f"output for index {i} of possible answers."
                )
                error_message += "\nErrors:\n" + '\n'.join(map(json.dumps, all_errors))
                return CheckerResult(
                    is_valid=False,
                    error_type="parallel_function_checker_no_order:cannot_find_match",
                    error_message=error_message
                )

        return CheckerResult(is_valid=True, error_type='', error_message='')

    def _simple_function_checker(
        self,
        func_description: dict,
        model_output: dict,
        possible_answer: dict,
        language: str,
    ) -> CheckerResult:
        
        language = language.lower()
        possible_answer = list(possible_answer.values())[0]
        # Extract function name and parameters details
        func_name = func_description["name"]
        param_details = func_description["parameters"]["properties"]
        required_params = func_description["parameters"]["required"]

        result = CheckerResult(is_valid=True, error_type="simple_function_checker:unclear", error_message="")
        func_name = utils.convert_func_name(func_name, self.model_name)
        # Check if function name matches
        if func_name not in model_output:
            return CheckerResult(
                is_valid=False,
                error_type="simple_function_checker:wrong_func_name",
                error_message=f"Function name {repr(func_name)} not found in model output."
            )

        model_params = model_output[func_name]
        # Check for required parameters in model output
        for param in required_params:
            if param not in model_params:
                return CheckerResult(
                    is_valid=False,
                    error_type="simple_function_checker:missing_required",
                    error_message=f"Missing required parameter: {repr(param)}."
                )

        # Validate types and values for each parameter in model output
        for param, value in model_params.items():
            if param not in param_details or param not in possible_answer:
                return CheckerResult(
                    is_valid=False,
                    error_type="simple_function_checker:unexpected_param",
                    error_message=f"Unexpected parameter: {repr(param)}."
                )

            full_param_details = param_details[param]
            expected_type_description = full_param_details["type"]  # This is a string
            is_variable = False
            nested_type_converted = None

            if language == "java":
                expected_type_converted = constants.JAVA_TYPE_CONVERSION[expected_type_description]
                if expected_type_description in constants.JAVA_TYPE_CONVERSION:
                    if not isinstance(value, str):
                        return CheckerResult(
                            is_valid=False,
                            error_type="type_error:java",
                            error_message=f"Incorrect type for parameter {repr(param)}. Expected type String, got {type(value).__name__}. Parameter value: {repr(value)}."
                        )

                    if expected_type_description in self.NESTED_CONVERSION_TYPE_LIST:
                        nested_type = param_details[param]["items"]["type"]
                        nested_type_converted = constants.JAVA_TYPE_CONVERSION[nested_type]
                        value = type_converter.java.java_type_converter(value, expected_type_description, nested_type)
                    else:
                        value = type_converter.java.java_type_converter(value, expected_type_description)
            elif language == "javascript":
                expected_type_converted = constants.JS_TYPE_CONVERSION[expected_type_description]
                if expected_type_description in constants.JS_TYPE_CONVERSION:
                    if not isinstance(value, str):
                        return CheckerResult(
                            is_valid=False,
                            error_type="type_error:js",
                            error_message=f"Incorrect type for parameter {repr(param)}. Expected type String, got {type(value).__name__}. Parameter value: {repr(value)}."
                        )

                    if expected_type_description in self.NESTED_CONVERSION_TYPE_LIST:
                        nested_type = param_details[param]["items"]["type"]
                        nested_type_converted = constants.JS_TYPE_CONVERSION[nested_type]
                        value = type_converter.javascript.js_type_converter(value, expected_type_description, nested_type)
                    else:
                        value = type_converter.javascript.js_type_converter(value, expected_type_description)
            elif language == "python":
                expected_type_converted = self.PYTHON_TYPE_MAPPING[expected_type_description]
                if expected_type_description in self.PYTHON_NESTED_TYPE_CHECK_LIST:
                    nested_type = param_details[param]["items"]["type"]
                    nested_type_converted = self.PYTHON_TYPE_MAPPING[nested_type]

            # We convert all tuple value to list when the expected type is tuple.
            # The conversion is necessary because any tuple in the possible answer would become a list after being processed through json.dump() and json.load().
            # This does introduce some false positive (eg, when the model provides a list value instead of tuple). We hope to find a better solution in the future.
            if expected_type_description == "tuple" and type(value) == tuple:
                value = list(value)

            # Allow python auto conversion from int to float
            if (
                language == "python"
                and expected_type_description == "float"
                and type(value) == int
            ):
                value = float(value)

            # Type checking
            # In fact, we only check for Python here.
            # Type check for other languages are handled by the type converter, and so their value (after conversion) is always correct.
            type_check_result = AstChecker.type_checker(
                param,
                value,
                possible_answer[param],
                expected_type_description,
                expected_type_converted,
                nested_type_converted,
            )
            if not type_check_result.is_valid:
                return type_check_result
            is_variable = type_check_result.is_variable

            # It doesn't make sense to special handle dictionaries and list of dictionaries if the value is a variable.
            # We can just treat the variable as a string and use the normal flow.
            if not is_variable:
                # Special handle for dictionaries
                if expected_type_converted == dict:
                    result = AstChecker.dict_checker(param, value, possible_answer[param])
                    if not result.is_valid:
                        return result
                    continue

                # Special handle for list of dictionaries
                elif expected_type_converted == list and nested_type_converted == dict:
                    result = AstChecker.list_dict_checker(param, value, possible_answer[param])
                    if not result.is_valid:
                        return result
                    continue

                # Special handle for strings
                elif expected_type_converted == str:
                    # We don't check for case sensitivity for string, as long as it's not a variable
                    result = AstChecker.string_checker(param, value, possible_answer[param])
                    if not result.is_valid:
                        return result
                    continue

                elif expected_type_converted == list:
                    result = AstChecker.list_checker(param, value, possible_answer[param])
                    if not result.is_valid:
                        return result
                    continue

            # Check if the value is within the possible answers
            if value not in possible_answer[param]:
                result.is_valid = False
                result.error_message = (
                    f"Invalid value for parameter {repr(param)}: {repr(value)}. Expected one of {possible_answer[param]}."
                )
                result.error_type = "value_error:others"
                return result

        # Check for optional parameters not provided but allowed
        for param in possible_answer:
            if param not in model_params and "" not in possible_answer[param]:
                result.is_valid = False
                result.error_message = f"Optional parameter {repr(param)} not provided and not marked as optional."
                result.error_type = "simple_function_checker:missing_optional"
                return result

        return result

    @staticmethod
    def type_checker(
        param: str,
        value,
        possible_answer: List,
        expected_type_description: str,
        expected_type_converted,
        nested_type_converted,
    ) -> CheckerResult:
        # NOTE: This type checker only supports nested type checking for one level deep.
        # We didn't implement recursive type checking for nested types, as it's not needed for 
        # the current use case and it's very complex.

        result = CheckerResult(
            is_valid=True, 
            error_type="type_error:simple", 
            error_message='', 
            is_variable=True
        )
        is_variable = False
        # check for the case where a variable is used instead of a actual value.
        # use the type in possible_answer as the expected type
        possible_answer_type = utils.get_possible_answer_type(possible_answer)
        # if possible_answer only contains optional parameters, we can't determine the type
        if possible_answer_type != None:
            # we are being precise here.
            # in fact, possible_answer_type should always be string, as that's how we treat varibale in possible_answer
            if possible_answer_type != expected_type_converted:
                is_variable = True

        # value is the same type as in function description
        if type(value) == expected_type_converted:
            # We don't need to do recursive check for simple types
            if nested_type_converted == None:
                result.is_variable = is_variable
                return result
            else:
                for possible_answer_item in possible_answer:
                    flag = True  # Each parameter should match to at least one possible answer type.
                    # Here, we assume that each item should be the same type. We could also relax it.
                    if type(possible_answer_item) == list:
                        for value_item in value:
                            checker_result = AstChecker.type_checker(
                                param,
                                value_item,
                                possible_answer_item,
                                str(nested_type_converted),
                                nested_type_converted,
                                None,
                            )
                            if not checker_result.is_valid:
                                flag = False
                                break

                    if flag:
                        return CheckerResult(
                            is_valid=True, 
                            error_type='', 
                            error_message='', 
                            is_variable=is_variable
                        )

                result.is_valid = False
                result.error_type = "type_error:nested"
                result.error_message = (
                    f"Nested type checking failed for parameter {repr(param)}. "
                    f'Expected outer type {expected_type_description} with inner type '
                    f'{str(nested_type_converted)}. Parameter value: {repr(value)}.'
                )

        # value is not as expected, check for the case where a variable is used instead of a actual value
        # use the type in possible_answer as the expected type
        possible_answer_type = utils.get_possible_answer_type(possible_answer)
        # if possible_answer only contains optional parameters, we can't determine the type
        if possible_answer_type is not None:
            # we are being precise here.
            # in fact, possible_answer_type should always be string, as that's how we treat varibale in possible_answer
            if type(value) == possible_answer_type:
                result.is_variable = True
                return result

        return CheckerResult(
            is_valid=False, 
            error_type='type_error:simple', 
            error_message=f"Incorrect type for parameter {repr(param)}. Expected type {expected_type_description}, got {type(value).__name__}. Parameter value: {repr(value)}."
        )
    
    def string_checker(param: str, model_output: str, possible_answer: List) -> CheckerResult:
        standardize_possible_answer = []
        standardize_model_output = AstChecker.standardize_string(model_output)
        for i in range(len(possible_answer)):
            if type(possible_answer[i]) == str:
                standardize_possible_answer.append(AstChecker.standardize_string(possible_answer[i]))

        if standardize_model_output not in standardize_possible_answer:
            return CheckerResult(
                is_valid=False,
                error_type="value_error:string",
                error_message=f"Invalid value for parameter {repr(param)}: {repr(model_output)}. Expected one of {possible_answer}. Case insensitive."
            )
        
        return CheckerResult(is_valid=True, error_type='', error_message='',)

    @staticmethod
    def list_checker(param: str, model_output: List, possible_answer: List) -> CheckerResult:
        # Convert the tuple to a list
        standardize_model_output = list(model_output)

        # If the element in the list is a string, we need to standardize it
        for i in range(len(standardize_model_output)):
            if type(standardize_model_output[i]) == str:
                standardize_model_output[i] = AstChecker.standardize_string(model_output[i])

        standardize_possible_answer = []
        # We also need to standardize the possible answers
        for i in range(len(possible_answer)):
            standardize_possible_answer.append([])
            for j in range(len(possible_answer[i])):
                if type(possible_answer[i][j]) == str:
                    standardize_possible_answer[i].append(AstChecker.standardize_string(possible_answer[i][j]))
                else:
                    standardize_possible_answer[i].append(possible_answer[i][j])

        if standardize_model_output not in standardize_possible_answer:
            return CheckerResult(
                is_valid=False,
                error_type="value_error:list/tuple",
                error_message=f"Invalid value for parameter {repr(param)}: {repr(model_output)}. Expected one of {possible_answer}."
            )

        return CheckerResult(is_valid=True, error_type='', error_message='')

    @staticmethod
    def dict_checker(param: str, model_output: Dict, possible_answers: List) -> CheckerResult:
        # This function works for simple dictionaries, as well as dictionaries with nested dictionaries
        result = CheckerResult(is_valid=False, error_type='dict_checker:unclear', error_message='')
        for i in range(len(possible_answers)):
            if possible_answers[i] == "":
                continue

            result = CheckerResult(is_valid=False, error_type='dict_checker:unclear', error_message='')
            flag = True
            possible_answer = possible_answers[i]
            # possible_answer is a single dictionary
            if len(model_output.keys()) != len(possible_answer.keys()):
                result.is_valid = False
                result.error_message = "Wrong number of parameters for dictionary."
                result.error_type = "value_error:dict_items"
                flag = False
                continue

            for key, value in model_output.items():
                if key not in possible_answer:
                    result.is_valid = False
                    result.error_message = f"Unexpected parameter: '{key}'."
                    result.error_type = "value_error:dict_key"
                    flag = False
                    break

                expected_values = possible_answer[key]
                if isinstance(expected_values, dict):
                    result = AstChecker.dict_checker(param, value, [expected_values])
                    if not result.is_valid:
                        flag = False
                        break
                else:
                    standardize_value = value
                    # If the value is a string, we need to standardize it
                    if type(value) == str:
                        standardize_value = AstChecker.standardize_string(value)
                    # We also need to standardize the possible answers
                    standardize_possible_answer = []
                    for i in range(len(possible_answer[key])):
                        if type(possible_answer[key][i]) == str:
                            standardize_possible_answer.append(
                                AstChecker.standardize_string(possible_answer[key][i])
                            )
                        else:
                            standardize_possible_answer.append(possible_answer[key][i])

                    if standardize_value not in standardize_possible_answer:
                        result.is_valid = False
                        result.error_message = f"Invalid value for parameter {repr(key)}: {repr(value)}. Expected one of {standardize_possible_answer}."
                        result.error_type = "value_error:dict_value"
                        flag = False
                        break
            if flag:
                return CheckerResult(is_valid=True, error_type='', error_message='')

        return result

    @staticmethod
    def list_dict_checker(param: str, model_output: List, possible_answers: List) -> CheckerResult:
        # This function takes in a list of dictionaries and checks if each dictionary is valid
        # The order of the dictionaries in the list must match the order of the possible answers
        result = CheckerResult(is_valid=False, error_type='list_dict_checker:unclear', error_message='')
        for answer_index in range(len(possible_answers)):
            flag = True  # True means so far, all dictionaries are valid

            # Only proceed if the number of dictionaries in the list matches the number of dictionaries in the possible answers
            if len(model_output) != len(possible_answers[answer_index]):
                result.is_valid = False
                result.error_message = "Wrong number of dictionaries in the list."
                result.error_type = "value_error:list_dict_count"
                flag = False
                continue

            for dict_index in range(len(model_output)):
                result = AstChecker.dict_checker(
                    param,
                    model_output[dict_index],
                    [possible_answers[answer_index][dict_index]],
                )
                if not result.is_valid:
                    flag = False
                    break
            if flag:
                return CheckerResult(is_valid=True, error_type='', error_message='')

        return result
    
    @staticmethod
    def standardize_string(input_string: str):
        # This function standardizes the string by removing all the spaces, ",./-_*^" punctuation, and converting it to lowercase
        # It will also convert all the single quotes to double quotes
        # This is used to compare the model output with the possible answers
        # We don't want to punish model for answer like April 1, 2024 vs April 1,2024, vs April 1 2024
        regex_string = r"[ \,\.\/\-\_\*\^]"
        return re.sub(regex_string, "", input_string).lower().replace("'", '"')

    @staticmethod
    def get_language(test_category: LeaderboardAstCategory) -> str:
        if test_category.value == LeaderboardAstCategory.JAVA.value:
            language = 'java'
        elif test_category.value == LeaderboardAstCategory.JAVASCRIPT.value:
            language = 'javascript'
        else:
            language = 'python'
        return language