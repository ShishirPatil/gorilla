from pathlib import Path

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
