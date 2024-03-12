from utils.python_parser import parse_python_function_call
from utils.java_parser import parse_java_function_call
from utils.js_parser import parse_javascript_function_call

FN_CALL_DELIMITER = "<<function>>"

def strip_function_calls(content: str) -> list[str]:
    """
    Split the content by the function call delimiter and remove empty strings
    """
    return [element.strip() for element in content.split(FN_CALL_DELIMITER)[2:] if element.strip()]

def parse_function_call(call: str) -> dict[str, any]:
    """
    This is temporary. The long term solution is to union all the 
    types of the parameters from the user's input function definition,
    and check which language is a proper super set of the union type.
    """
    try:
        return parse_python_function_call(call)
    except Exception as e:
        # If Python parsing fails, try Java parsing
        try:
            java_result = parse_java_function_call(call)
            if not java_result:
                raise Exception("Java parsing failed")
            return java_result
        except Exception as e:
            # If Java parsing also fails, try JavaScript parsing
            try:   
                javascript_result = parse_javascript_function_call(call)
                if not javascript_result:
                    raise Exception("JavaScript parsing failed")
                return javascript_result
            except:
                return None