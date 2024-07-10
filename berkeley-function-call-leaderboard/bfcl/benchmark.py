import os
import json
import argparse

from tqdm import tqdm
from dotenv import load_dotenv

from bfcl.model_handler.base import BaseHandler, ModelStyle
from bfcl.types import (LeaderboardCategory, LeaderboardCategories,
                        LeaderboardVersion, ModelType, LeaderboardCategoryGroup)

load_dotenv()


def main() -> None:
    args = get_args()
    if os.getenv('USE_COHERE_OPTIMIZATION') and 'command-r-plus' in args.model:
        args.model += '-optimized'

    test_categories = _get_test_categories(args)
    model_handler = _get_model_handler(args)
    test_category_to_data = test_categories.load_test_data()
    get_file_name = lambda cat: test_categories.get_file_name(cat).replace('.json', '_result.jsonl')
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


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--model', 
        type=str, 
        default='gorilla-openfunctions-v2',
        help="Name of the LLM. (default: 'gorilla-openfunctions-v2')"
    )
    parser.add_argument(
        '--model-type', 
        type=ModelType,
        choices=[mtype.value for mtype in ModelType], 
        default=ModelType.PROPRIETARY.value,
        help="Model type: Open-source or Proprietary (default: 'proprietary')"
    )
    parser.add_argument(
        '--test-group', 
        type=LeaderboardCategoryGroup, 
        choices=[group.value for group in LeaderboardCategoryGroup],
        default=None,
        help='Test category group (default: None)'
    )
    parser.add_argument(
        '--test-categories', 
        type=str, 
        default=None,
        help=(
            'Comma-separated list of test categories '
            f"({','.join(cat.value for cat in LeaderboardCategory)}). "
            "(default: None)"
        )
    )
    parser.add_argument(
        '--version', 
        type=LeaderboardVersion, 
        default=LeaderboardVersion.V1.value,
        choices=[category.value for category in LeaderboardVersion],
        help="Leaderboard version. (default: 'v1')",
    )
    parser.add_argument('--temperature', type=float, default=0.7, help='Temperature (default: 0.7)')
    parser.add_argument('--top-p', type=float, default=1, help='Top-p (default: 1)')
    parser.add_argument('--max-tokens', type=int, default=1000, help='Max tokens (default: 1000)')
    parser.add_argument('--num-gpus', default=1, type=int, help='No. of GPUs (default: 1)')
    parser.add_argument('--timeout', default=60, type=int, help='Timeout (default: 60)')
    args = parser.parse_args()
    return args


def _get_test_categories(args) -> LeaderboardCategories:
    if args.test_categories:
        categories = []
        for value in args.test_categories.split(','):
            if value not in LeaderboardCategory._value2member_map_:
                raise ValueError(f'Invalid test category: "{value}"!')
            categories.append(LeaderboardCategory(value))
        args.test_categories = categories
    return LeaderboardCategories(
        test_group=args.test_group, 
        test_categories=args.test_categories, 
        version=args.version
    )


def _get_model_handler(args) -> BaseHandler:
    if args.model_type == ModelType.OSS:
        from bfcl.model_handler.oss_model import MODEL_TO_HANDLER_CLS
    elif args.model_type == ModelType.PROPRIETARY:
        from bfcl.model_handler.proprietary_model import MODEL_TO_HANDLER_CLS
    
    assert (handler_cls := MODEL_TO_HANDLER_CLS.get(args.model)), \
        f'Invalid model name "{args.model}"! Please select a {args.model_type.value} model from {tuple(MODEL_TO_HANDLER_CLS)}'

    return handler_cls(
        model_name=args.model, 
        temperature=args.temperature,
        top_p=args.top_p,
        max_tokens=args.max_tokens,
    )


if __name__ == '__main__':
    
    main()