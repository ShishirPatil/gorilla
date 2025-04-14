from pathlib import Path

VLLM_PORT = 1053

# The root directory of the project, relative to the current file location
PROJECT_ROOT = "../../"

# NOTE: These paths are relative to the PROJECT_ROOT directory.
RESULT_PATH = "./result/"
PROMPT_PATH = "./data/"
MULTI_TURN_FUNC_DOC_PATH = "./data/multi_turn_func_doc/"
POSSIBLE_ANSWER_PATH = "./data/possible_answer/"
SCORE_PATH = "./score/"
DOTENV_PATH = "./.env"
UTILS_PATH = "./utils/"
TEST_IDS_TO_GENERATE_PATH = "./test_case_ids_to_generate.json"


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
    "gemini-2.5-pro-exp-03-25-FC",
    "gemini-2.0-flash-lite-001-FC",
    "gemini-2.0-flash-001-FC",
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
    "command-a-03-2025-FC",
    "THUDM/glm-4-9b-chat",
    "ibm-granite/granite-20b-functioncalling",
    "yi-large-fc",
    "openbmb/MiniCPM3-4B-FC",
    "grok-beta",
    "qwen/qwq-32b-FC-novita",
    "meta-llama/llama-4-maverick-17b-128e-instruct-fp8-FC-novita",
    "meta-llama/llama-4-scout-17b-16e-instruct-FC-novita",
]

RED_FONT = "\033[91m"
RESET = "\033[0m"

# Construct the full path for other modules to use
script_dir = Path(__file__).parent
PROJECT_ROOT = (script_dir / PROJECT_ROOT).resolve()

RESULT_PATH = (PROJECT_ROOT / RESULT_PATH).resolve()
PROMPT_PATH = (PROJECT_ROOT / PROMPT_PATH).resolve()
MULTI_TURN_FUNC_DOC_PATH = (PROJECT_ROOT / MULTI_TURN_FUNC_DOC_PATH).resolve()
POSSIBLE_ANSWER_PATH = (PROJECT_ROOT / POSSIBLE_ANSWER_PATH).resolve()
SCORE_PATH = (PROJECT_ROOT / SCORE_PATH).resolve()
DOTENV_PATH = (PROJECT_ROOT / DOTENV_PATH).resolve()
UTILS_PATH = (PROJECT_ROOT / UTILS_PATH).resolve()
TEST_IDS_TO_GENERATE_PATH = (PROJECT_ROOT / TEST_IDS_TO_GENERATE_PATH).resolve()

RESULT_PATH.mkdir(parents=True, exist_ok=True)
SCORE_PATH.mkdir(parents=True, exist_ok=True)
