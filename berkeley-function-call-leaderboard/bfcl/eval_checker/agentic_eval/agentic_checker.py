from bfcl.eval_checker.ast_eval.ast_checker import standardize_string


#### Main functions ####


def agentic_checker(model_response: str, possible_answer_list: list[str]) -> dict:
    """
    Check if one of the possible answers is contained in the model response, ignoring case, whitespace and ",./-_*^" punctuation.
    """
    standardized_possible_answer_list = [
        standardize_string(possible_answer) for possible_answer in possible_answer_list
    ]
    # Sometimes the model response is a list of one string
    if type(model_response) is list:
        model_response = model_response[0]
        
    standardized_model_response = standardize_string(model_response)
    for possible_answer in standardized_possible_answer_list:
        if possible_answer in standardized_model_response:
            return {"valid": True, "error": []}

    return {
        "valid": False,
        "error_message": f"None of the expected answers were found in the model response.",
        "error_type": "agentic:answer_not_found",
        "details": {
            "model_response": model_response,
            "possible_answers": possible_answer_list,
            "standardized_model_response": standardized_model_response,
            "standardized_possible_answers": standardized_possible_answer_list,
        },
    }


#### Helper functions ####
