REAL_TIME_MATCH_ALLOWED_DIFFERENCE = 0.2

REST_API_GROUND_TRUTH_FILE_PATH = "./executable_eval/data/api_status_check_ground_truth_REST.json"
EXECTUABLE_API_GROUND_TRUTH_FILE_PATH = "./executable_eval/data/api_status_check_ground_truth_executable.json"

COLUMNS_NON_LIVE = [
    "Rank",
    "Overall Acc",
    "Model",
    "Model Link",
    "Organization",
    "License",
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
    "Cost ($ Per 1k Function Calls)",
    "Latency Mean (s)",
    "Latency Standard Deviation (s)",
    "Latency 95th Percentile (s)",
]


COLUMNS_LIVE = [
    "Rank",
    "Overall Acc",
    "Model",
    "Model Link",
    "Organization",
    "License",
    "AST Summary",
    "Python Simple AST",
    "Python Multiple AST",
    "Python Parallel AST",
    "Python Parallel Multiple AST",
    "Irrelevance Detection",
    "Relevance Detection",
    "Cost ($ Per 1k Function Calls)",
    "Latency Mean (s)",
    "Latency Standard Deviation (s)",
    "Latency 95th Percentile (s)",
]


COLUMNS_COMBINED = [
    "Rank",
    "Overall Acc",
    "Model",
    "Model Link",
    "Organization",
    "License",
    "AST Summary",
    "Exec Summary",
    "Simple AST",
    "Multiple AST",
    "Parallel AST",
    "Parallel Multiple AST",
    "Simple Exec",
    "Multiple Exec",
    "Parallel Exec",
    "Parallel Multiple Exec",
    "Irrelevance Detection",
    "Relevance Detection",
    "Cost ($ Per 1k Function Calls)",
    "Latency Mean (s)",
    "Latency Standard Deviation (s)",
    "Latency 95th Percentile (s)",
]

# Price got from AZure, 22.032 per hour for 8 V100, Pay As You Go Total Price
# Reference: https://azure.microsoft.com/en-us/pricing/details/machine-learning/
V100_x8_PRICE_PER_HOUR = 22.032

RED_FONT = "\033[91m"
RESET = "\033[0m"