import re

from bfcl.model_handler.constants import UNDERSCORE_TO_DOT
                                          

def convert_func_name(function_name, model_name: str):
    model_name_escaped = model_name.replace("_", "/")
    if "." in function_name:
        if model_name_escaped in UNDERSCORE_TO_DOT:
            # OAI does not support "." in the function name so we replace it with "_". 
            # ^[a-zA-Z0-9_-]{1,64}$ is the regex for the name.
            # This happens for OpenAI, Mistral, and Google models
            return re.sub(r"\.", "_", function_name)
    return function_name

def find_description(func_descriptions, name):
    # If func_descriptions is a list, this is the multiple or multiple_parallel case
    if type(func_descriptions) == list:
        for func_description in func_descriptions:
            if func_description["name"] in name:
                return func_description
        return None
    else:
        # This is the parallel case, there is no need to loop through the list, as there is only one function
        return func_descriptions
    
def get_possible_answer_type(possible_answer: list):
    for answer in possible_answer:
        if answer != "":  # Optional parameter
            return type(answer)
    return None