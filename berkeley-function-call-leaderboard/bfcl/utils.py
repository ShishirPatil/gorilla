import json
import os
import re
from pathlib import Path
from typing import Union, Any

from bfcl.constants.category_mapping import TEST_COLLECTION_MAPPING, TEST_FILE_MAPPING, VERSION_PREFIX


def extract_test_category(input_string: Union[str, Path]) -> str:
    """
    Extracts the test category from a given input string or Path. The input string should contain a version prefix followed by the test category name.
    
    Args:
        input_string (`Union[str, Path]`):
            The input string or Path to extract the test category from.
    
    Returns:
        `str`: The extracted test category.
    
    Raises:
        `ValueError`: If the test category cannot be extracted from the input string.
    """
    input_string = str(input_string)
    pattern = rf".*{VERSION_PREFIX}_(\w+?)(?:_unused)?(?:_score|_result)?\.json"
    match = re.search(pattern, input_string)

    # Check if there's a match and extract the captured group
    if match:
        return match.group(1)  # the first captured group (\w+)
    else:
        raise ValueError(
            f"Could not extract the test category from the input string: {input_string}"
        )


def extract_test_category_from_id(test_entry_id: str) -> str:
    """
    Extracts the test category from a test entry ID by splitting on the last underscore.
    
    Args:
        test_entry_id (`str`):
            The test entry ID to extract the category from.
    
    Returns:
        `str`: The test category extracted from the ID.
    """
    return test_entry_id.rsplit("_", 1)[0]


def find_file_with_suffix(folder_path: Path, suffix: str) -> Path:
    """
    Finds a JSON file in the specified folder that matches the given suffix.
    
    Args:
        folder_path (`Path`):
            The folder to search for the JSON file.
        suffix (`str`):
            The suffix to match against the test category of files.
    
    Returns:
        `Path`: The path to the matching JSON file.
    
    Raises:
        `FileNotFoundError`: If no matching JSON file is found.
    """
    for json_file in folder_path.glob("*.json"):
        if extract_test_category(json_file) == suffix:
            return json_file
    raise FileNotFoundError(f"No JSON file found with suffix: {suffix}")


def is_multi_turn(test_category: str) -> bool:
    """
    Checks if a test category is for multi-turn tests.
    
    Args:
        test_category (`str`):
            The test category to check.
    
    Returns:
        `bool`: True if the test category is for multi-turn tests, False otherwise.
    """
    return "multi_turn" in test_category


def contain_multi_turn_irrelevance(test_category: str) -> bool:
    """
    Checks if a test category contains multi-turn irrelevance tests.
    
    Args:
        test_category (`str`):
            The test category to check.
    
    Returns:
        `bool`: True if the test category contains multi-turn irrelevance tests, False otherwise.
    """
    return "miss_func" in test_category or "miss_param" in test_category


def is_executable(test_category: str) -> bool:
    """
    Checks if a test category is for executable tests.
    
    Args:
        test_category (`str`):
            The test category to check.
    
    Returns:
        `bool`: True if the test category is for executable tests, False otherwise.
    """
    return "exec" in test_category or "rest" in test_category


def is_rest(test_category: str) -> bool:
    """
    Checks if a test category is for REST API tests.
    
    Args:
        test_category (`str`):
            The test category to check.
    
    Returns:
        `bool`: True if the test category is for REST API tests, False otherwise.
    """
    return "rest" in test_category


def is_relevance_or_irrelevance(test_category: str) -> bool:
    """
    Checks if a test category is for relevance or irrelevance tests.
    
    Args:
        test_category (`str`):
            The test category to check.
    
    Returns:
        `bool`: True if the test category is for relevance or irrelevance tests, False otherwise.
    """
    return "relevance" in test_category or "irrelevance" in test_category


def is_chatable(test_category: str) -> bool:
    """
    Checks if a test category is for chat-based tests.
    
    Args:
        test_category (`str`):
            The test category to check.
    
    Returns:
        `bool`: True if the test category is for chat-based tests, False otherwise.
    """
    return "chatable" in test_category


def is_java(test_category: str) -> bool:
    """
    Checks if a test category is for Java tests.
    
    Args:
        test_category (`str`):
            The test category to check.
    
    Returns:
        `bool`: True if the test category is for Java tests, False otherwise.
    """
    return "java" in test_category


def is_js(test_category: str) -> bool:
    """
    Checks if a test category is for JavaScript tests.
    
    Args:
        test_category (`str`):
            The test category to check.
    
    Returns:
        `bool`: True if the test category is for JavaScript tests, False otherwise.
    """
    return "javascript" in test_category


def is_sql(test_category: str) -> bool:
    """
    Checks if a test category is for SQL tests.
    
    Args:
        test_category (`str`):
            The test category to check.
    
    Returns:
        `bool`: True if the test category is for SQL tests, False otherwise.
    """
    return "sql" in test_category


def load_file(file_path: Union[str, Path], sort_by_id: bool=False) -> list[dict]:
    """
    Loads a file containing JSON objects, one per line, and returns them as a list of dictionaries.
    
    Args:
        file_path (`Union[str, Path]`):
            The path to the file to load.
        sort_by_id (`bool`, optional):
            Whether to sort the entries by their ID. Defaults to False.
    
    Returns:
        `list[dict]`: A list of dictionaries loaded from the file.
    """
    result = []
    with open(file_path) as f:
        file = f.readlines()
        for line in file:
            result.append(json.loads(line))

    if sort_by_id:
        result.sort(key=sort_key)
    return result


def write_list_of_dicts_to_file(filename: str, data: list[dict], subdir: Optional[str]=None) -> None:
    """
    Writes a list of dictionaries to a file in JSON format, one dictionary per line.
    
    Args:
        filename (`str`):
            The name of the file to write to.
        data (`list[dict]`):
            The list of dictionaries to write.
        subdir (`Optional[str]`, optional):
            A subdirectory to write the file in. If provided, the subdirectory will be created if it doesn't exist.
    
    Returns:
        `None`
    """
    if subdir:
        # Ensure the subdirectory exists
        os.makedirs(subdir, exist_ok=True)

        # Construct the full path to the file
        filename = os.path.join(subdir, filename)

    # Write the list of dictionaries to the file in JSON format
    with open(filename, "w") as f:
        for i, entry in enumerate(data):
            # Go through each key-value pair in the dictionary to make sure the values are JSON serializable
            entry = make_json_serializable(entry)
            json_str = json.dumps(entry)
            f.write(json_str)
            if i < len(data) - 1:
                f.write("\n")


def make_json_serializable(value):
    """
    Recursively converts values in a dictionary or list to be JSON serializable.
    
    Args:
        value: The value to make JSON serializable.
    
    Returns:
        The JSON-serializable version of the input value.
    """
    if isinstance(value, dict):
        # If the value is a dictionary, we need to go through each key-value pair recursively
        return {k: make_json_serializable(v) for k, v in value.items()}
    elif isinstance(value, list):
        # If the value is a list, we need to process each element recursively
        return [make_json_serializable(item) for item in value]
    else:
        # Try to serialize the value directly, and if it fails, convert it to a string
        try:
            json.dumps(value)
            return value
        except (TypeError, ValueError):
            return str(value)


def sort_key(entry: dict) -> tuple[str, int]:
    """
    Index comes in two forms: TestCategory_Index or TestCategory_Index-FuncDocSubIndex-PromptSubIndex; both 0-indexed.

    TestCategory_Index: For example, `simple_20` means the 21st entry in the `simple` test category.

    TestCategory_Index-FuncDocSubIndex-PromptSubIndex is used when there are multiple prompts for a single function doc; this only happens in the live dataset.
    FuncDocSubIndex increments for each unique function doc.
    PromptSubIndex is per function doc. It resets to 0 for each function doc.
        For example, `live_simple_19-3-15` means the 20th entry in the `live_simple` test category.
        This entry has the 4th unique function doc and the 16th prompt for that function doc (there are at least 15 other prompts for this same function doc in this category).

    In either case, the universal index is enough to sort the entries.
    """
    parts = entry["id"].rsplit("_", 1)
    test_category, index = parts[0], parts[1]
    # This handles the case where the index is in the form TestCategory_Index-FuncDocSubIndex-PromptSubIndex
    if "-" in index:
        index = index.split("-")[0]
    return (test_category, int(index))


def is_function_calling_format_output(decoded_output) -> bool:
    """
    Ensure the output is a list of dictionaries of the form:
    `[{func1: {param1: val1, param2: val2, ...}}, {func2: {param1: val1, param2: val2, ...}}, ...]`
    Sometimes the model handler's `decode_ast` method will return successfully, but the output is not in the correct format, and that will mess up the downstream evaluation that expects this format.
    This is especially the case when the model doesn't predict any function calls, and the output is an human-readable string.
    Note: Empty list `[]` is considered the correct format in this check.
    """
    if type(decoded_output) != list:
        return False
    for item in decoded_output:
        if type(item) != dict:
            return False
        # Check for `{func1: {param1: val1, param2: val2, ...}}`, should only have one key-value pair
        if len(item) != 1:
            return False
        # Check for `{param1: val1, param2: val2, ...}`; the parameter-value pairs should be a dictionary
        if type(list(item.values())[0]) != dict:
            return False
    return True


def is_executable_format_output(decoded_output) -> bool:
    """
    Checks if decoded output is in the correct format for executable tests (list of strings).
    
    Args:
        decoded_output: The output to check.
    
    Returns:
        `bool`: True if the output is in the correct format, False otherwise.
    """
    # Ensure the output is a list of strings (one or more strings)
    if type(decoded_output) == list:
        if len(decoded_output) == 0:
            return False
        for item in decoded_output:
            if type(item) != str:
                return False
        return True
    return False


def is_empty_output(decoded_output) -> bool:
    """
    Checks if decoded output is empty (not in function calling format or empty list/dict).
    
    Args:
        decoded_output: The output to check.
    
    Returns:
        `bool`: True if the output is empty, False otherwise.
    """
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


def parse_test_category_argument(test_category_args: list[str]) -> tuple[list[str], list[str]]:
    """
    Parses test category arguments into test filenames and test names using predefined mappings.
    
    Args:
        test_category_args (`list[str]`):
            List of test category names or collection names.
    
    Returns:
        `tuple[list[str], list[str]]`: A tuple containing two lists:
            1. Sorted list of test filenames
            2. Sorted list of test names
    
    Raises:
        `Exception`: If an invalid test category name is provided.
    """
    test_name_total = set()
    test_filename_total = set()

    for test_category in test_category_args:
        if test_category in TEST_COLLECTION_MAPPING:
            for test_name in TEST_COLLECTION_MAPPING[test_category]:
                test_name_total.add(test_name)
                test_filename_total.add(TEST_FILE_MAPPING[test_name])
        elif test_category in TEST_FILE_MAPPING:
            test_name_total.add(test_category)
            test_filename_total.add(TEST_FILE_MAPPING[test_category])
        else:
            # Invalid test category name
            raise Exception(f"Invalid test category name provided: {test_category}")

    return sorted(list(test_filename_total)), sorted(list(test_name_total))