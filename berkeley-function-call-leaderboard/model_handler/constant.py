USE_COHERE_OPTIMIZATION = False

DEFAULT_SYSTEM_PROMPT_WITHOUT_FUNC_DOC = """
    You are an expert in composing functions. You are given a question and a set of possible functions. 
    Based on the question, you will need to make one or more function/tool calls to achieve the purpose. 
    If none of the function can be used, point it out. If the given question lacks the parameters required by the function,
    also point it out. You should only return the function call in tools call sections.
    
    If you decide to invoke any of the function(s), you MUST put it in the format of [func_name1(params_name1=params_value1, params_name2=params_value2...), func_name2(params)]\n
    You SHOULD NOT include any other text in the response.
    """

DEFAULT_SYSTEM_PROMPT = DEFAULT_SYSTEM_PROMPT_WITHOUT_FUNC_DOC + """
    Here is a list of functions in JSON format that you can invoke.\n\n{functions}\n
    """

GORILLA_TO_OPENAPI = {
    "integer": "integer",
    "number": "number",
    "float": "number",
    "string": "string",
    "boolean": "boolean",
    "bool": "boolean",
    "array": "array",
    "list": "array",
    "dict": "object",
    "object": "object",
    "tuple": "array",
    "any": "string",
    "byte": "integer",
    "short": "integer",
    "long": "integer",
    "double": "number",
    "char": "string",
    "ArrayList": "array",
    "Array": "array",
    "HashMap": "object",
    "Hashtable": "object",
    "Queue": "array",
    "Stack": "array",
    "Any": "string",
    "String": "string",
    "Bigint": "integer",
}

GORILLA_TO_PYTHON = {
    "integer": "int",
    "number": "float",
    "float": "float",
    "string": "str",
    "boolean": "bool",
    "bool": "bool",
    "array": "list",
    "list": "list",
    "dict": "dict",
    "object": "dict",
    "tuple": "tuple",
    "any": "str",
    "byte": "int",
    "short": "int",
    "long": "int",
    "double": "float",
    "char": "str",
    "ArrayList": "list",
    "Array": "list",
    "HashMap": "dict",
    "Hashtable": "dict",
    "Queue": "list",
    "Stack": "list",
    "Any": "str",
    "String": "str",
    "Bigint": "int",
}

# supported open source models
MODEL_ID_DICT = {
    "deepseek-7b": "deepseek-coder",
    "glaiveai": "vicuna_1.1",
    "llama-v2-7b": "llama-2",
    "llama-v2-13b": "llama-2",
    "llama-v2-70b": "llama-2",
    "dolphin-2.2.1-mistral-7b": "dolphin-2.2.1-mistral-7b",
    "gorilla-openfunctions-v0": "gorilla",
    "functionary-small-v2.2": "mistral",
    "functionary-medium-v2.2": "mistral",
}

JAVA_TYPE_CONVERSION = {
    "byte": int,
    "short": int,
    "integer": int,
    "float": float,
    "double": float,
    "long": int,
    "boolean": bool,
    "char": str,
    "Array": list,
    "ArrayList": list,
    "Set": set,
    "HashMap": dict,
    "Hashtable": dict,
    "Queue": list,  # this can be `queue.Queue` as well, for simplicity we check with list
    "Stack": list,
    "String": str,
    "any": str,
}

JS_TYPE_CONVERSION = {
    "String": str,
    "integer": int,
    "float": float,
    "Bigint": int,
    "Boolean": bool,
    "dict": dict,
    "array": list,
    "any": str,
}

UNDERSCORE_TO_DOT = [
    "gpt-4o-2024-08-06-FC",
    "gpt-4o-2024-05-13-FC",
    "gpt-4o-mini-2024-07-18-FC",
    "gpt-4-turbo-2024-04-09-FC",
    "gpt-4-1106-preview-FC",
    "gpt-4-0125-preview-FC",
    "gpt-4-0613-FC",
    "gpt-3.5-turbo-0125-FC",
    "claude-3-opus-20240229-FC",
    "claude-3-sonnet-20240229-FC",
    "claude-3-haiku-20240307-FC",
    "claude-3-5-sonnet-20240620-FC",
    "open-mistral-nemo-2407-FC-Any",
    "open-mistral-nemo-2407-FC-Auto",
    "open-mixtral-8x22b-FC-Any",
    "open-mixtral-8x22b-FC-Auto",
    "mistral-large-2407-FC",
    "mistral-large-2407-FC-Any",
    "mistral-large-2407-FC-Auto",
    "mistral-small-2402-FC-Any",
    "mistral-small-2402-FC-Auto",
    "mistral-small-2402-FC",
    "gemini-1.0-pro",
    "gemini-1.5-pro-preview-0409",
    "gemini-1.5-pro-preview-0514",
    "gemini-1.5-flash-preview-0514",
    "meetkai/functionary-small-v3.1-FC",
    "meetkai/functionary-small-v3.2-FC",
    "meetkai/functionary-medium-v3.1-FC",
    "NousResearch/Hermes-2-Pro-Llama-3-8B",
    "NousResearch/Hermes-2-Pro-Llama-3-70B",
    "NousResearch/Hermes-2-Pro-Mistral-7B",
    "NousResearch/Hermes-2-Theta-Llama-3-8B",
    "NousResearch/Hermes-2-Theta-Llama-3-70B",
    "command-r-plus-FC",
    "command-r-plus-FC-optimized",
    "THUDM/glm-4-9b-chat",
    "ibm-granite/granite-20b-functioncalling",
    "yi-large-fc",
]

TEST_FILE_MAPPING = {
    "exec_simple": "BFCL_v2_exec_simple.json",
    "exec_parallel": "BFCL_v2_exec_parallel.json",
    "exec_multiple": "BFCL_v2_exec_multiple.json",
    "exec_parallel_multiple": "BFCL_v2_exec_parallel_multiple.json",
    "simple": "BFCL_v2_simple.json",
    "irrelevance": "BFCL_v2_irrelevance.json",
    "parallel": "BFCL_v2_parallel.json",
    "multiple": "BFCL_v2_multiple.json",
    "parallel_multiple": "BFCL_v2_parallel_multiple.json",
    "java": "BFCL_v2_java.json",
    "javascript": "BFCL_v2_javascript.json",
    "rest": "BFCL_v2_rest.json",
    "sql": "BFCL_v2_sql.json",
    "chatable": "BFCL_v2_chatable.json",
    # Live Datasets
    "live_simple": "BFCL_v2_live_simple.json",
    "live_multiple": "BFCL_v2_live_multiple.json",
    "live_parallel": "BFCL_v2_live_parallel.json",
    "live_parallel_multiple": "BFCL_v2_live_parallel_multiple.json",
    "live_irrelevance": "BFCL_v2_live_irrelevance.json",
    "live_relevance": "BFCL_v2_live_relevance.json",
}
