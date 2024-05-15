from typing import Any
import string
import re
from openai import OpenAI 
from openai import AzureOpenAI
from openai.types.chat import ChatCompletionMessageParam, ChatCompletion
import multiprocessing as mp
import time
import argparse
import json
import os
from client_utils import build_openai_client
import logging
from logconf import log_setup
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env.eval")  # take environment variables from .env.

def get_args() -> argparse.Namespace:
    """
    Parses and returns the arguments specified by the user's command
    """
    parser = argparse.ArgumentParser()

    parser.add_argument("--question-file", type=str, required=True)
    parser.add_argument("--answer-file", type=str, default="answer.jsonl")
    parser.add_argument("--model", type=str, default="gpt-4", help="The model to evaluate")
    parser.add_argument("--input-prompt-key", type=str, default="instruction", help="The column to use as input prompt")
    parser.add_argument("--output-answer-key", type=str, default="answer", help="The column to use as output answer")

    args = parser.parse_args()
    return args


if __name__ == "__main__":

    log_setup()
    client = build_openai_client(env_prefix = "EVAL")
    args = get_args()

    logger = logging.getLogger('eval')

    model = args.model
    prompt_key = args.input_prompt_key
    answer_key = args.output_answer_key

    def get_openai_response(
        prompt: str
    ) -> str | ChatCompletion | None :
        response = client.completions.create(
            model=model,
            prompt=prompt,
            temperature=0.2,
            max_tokens=1024,
        )

        try:
            return response.choices[0].text
        except Exception as e:
            print(e)
            return response

    def get_answer(input_json: dict[str, Any]) -> dict[str, Any]:
        prompt = input_json[prompt_key]
        result = get_openai_response(prompt)
        input_json[answer_key] = result
        return input_json

    def write_result_to_file(
        result: dict[str, Any], 
        write_file_name: str
    ) -> None:
        global file_write_lock
        with file_write_lock:
            with open(write_file_name, "a") as outfile:
                json.dump(result, outfile)
                outfile.write("\n")


    write_file_name = args.answer_file
    if os.path.isfile(write_file_name):
        os.remove(write_file_name)

    num_workers = 20
    file_write_lock = mp.Lock()
    inputs = []
    with open(args.question_file, 'r') as f:
        for line in f:
            inputs.append(json.loads(line))

    logger.info(f'number of inputs: {len(inputs)}')
    start_time = time.time()
    with tqdm(total=len(inputs)) as pbar:
        with ThreadPoolExecutor(num_workers) as executor:
            futures = [executor.submit(get_answer, input) for input in inputs]

            for future in as_completed(futures):
                result = future.result()
                pbar.update(1)
                write_result_to_file(result, write_file_name)

    end_time = time.time()
    logger.info(f"total time used: {end_time - start_time}")
