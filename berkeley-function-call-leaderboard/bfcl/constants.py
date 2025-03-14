from pathlib import Path

# NOTE: These paths are relative to the `bfcl` directory where this script is located.
RESULT_PATH = "../result/"
PROMPT_PATH = "../data/"
MULTI_TURN_FUNC_DOC_PATH = "../data/multi_turn_func_doc/"
POSSIBLE_ANSWER_PATH = "../data/possible_answer/"
SCORE_PATH = "../score/"
DOTENV_PATH = "../.env"
UTILS_PATH = "../utils/"
PROJECT_ROOT = "../"
TEST_IDS_TO_GENERATE_PATH = "../test_case_ids_to_generate.json"

VERSION_PREFIX = "BFCL_v3"

# These are in the PROMPT_PATH
TEST_FILE_MAPPING = {
    "exec_simple": f"{VERSION_PREFIX}_exec_simple.json",
    "exec_parallel": f"{VERSION_PREFIX}_exec_parallel.json",
    "exec_multiple": f"{VERSION_PREFIX}_exec_multiple.json",
    "exec_parallel_multiple": f"{VERSION_PREFIX}_exec_parallel_multiple.json",
    "simple": f"{VERSION_PREFIX}_simple.json",
    "irrelevance": f"{VERSION_PREFIX}_irrelevance.json",
    "parallel": f"{VERSION_PREFIX}_parallel.json",
    "multiple": f"{VERSION_PREFIX}_multiple.json",
    "parallel_multiple": f"{VERSION_PREFIX}_parallel_multiple.json",
    "java": f"{VERSION_PREFIX}_java.json",
    "javascript": f"{VERSION_PREFIX}_javascript.json",
    "rest": f"{VERSION_PREFIX}_rest.json",
    "sql": f"{VERSION_PREFIX}_sql.json",
    "chatable": f"{VERSION_PREFIX}_chatable.json",
    # Live Datasets
    "live_simple": f"{VERSION_PREFIX}_live_simple.json",
    "live_multiple": f"{VERSION_PREFIX}_live_multiple.json",
    "live_parallel": f"{VERSION_PREFIX}_live_parallel.json",
    "live_parallel_multiple": f"{VERSION_PREFIX}_live_parallel_multiple.json",
    "live_irrelevance": f"{VERSION_PREFIX}_live_irrelevance.json",
    "live_relevance": f"{VERSION_PREFIX}_live_relevance.json",
    # Multi-turn Datasets
    "multi_turn_base": f"{VERSION_PREFIX}_multi_turn_base.json",
    "multi_turn_miss_func": f"{VERSION_PREFIX}_multi_turn_miss_func.json",
    "multi_turn_miss_param": f"{VERSION_PREFIX}_multi_turn_miss_param.json",
    "multi_turn_long_context": f"{VERSION_PREFIX}_multi_turn_long_context.json",
    "multi_turn_composite": f"{VERSION_PREFIX}_multi_turn_composite.json",
}

TEST_COLLECTION_MAPPING = {
    "all": [
        "exec_simple",
        "exec_parallel",
        "exec_multiple",
        "exec_parallel_multiple",
        "simple",
        "irrelevance",
        "parallel",
        "multiple",
        "parallel_multiple",
        "java",
        "javascript",
        "rest",
        "live_simple",
        "live_multiple",
        "live_parallel",
        "live_parallel_multiple",
        "live_irrelevance",
        "live_relevance",
        "multi_turn_base",
        "multi_turn_miss_func",
        "multi_turn_miss_param",
        "multi_turn_long_context",
    ],
    "multi_turn": [
        "multi_turn_base",
        "multi_turn_miss_func",
        "multi_turn_miss_param",
        "multi_turn_long_context",
    ],
    "single_turn": [
        "exec_simple",
        "exec_parallel",
        "exec_multiple",
        "exec_parallel_multiple",
        "simple",
        "irrelevance",
        "parallel",
        "multiple",
        "parallel_multiple",
        "java",
        "javascript",
        "rest",
        "live_simple",
        "live_multiple",
        "live_parallel",
        "live_parallel_multiple",
        "live_irrelevance",
        "live_relevance",
    ],
    "live": [
        "live_simple",
        "live_multiple",
        "live_parallel",
        "live_parallel_multiple",
        "live_irrelevance",
        "live_relevance",
    ],
    "non_live": [
        "exec_simple",
        "exec_parallel",
        "exec_multiple",
        "exec_parallel_multiple",
        "simple",
        "irrelevance",
        "parallel",
        "multiple",
        "parallel_multiple",
        "java",
        "javascript",
        "rest",
    ],
    # TODO: Update this mapping
    "ast": [
        "simple",
        "irrelevance",
        "parallel",
        "multiple",
        "parallel_multiple",
        "java",
        "javascript",
        "live_simple",
        "live_multiple",
        "live_parallel",
        "live_parallel_multiple",
        "live_irrelevance",
        "live_relevance",
    ],
    "executable": [
        "exec_simple",
        "exec_parallel",
        "exec_multiple",
        "exec_parallel_multiple",
        "rest",
    ],
    "non_python": [
        "java",
        "javascript",
    ],
    "python": [
        "exec_simple",
        "exec_parallel",
        "exec_multiple",
        "exec_parallel_multiple",
        "simple",
        "irrelevance",
        "parallel",
        "multiple",
        "parallel_multiple",
        "rest",
        "live_simple",
        "live_multiple",
        "live_parallel",
        "live_parallel_multiple",
        "live_irrelevance",
        "live_relevance",
    ],
    "python_ast": [
        "simple",
        "irrelevance",
        "parallel",
        "multiple",
        "parallel_multiple",
        "live_simple",
        "live_multiple",
        "live_parallel",
        "live_parallel_multiple",
        "live_irrelevance",
        "live_relevance",
    ],
}

MULTI_TURN_FUNC_DOC_FILE_MAPPING = {
    "GorillaFileSystem": "gorilla_file_system.json",
    "MathAPI": "math_api.json",
    "MessageAPI": "message_api.json",
    "TwitterAPI": "posting_api.json",
    "TicketAPI": "ticket_api.json",
    "TradingBot": "trading_bot.json",
    "TravelAPI": "travel_booking.json",
    "VehicleControlAPI": "vehicle_control.json",
}


# Construct the full path to use by other scripts
script_dir = Path(__file__).parent
RESULT_PATH = (script_dir / RESULT_PATH).resolve()
PROMPT_PATH = (script_dir / PROMPT_PATH).resolve()
MULTI_TURN_FUNC_DOC_PATH = (script_dir / MULTI_TURN_FUNC_DOC_PATH).resolve()
POSSIBLE_ANSWER_PATH = (script_dir / POSSIBLE_ANSWER_PATH).resolve()
SCORE_PATH = (script_dir / SCORE_PATH).resolve()
DOTENV_PATH = (script_dir / DOTENV_PATH).resolve()
UTILS_PATH = (script_dir / UTILS_PATH).resolve()
PROJECT_ROOT = (script_dir / PROJECT_ROOT).resolve()
TEST_IDS_TO_GENERATE_PATH = (script_dir / TEST_IDS_TO_GENERATE_PATH).resolve()

RESULT_PATH.mkdir(parents=True, exist_ok=True)
SCORE_PATH.mkdir(parents=True, exist_ok=True)
