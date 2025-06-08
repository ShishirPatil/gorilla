import os
from pathlib import Path

VLLM_PORT = 1053

# Directory of the installed package
PACKAGE_ROOT = Path(__file__).resolve().parents[2]

# By default, results and other generated files are stored alongside the
# package itself so that editable installs behave the same as a regular
# installation. You can override this by setting the ``BFCL_PROJECT_ROOT``
# environment variable.
PROJECT_ROOT = Path(os.getenv("BFCL_PROJECT_ROOT", PACKAGE_ROOT))

# NOTE: These paths are relative to the PROJECT_ROOT directory.
RESULT_PATH = PROJECT_ROOT / "result"
PROMPT_PATH = PACKAGE_ROOT / "data"
MULTI_TURN_FUNC_DOC_PATH = PROMPT_PATH / "multi_turn_func_doc"
POSSIBLE_ANSWER_PATH = PROMPT_PATH / "possible_answer"
SCORE_PATH = PROJECT_ROOT / "score"
DOTENV_PATH = PROJECT_ROOT / ".env"
UTILS_PATH = PACKAGE_ROOT / "utils"
TEST_IDS_TO_GENERATE_PATH = PACKAGE_ROOT / "test_case_ids_to_generate.json"


RED_FONT = "\033[91m"
RESET = "\033[0m"

RESULT_PATH.mkdir(parents=True, exist_ok=True)
SCORE_PATH.mkdir(parents=True, exist_ok=True)
