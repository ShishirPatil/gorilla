import argparse, json, os
from tqdm import tqdm
from model_handler.handler_map import handler_map
from model_handler.model_style import ModelStyle
from model_handler.constant import USE_COHERE_OPTIMIZATION
import aiohttp
import asyncio
from functools import wraps,partial

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
    parser.add_argument('--batch-size', type=int, default=1, help='Batch size for processing (default: 1)')

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
    "multiple_function": "gorilla_openfunctions_v1_test_multiple_function.json",
    "parallel_multiple_function": "gorilla_openfunctions_v1_test_parallel_multiple_function.json",
    "java": "gorilla_openfunctions_v1_test_java.json",
    "javascript": "gorilla_openfunctions_v1_test_javascript.json",
    "rest": "gorilla_openfunctions_v1_test_rest.json",
    "sql": "gorilla_openfunctions_v1_test_sql.json",
}

def make_async(func):
    @wraps(func)
    async def run(*args, loop=None, executor=None, **kwargs):
        if loop is None:
            loop = asyncio.get_running_loop()
        pfunc = partial(func, *args, **kwargs)
        return await loop.run_in_executor(executor, pfunc)
    return run

## automatically wraps the the handler to make handler.inference async
def build_handler(model_name, temperature, top_p, max_tokens):
    handler = handler_map[model_name](model_name, temperature, top_p, max_tokens)
    
    if not asyncio.iscoroutinefunction(handler.inference):
        handler.inference = make_async(handler.inference)
    return handler


def load_file(test_category):
    if test_category == "all":
        test_cate, files_to_open = list(test_categories.keys()), list(
            test_categories.values()
        )
    else:
        test_cate, files_to_open = [test_category], [test_categories[test_category]]
    return test_cate, files_to_open


async def fetch_and_process(session, index, test_case, handler, test_category, file_to_open):
    user_question, functions = test_case["question"], test_case["function"]
    if isinstance(functions, (dict, str)):
        functions = [functions]

    result, metadata = await handler.inference(user_question, functions, test_category)

    result_to_write = {
        "idx": index,
        "result": result,
        "input_token_count": metadata["input_tokens"],
        "output_token_count": metadata["output_tokens"],
        "latency": metadata["latency"],
    }
    await handler.write(result_to_write, file_to_open)

async def main():
    args = get_args()
    if USE_COHERE_OPTIMIZATION and "command-r-plus" in args.model:
        args.model = args.model + "-optimized"
    
    handler = build_handler(args.model, args.temperature, args.top_p, args.max_tokens)

    if handler.model_style == ModelStyle.OSSMODEL:
        result = await handler.inference(
            question_file="eval_data_total.json",
            test_category=args.test_category,
            num_gpus=args.num_gpus,
        )
        for res in result[0]:
            await handler.write(res, "result.json")
    else:
        test_cate, files_to_open = load_file(args.test_category)
        for test_category, file_to_open in zip(test_cate, files_to_open):
            print("Generating: " + file_to_open)
            test_cases = []
            with open("./data/" + file_to_open) as f:
                for line in f:
                    test_cases.append(json.loads(line))
            
            # sorts the results of the test cases if they already exist 
            # and returns the indexs that have been saved so far in order
            indicies = handler.sort_results(file_to_open) 

            # filter the test_cases that have already been completed
            # add a None if test_case already completed
            filtered_test_cases = []
            if indicies is not None:
                for test_idx,test_case in enumerate(test_cases):
                    if test_idx not in indicies:
                        filtered_test_cases.append(test_case)
                    else:
                        filtered_test_cases.append(None)
                test_cases = filtered_test_cases
            debug = []
            for test_idx,test_case in enumerate(test_cases):
                if test_case is not None:
                    debug.append(test_idx)
                else:
                    debug.append(None)
            print(f"Completed Indicies {indicies}")
            print(f"Test Indicies {debug}")

            async with aiohttp.ClientSession() as session:
                batch_size = args.batch_size    # Number of iterations to run at a time
                tasks = []
                # Create a tqdm progress bar for the entire dataset
                progress_bar = tqdm(total=len(test_cases), desc="Processing test cases")
                
                for start_index in range(0, len(test_cases), batch_size):
                    end_index = min(start_index + batch_size, len(test_cases))
                    for index in range(start_index, end_index):
                        test_case = test_cases[index]
                        # if test_case is None it means its already completed
                        if test_case is None:
                            progress_bar.update(1)  # Update for skipped items
                            continue
                        task = asyncio.create_task(fetch_and_process(session, index, test_case, handler, test_category, file_to_open))
                        task.add_done_callback(lambda _: progress_bar.update(1))  # Update progress when task is done
                        tasks.append(task)
                    await asyncio.gather(*tasks)
                    tasks.clear()
            progress_bar.close()
            ## sort results since async entires could be out of order
            handler.sort_results(file_to_open)


if __name__ == "__main__":
    asyncio.run(main())