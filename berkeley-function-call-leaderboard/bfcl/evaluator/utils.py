def is_empty_output(decoded_output) -> bool:
    # This function is a patch to the ast decoder for relevance detection.
    # Sometimes the ast decoder will parse successfully, but the input doesn't 
    # really have a function call.
    # [], [{}], and anything that is not in function calling format is considered 
    # empty (and thus should be marked as correct).
    if (
        not is_function_calling_format_output(decoded_output)
        or len(decoded_output) == 0
        or (len(decoded_output) == 1 and len(decoded_output[0]) == 0)
    ):
        return True

def is_function_calling_format_output(decoded_output):
    # Ensure the output is a list of dictionaries
    if isinstance(decoded_output, list):
        for item in decoded_output:
            if not isinstance(item, dict):
                return False
        return True
    return False

def display_api_status_error(rest_error, executable_error, display_success=False):
    if not rest_error and not executable_error:
        if display_success:
            print("🟢 All API Status Test Passed!")
        return None

    RED_FONT = "\033[91m"
    RESET = "\033[0m"
    
    print(f"\n{RED_FONT}{'-' * 18} Executable Categories' Error Bounds Based on API Health Status {'-' * 18}{RESET}\n")

    if rest_error:
        print(f"❗️ Warning: Unable to verify health of executable APIs used in executable test group (REST). Please contact API provider.\n")
        print(f"{rest_error.error_rate} APIs affected:\n")
        for data, status in rest_error.errors:
            print(f"  - Test Case: {data['ground_truth']}")
            print(f"    Error Type: {status['error_type']}\n")
            
    if executable_error:
        print(f"❗️ Warning: Unable to verify health of executable APIs used in executable test group (Non-REST). Please contact API provider.\n")
        print(f"{executable_error.error_rate} APIs affected:\n")
        for data, status in executable_error.errors:
            print(f"  - Test Case: {data['ground_truth'][0]}")
            print(f"    Error Type: {status['error_type']}\n")

    print(f"{RED_FONT}{'-' * 100}\n{RESET}")

def is_rest_format_output(decoded_output):
    # Ensure the output is a list of one string
    if type(decoded_output) == list:
        if len(decoded_output) == 1 and type(decoded_output[0]) == str:
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