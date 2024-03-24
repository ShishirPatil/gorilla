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

base_url = ''
api_key = ''
model_name = ''
client = OpenAI(
        base_url = base_url,
        api_key=api_key,
        )

def get_openai_response(
    message: list[ChatCompletionMessageParam]
) -> str | ChatCompletion | None :
    response = client.chat.completions.create(
        messages=message,
        model=model_name,
        temperature=0.2,
    )
    try:
        return response.choices[0].message.content
    except Exception as e:
        print(e)
        return response

def get_answer(input_json: dict[str, Any]) -> dict[str, Any]:
    message = [{"role": "user", "content": input_json['instruction']}]
    result = get_openai_response(message)
    input_json['model_answer'] = result
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--question-file", type=str, required=True)
    parser.add_argument("--answer-file", type=str, default="answer.jsonl")
    args = parser.parse_args()
    write_file_name = args.answer_file
    if os.path.isfile(write_file_name):
        os.remove(write_file_name)

    num_workers = 20
    file_write_lock = mp.Lock()
    inputs = []
    with open(args.question_file, 'r') as f:
        for line in f:
            inputs.append(json.loads(line))

    print('number of inputs: ', len(inputs))
    start_time = time.time()
    with mp.Pool(num_workers) as pool:
        results = []
        for idx, input in enumerate(inputs):
            result = pool.apply_async(
                get_answer,
                args=(input,),
                callback=lambda result: write_result_to_file(result, write_file_name),
            )
            results.append(result)
        pool.close()
        pool.join()
    end_time = time.time()
    print("total time used: ", end_time - start_time)
