import argparse, json, os, time
from tqdm import tqdm
from bfcl.model_handler.handler_map import handler_map
from bfcl.model_handler.model_style import ModelStyle
from bfcl.model_handler.constant import USE_COHERE_OPTIMIZATION
from bfcl.eval_checker.eval_checker_constant import TEST_COLLECTION_MAPPING, TEST_FILE_MAPPING
from concurrent.futures import ThreadPoolExecutor

RETRY_LIMIT = 3
# 60s for the timer to complete. But often we find that even with 60 there is a conflict. So 65 is a safe no.
RETRY_DELAY = 65  # Delay in seconds

def get_args():
    parser = argparse.ArgumentParser()
    # Refer to model_choice for supported models.
    parser.add_argument("--model", type=str, default="gorilla-openfunctions-v2", nargs="+")
    # Refer to test_categories for supported categories.
    parser.add_argument("--test-category", type=str, default="all", nargs="+")

    # Parameters for the model that you want to test.
    parser.add_argument("--temperature", type=float, default=0.001)
    parser.add_argument("--top-p", type=float, default=1)
    parser.add_argument("--max-tokens", type=int, default=1200)
    parser.add_argument("--num-gpus", default=1, type=int)
    parser.add_argument("--timeout", default=60, type=int)
    parser.add_argument("--num-threads", default=1, type=int)
    parser.add_argument("--gpu-memory-utilization", default=0.9, type=float)
    args = parser.parse_args()
    return args


def build_handler(model_name, temperature, top_p, max_tokens):
    handler = handler_map[model_name](model_name, temperature, top_p, max_tokens)
    return handler


def sort_key(entry):
    """
    Index comes in two forms: TestCategory_Index or TestCategory_Index-FuncDocSubIndex-PromptSubIndex; both 0-indexed.
    
    TestCategory_Index: For example, `simple_20` means the 21st entry in the `simple` test category.
    
    TestCategory_Index-FuncDocSubIndex-PromptSubIndex is used when there are multiple prompts for a single function doc; this only happens in the live dataset.
    FuncDocSubIndex increments for each unique function doc.
    PromptSubIndex is per function doc. It resets to 0 for each function doc.
        For example, `live_simple_19-3-15` means the 20th entry in the `live_simple` test category. 
        This entry has the 4th unique function doc and the 16th prompt for that function doc (there are at least 15 other prompts for this same function doc in this category).
    
    In either case, the universal index is enough to sort the entries.
    """
    parts = entry["id"].rsplit("_", 1)
    test_category, index = parts[0], parts[1]
    # This handles the case where the index is in the form TestCategory_Index-FuncDocSubIndex-PromptSubIndex
    if "-" in index:
        index = index.split("-")[0]
    return (test_category, int(index))


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

    return sorted(list(test_name_total)), sorted(list(test_filename_total))


def collect_test_cases(test_filename_total, model_name):
    model_name_dir = model_name.replace("/", "_")
    test_cases_total = []
    for file_to_open in test_filename_total:
        test_cases = []
        with open("./data/" + file_to_open) as f:
            for line in f:
                test_cases.append(json.loads(line))

        existing_result = []
        if os.path.exists(
            "./result/"
            + model_name_dir
            + "/"
            + file_to_open.replace(".json", "_result.json")
        ):
            with open(
                "./result/"
                + model_name_dir
                + "/"
                + file_to_open.replace(".json", "_result.json")
            ) as f:
                for line in f:
                    existing_result.append(json.loads(line))

        existing_ids = [entry["id"] for entry in existing_result]
        test_cases_total.extend(
            [
                test_case
                for test_case in test_cases
                if test_case["id"] not in existing_ids
            ]
        )

    return sorted(test_cases_total, key=sort_key)


def multi_threaded_inference(handler, test_case):
    user_question, functions, test_category = (
        test_case["question"],
        test_case["function"],
        test_case["id"].rsplit("_", 1)[0],
    )
    if type(functions) is dict or type(functions) is str:
        functions = [functions]

    retry_count = 0

    while True:
        try:
            result, metadata = handler.inference(
                user_question, functions, test_category
            )
            break  # Success, exit the loop
        except Exception as e:
            # TODO: It might be better to handle the exception in the handler itself rather than a universal catch block here, as each handler use different ways to call the endpoint.
            # OpenAI has openai.RateLimitError while Anthropic has anthropic.RateLimitError. It would be more robust in the long run.
            if retry_count < RETRY_LIMIT and (
                "rate limit reached" in str(e).lower()
                or (hasattr(e, "status_code") and (e.status_code in {429, 503, 500}))
            ):
                print(
                    f"Rate limit reached. Sleeping for 65 seconds. Retry {retry_count + 1}/{RETRY_LIMIT}"
                )
                time.sleep(RETRY_DELAY)
                retry_count += 1
            else:
                # This is usually the case when the model getting stuck on one particular test case.
                # For example, timeout error or FC model returning invalid JSON response.
                # Since temperature is already set to 0.001, retrying the same test case will not help.
                # So we continue the generation process and record the error message as the model response
                print("-" * 100)
                print(
                    "❗️❗️ Error occurred during inference. Maximum reties reached for rate limit or other error. Continuing to next test case."
                )
                print(f"❗️❗️ Test case ID: {test_case['id']}, Error: {str(e)}")
                print("-" * 100)

                return {
                    "id": test_case["id"],
                    "result": f"Error during inference: {str(e)}",
                }

    result_to_write = {
        "id": test_case["id"],
        "result": result,
        "input_token_count": metadata["input_tokens"],
        "output_token_count": metadata["output_tokens"],
        "latency": metadata["latency"],
    }

    return result_to_write


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
        futures = []
        with ThreadPoolExecutor(max_workers=args.num_threads) as executor:
            with tqdm(
                total=len(test_cases_total), desc=f"Generating results for {model_name}"
            ) as pbar:

                for test_case in test_cases_total:
                    future = executor.submit(
                        multi_threaded_inference, handler, test_case
                    )
                    futures.append(future)

                for future in futures:
                    # This will wait for the task to complete, so that we are always writing in order
                    result = future.result()
                    handler.write(result)
                    pbar.update()


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
            print(
                f"All selected test cases have been previously generated for {model_name}. No new test cases to generate."
            )
        else:
            generate_results(args, model_name, test_cases_total)
