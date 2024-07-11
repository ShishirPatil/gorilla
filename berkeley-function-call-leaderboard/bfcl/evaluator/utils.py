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

@staticmethod
def is_function_calling_format_output(decoded_output):
    # Ensure the output is a list of dictionaries
    if isinstance(decoded_output, list):
        for item in decoded_output:
            if not isinstance(item, dict):
                return False
        return True
    return False
