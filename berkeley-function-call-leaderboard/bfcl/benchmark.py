import json
import argparse

from tqdm import tqdm

from bfcl.types import Leaderboard
from bfcl.model_handler.base import ModelStyle, BaseHandler


def benchmark(
    leaderboard: Leaderboard, 
    model_handler: BaseHandler, 
    args: argparse.Namespace
) -> None:
    
    test_category_to_data = leaderboard.load_test_data()
    get_file_name = lambda cat: leaderboard.get_file_name(cat).replace('.json', '_result.jsonl')
    print('Getting model responses...')
    if model_handler.model_style == ModelStyle.OSS_MODEL:
        # Combine all samples to use GPUs efficiently
        test_inputs = sum(test_category_to_data.values(), []) 
        combined_responses = model_handler.inference(inputs=test_inputs, num_gpus=args.num_gpus)
        # Collect all the responses for each test category
        test_category_to_responses = {} 
        for response in combined_responses:
            test_category_to_responses.setdefault(response['test_category'], []).append(response)
        # Save responses for each test category
        for test_category, responses in test_category_to_responses.items():
            model_handler.write(responses, file_name=get_file_name(test_category))
    else:
        # Proprietary models
        for test_category, test_inputs in test_category_to_data.items():
            # Check if model responses are already available for the test category
            file_name = get_file_name(test_category)
            responses = model_handler.load_model_responses(file_name)
            if responses is not None and len(responses) == len(test_inputs):
                continue
            response_ids = set(rp['id'] for rp in responses) if responses else None
            file_path = model_handler.model_dir / file_name
            with open(file_path, 'a+') as file:
                for test_input in tqdm(test_inputs, total=len(test_inputs), desc=f'{test_category.value}'):
                    if response_ids and test_input['id'] in response_ids:
                        continue
                    # TODO: Handle rate limits
                    try:
                        response, metadata = model_handler.inference(
                            prompt=test_input['question'], 
                            functions=test_input['function'], 
                            test_category=test_category,
                        )
                        row = dict(id=test_input['id'], response=response, **metadata)
                        file.write(json.dumps(row) + '\n')
                    except Exception as e:
                        print('Failed to get response! Error:', e)
