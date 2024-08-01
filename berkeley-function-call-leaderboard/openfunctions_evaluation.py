import argparse, json, os
from tqdm import tqdm
from bfcl.model_handler.handler_map import handler_map
from bfcl.model_handler.model_style import ModelStyle
from bfcl.model_handler.constant import USE_COHERE_OPTIMIZATION
from bfcl.eval_checker.eval_checker_constant import TEST_COLLECTION_MAPPING


def get_args():
    parser = argparse.ArgumentParser()
    # Refer to model_choice for supported models.
    parser.add_argument("--model", type=str, default="gorilla-openfunctions-v2", nargs="+")
    # Refer to test_categories for supported categories.
    parser.add_argument("--test-category", type=str, default="all", nargs="+")

    # Parameters for the model that you want to test.
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--top-p", type=float, default=1)
    parser.add_argument("--max-tokens", type=int, default=1200)
    parser.add_argument("--num-gpus", default=1, type=int)
    parser.add_argument("--timeout", default=60, type=int)
    parser.add_argument("--gpu-memory-utilization", default=0.9, type=float)
    args = parser.parse_args()
    return args


TEST_FILE_MAPPING = {
    "executable_simple": "gorilla_openfunctions_v1_test_executable_simple.json",
    "executable_parallel_function": "gorilla_openfunctions_v1_test_executable_parallel_function.json",
    "executable_multiple_function": "gorilla_openfunctions_v1_test_executable_multiple_function.json",
    "executable_parallel_multiple_function": "gorilla_openfunctions_v1_test_executable_parallel_multiple_function.json",
    "simple": "gorilla_openfunctions_v1_test_simple.json",
    "relevance": "gorilla_openfunctions_v1_test_relevance.json",
    "parallel_function": "gorilla_openfunctions_v1_test_parallel_function.json",
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


def parse_test_category_argument(test_category_args):
    test_name_total = set()
    test_filename_total = set()
    
    for test_category in test_category_args:
        if test_category in TEST_COLLECTION_MAPPING:
            for test_name in TEST_COLLECTION_MAPPING[test_category]:
                test_name_total.add(test_name)
                test_filename_total.add(TEST_FILE_MAPPING[test_name])
        else:
            test_name_total.add(test_category)
            test_filename_total.add(TEST_FILE_MAPPING[test_category])

    return list(test_name_total), list(test_filename_total)


def collect_test_cases(test_filename_total, model_name):
    test_cases_total = []
    for file_to_open in test_filename_total:
        test_cases = []
        with open("./data/" + file_to_open) as f:
            for line in f:
                test_cases.append(json.loads(line))

        num_existing_result = 0  # if the result file already exists, skip the test cases that have been tested.
        if os.path.exists(
            "./result/"
            + model_name.replace("/", "_")
            + "/"
            + file_to_open.replace(".json", "_result.json")
        ):
            with open(
                "./result/"
                + model_name.replace("/", "_")
                + "/"
                + file_to_open.replace(".json", "_result.json")
            ) as f:
                for line in f:
                    num_existing_result += 1

        test_cases_total.extend(test_cases[num_existing_result:])
    return test_cases_total


def generate_results(args, model_name, test_cases_total):
    handler = build_handler(model_name, args.temperature, args.top_p, args.max_tokens)

    if handler.model_style == ModelStyle.OSSMODEL:
        result, metadata = handler.inference(
            test_question=test_cases_total,
            num_gpus=args.num_gpus,
            gpu_memory_utilization=args.gpu_memory_utilization,
        )
        for test_case, res in zip(test_cases_total, result):
            result_to_write = {"id": test_case["id"], "result": res}
            handler.write(result_to_write)

    else:
        for test_case in tqdm(test_cases_total):

            user_question, functions, test_category = (
                test_case["question"],
                test_case["function"],
                test_case["id"].rsplit("_", 1)[0],
            )
            if type(functions) is dict or type(functions) is str:
                functions = [functions]

            result, metadata = handler.inference(
                user_question, functions, test_category
            )
            result_to_write = {
                "id": test_case["id"],
                "result": result,
                "input_token_count": metadata["input_tokens"],
                "output_token_count": metadata["output_tokens"],
                "latency": metadata["latency"],
            }
            handler.write(result_to_write)


if __name__ == "__main__":
    args = get_args()

    if type(args.model) is not list:
        args.model = [args.model]
    if type(args.test_category) is not list:
        args.test_category = [args.test_category]
        
    test_name_total, test_filename_total = parse_test_category_argument(args.test_category)
    
    print(f"Generating results for {args.model} on test category: {test_name_total}.")

    for model_name in args.model:
        if USE_COHERE_OPTIMIZATION and "command-r-plus" in model_name:
            model_name = model_name + "-optimized"
        
        test_cases_total = collect_test_cases(test_filename_total, model_name)
        
        if len(test_cases_total) == 0:
            print(f"All selected test cases have been previously generated for {model_name}. No new test cases to generate.")
        else:
            generate_results(args, model_name, test_cases_total)
