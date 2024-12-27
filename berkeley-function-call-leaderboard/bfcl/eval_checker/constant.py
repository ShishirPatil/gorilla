from pathlib import Path

from bfcl.model_handler.handler_map import local_inference_handler_map

REAL_TIME_MATCH_ALLOWED_DIFFERENCE = 0.2

# These two files are for the API status sanity check
REST_API_GROUND_TRUTH_FILE_PATH = (
    "./executable_eval/data/api_status_check_ground_truth_REST.json"
)
EXECTUABLE_API_GROUND_TRUTH_FILE_PATH = (
    "./executable_eval/data/api_status_check_ground_truth_executable.json"
)

# This is the ground truth file for the `rest` test category
REST_EVAL_GROUND_TRUTH_PATH = "./executable_eval/data/rest-eval-response_v5.jsonl"


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
    # TODO: Use the model style to determine this, single source of truth
    "o1-2024-12-17-FC",
    "gpt-4o-2024-11-20-FC",
    "gpt-4o-mini-2024-07-18-FC",
    "gpt-4-turbo-2024-04-09-FC",
    "gpt-3.5-turbo-0125-FC",
    "claude-3-opus-20240229-FC",
    "claude-3-5-sonnet-20241022-FC",
    "claude-3-5-haiku-20241022-FC",
    "nova-pro-v1.0",
    "nova-lite-v1.0",
    "nova-micro-v1.0",
    "open-mistral-nemo-2407-FC",
    "open-mixtral-8x22b-FC",
    "mistral-large-2407-FC",
    "mistral-large-2407-FC",
    "mistral-small-2402-FC",
    "mistral-small-2402-FC",
    "gemini-exp-1206-FC",
    "gemini-2.0-flash-exp-FC",
    "gemini-1.5-pro-002-FC",
    "gemini-1.5-pro-001-FC",
    "gemini-1.5-flash-002-FC",
    "gemini-1.5-flash-001-FC",
    "gemini-1.0-pro-002-FC",
    "meetkai/functionary-small-v3.1-FC",
    "meetkai/functionary-medium-v3.1-FC",
    "command-r-plus-FC",
    "command-r7b-12-2024-FC",
    "yi-large-fc",
    "grok-beta",
]
# All locally hosted models should be added as well
UNDERSCORE_TO_DOT += list(local_inference_handler_map.keys())


COLUMNS_NON_LIVE = [
    "Rank",
    "Model",
    "Non_Live Overall Acc",
    "AST Summary",
    "Exec Summary",
    "Simple AST",
    "Python Simple AST",
    "Java Simple AST",
    "JavaScript Simple AST",
    "Multiple AST",
    "Parallel AST",
    "Parallel Multiple AST",
    "Simple Exec",
    "Python Simple Exec",
    "REST Simple Exec",
    "Multiple Exec",
    "Parallel Exec",
    "Parallel Multiple Exec",
    "Irrelevance Detection",
]


COLUMNS_LIVE = [
    "Rank",
    "Model",
    "Live Overall Acc",
    "AST Summary",
    "Python Simple AST",
    "Python Multiple AST",
    "Python Parallel AST",
    "Python Parallel Multiple AST",
    "Irrelevance Detection",
    "Relevance Detection",
]


COLUMNS_MULTI_TURN = [
    "Rank",
    "Model",
    "Multi Turn Overall Acc",
    "Base",
    "Miss Func",
    "Miss Param",
    "Long Context",
]


COLUMNS_OVERALL = [
    "Rank",
    "Overall Acc",
    "Model",
    "Model Link",
    "Cost ($ Per 1k Function Calls)",
    "Latency Mean (s)",
    "Latency Standard Deviation (s)",
    "Latency 95th Percentile (s)",
    "Non-Live AST Acc",
    "Non-Live Simple AST",
    "Non-Live Multiple AST",
    "Non-Live Parallel AST",
    "Non-Live Parallel Multiple AST",
    "Non-Live Exec Acc",
    "Non-Live Simple Exec",
    "Non-Live Multiple Exec",
    "Non-Live Parallel Exec",
    "Non-Live Parallel Multiple Exec",
    "Live Acc",
    "Live Simple AST",
    "Live Multiple AST",
    "Live Parallel AST",
    "Live Parallel Multiple AST",
    "Multi Turn Acc",
    "Multi Turn Base",
    "Multi Turn Miss Func",
    "Multi Turn Miss Param",
    "Multi Turn Long Context",
    "Relevance Detection",
    "Irrelevance Detection",
    "Organization",
    "License",
]


# Price got from AZure, 22.032 per hour for 8 V100, Pay As You Go Total Price
# Reference: https://azure.microsoft.com/en-us/pricing/details/machine-learning/
V100_x8_PRICE_PER_HOUR = 22.032

RED_FONT = "\033[91m"
RESET = "\033[0m"

# Construct the full path for other modules to use
script_dir = Path(__file__).parent
REST_API_GROUND_TRUTH_FILE_PATH = (script_dir / REST_API_GROUND_TRUTH_FILE_PATH).resolve()
EXECTUABLE_API_GROUND_TRUTH_FILE_PATH = (script_dir / EXECTUABLE_API_GROUND_TRUTH_FILE_PATH).resolve()
REST_EVAL_GROUND_TRUTH_PATH = (script_dir / REST_EVAL_GROUND_TRUTH_PATH).resolve()
