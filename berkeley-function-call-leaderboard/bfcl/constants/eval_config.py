from pathlib import Path

REAL_TIME_MATCH_ALLOWED_DIFFERENCE = 0.2

# These two files are for the API status sanity check
REST_API_GROUND_TRUTH_FILE_PATH = (
    "./eval_checker/executable_eval/data/api_status_check_ground_truth_REST.json"
)
EXECTUABLE_API_GROUND_TRUTH_FILE_PATH = (
    "./eval_checker/executable_eval/data/api_status_check_ground_truth_executable.json"
)

# This is the ground truth file for the `rest` test category
REST_EVAL_GROUND_TRUTH_PATH = "./eval_checker/executable_eval/data/rest-eval-response_v5.jsonl"

# Price got from AZure, 22.032 per hour for 8 V100, Pay As You Go Total Price
# Reference: https://azure.microsoft.com/en-us/pricing/details/machine-learning/
V100_x8_PRICE_PER_HOUR = 22.032

RED_FONT = "\033[91m"
RESET = "\033[0m"

# Construct the full path for other modules to use
script_dir = Path(__file__).parent.parent
REST_API_GROUND_TRUTH_FILE_PATH = (script_dir / REST_API_GROUND_TRUTH_FILE_PATH).resolve()
EXECTUABLE_API_GROUND_TRUTH_FILE_PATH = (script_dir / EXECTUABLE_API_GROUND_TRUTH_FILE_PATH).resolve()
REST_EVAL_GROUND_TRUTH_PATH = (script_dir / REST_EVAL_GROUND_TRUTH_PATH).resolve()

UNDERSCORE_TO_DOT = [
    # TODO: Use the model style to determine this, single source of truth
    "DeepSeek-V3-FC",
    "gpt-4.5-preview-2025-02-27-FC",
    "o1-2024-12-17-FC",
    "o3-mini-2025-01-31-FC",
    "gpt-4o-2024-11-20-FC",
    "gpt-4o-mini-2024-07-18-FC",
    "gpt-4-turbo-2024-04-09-FC",
    "gpt-3.5-turbo-0125-FC",
    "claude-3-opus-20240229-FC",
    "claude-3-sonnet-20240229-FC",
    "claude-3-5-sonnet-20240620-FC",
    "claude-3-5-sonnet-20241022-FC",
    "claude-3-7-sonnet-20250219-FC",
    "claude-3-haiku-20240307-FC",
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
    "gemini-2.0-flash-lite-preview-02-05-FC",
    "gemini-2.0-flash-001-FC",
    "gemini-2.0-pro-exp-02-05-FC",
    "gemini-1.5-pro-002-FC",
    "gemini-1.5-pro-001-FC",
    "gemini-1.5-flash-002-FC",
    "gemini-1.5-flash-001-FC",
    "gemini-1.0-pro-002-FC",
    "meetkai/functionary-small-v3.1-FC",
    "meetkai/functionary-small-v3.2-FC",
    "meetkai/functionary-medium-v3.1-FC",
    "NousResearch/Hermes-2-Pro-Llama-3-8B",
    "NousResearch/Hermes-2-Pro-Llama-3-70B",
    "NousResearch/Hermes-2-Pro-Mistral-7B",
    "NousResearch/Hermes-2-Theta-Llama-3-8B",
    "NousResearch/Hermes-2-Theta-Llama-3-70B",
    "command-r-plus-FC",
    "command-r7b-12-2024-FC",
    "THUDM/glm-4-9b-chat",
    "ibm-granite/granite-20b-functioncalling",
    "yi-large-fc",
    "openbmb/MiniCPM3-4B-FC",
    "grok-beta",
]
