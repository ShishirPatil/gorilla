import argparse
import json
import os

from model_handler.constant import USE_COHERE_OPTIMIZATION
from model_handler.handler_map import handler_map
from model_handler.model_style import ModelStyle
from tqdm import tqdm


def get_args():
    parser = argparse.ArgumentParser()
    # Refer to model_choice for supported models.
    parser.add_argument("--model", type=str, default="gorilla-openfunctions-v2")
    # Refer to test_categories for supported categories.
    parser.add_argument("--test-category", type=str, default="all")

    # Parameters for the model that you want to test.
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--top-p", type=float, default=1)
    parser.add_argument("--max-tokens", type=int, default=1200)
    parser.add_argument("--num-gpus", default=1, type=int)
    parser.add_argument("--timeout", default=60, type=int)

    args = parser.parse_args()
    return args


test_categories = {
    "executable_simple": "gorilla_openfunctions_v1_test_executable_simple.json",
    "executable_parallel_function": "gorilla_openfunctions_v1_test_executable_parallel_function.json",
    "executable_multiple_function": "gorilla_openfunctions_v1_test_executable_multiple_function.json",
    "executable_parallel_multiple_function": "gorilla_openfunctions_v1_test_executable_parallel_multiple_function.json",
    "simple": "gorilla_openfunctions_v1_test_simple.json",
    "relevance": "gorilla_openfunctions_v1_test_relevance.json",
    "parallel_function": "gorilla_openfunctions_v1_test_parallel_function.json",
    "parallel_function_local": "gorilla_openfunctions_v1_test_parallel_function_local.json",
    "multiple_function": "gorilla_openfunctions_v1_test_multiple_function.json",
    "parallel_multiple_function": "gorilla_openfunctions_v1_test_parallel_multiple_function.json",
    "java": "gorilla_openfunctions_v1_test_java.json",
    "javascript": "gorilla_openfunctions_v1_test_javascript.json",
    "rest": "gorilla_openfunctions_v1_test_rest.json",
    "sql": "gorilla_openfunctions_v1_test_sql.json",
}


def build_handler(model_name, temperature, top_p, max_tokens):
    handler = handler_map[model_name](model_name, temperature, top_p, max_tokens)
    return handler


def load_file(test_category):
    if test_category == "all":
        test_cate, files_to_open = list(test_categories.keys()), list(
            test_categories.values()
        )
    else:
        test_cate, files_to_open = [test_category], [test_categories[test_category]]
    return test_cate, files_to_open


if __name__ == "__main__":
    args = get_args()
    if USE_COHERE_OPTIMIZATION and "command-r-plus" in args.model:
        args.model = args.model + "-optimized"
    handler = build_handler(args.model, args.temperature, args.top_p, args.max_tokens)
    if handler.model_style == ModelStyle.OSSMODEL:
        result = handler.inference(
            question_file="eval_data_total.json",
            test_category=args.test_category,
            num_gpus=args.num_gpus,
        )
        for res in result[0]:
            handler.write(res, "result.json")
    else:
        test_cate, files_to_open = load_file(args.test_category)
        for test_category, file_to_open in zip(test_cate, files_to_open):
            print("Generating: " + file_to_open)
            test_cases = []
            with open("./data/" + file_to_open) as f:
                for line in f:
                    test_cases.append(json.loads(line))
            num_existing_result = 0  # if the result file already exists, skip the test cases that have been tested.
            if os.path.exists(
                "./result/"
                + args.model.replace("/", "_")
                + "/"
                + file_to_open.replace(".json", "_result.json")
            ):
                with open(
                    "./result/"
                    + args.model.replace("/", "_")
                    + "/"
                    + file_to_open.replace(".json", "_result.json")
                ) as f:
                    for line in f:
                        num_existing_result += 1
            for index, test_case in enumerate(tqdm(test_cases)):
                if index < num_existing_result:
                    continue
                user_question, functions = test_case["question"], test_case["function"]
                if type(functions) is dict or type(functions) is str:
                    functions = [functions]
                result, metadata = handler.inference(
                    user_question, functions, test_category
                )
                result_to_write = {
                    "idx": index,
                    "result": result,
                    "input_token_count": metadata["input_tokens"],
                    "output_token_count": metadata["output_tokens"],
                    "latency": metadata["latency"],
                }
                handler.write(result_to_write, file_to_open)
