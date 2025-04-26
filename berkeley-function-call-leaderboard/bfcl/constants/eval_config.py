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
