import os
import argparse

from dotenv import load_dotenv

from bfcl.model_handler.base import BaseHandler, ModelStyle
from bfcl.types import (LeaderboardCategory, LeaderboardCategories,
                        LeaderboardVersion, ModelType)

load_dotenv()


def main() -> None:
    args = get_args()
    if os.getenv('USE_COHERE_OPTIMIZATION') and 'command-r-plus' in args.model:
        args.model += '-optimized'

    test_categories = _get_test_categories(args)
    model_handler = _get_model_handler(args)
    test_inputs = test_categories.load_data()
    if model_handler.model_style == ModelStyle.OSS_MODEL:
        responses = model_handler.inference(inputs=test_inputs, num_gpus=args.num_gpus)
        file_name = test_categories.output_file_path.name.replace('.jsonl', '_result.jsonl')
        model_handler.write(responses, file_name)
    else:
        raise NotImplementedError()


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
        choices=[category.value for category in ModelType], 
        default=ModelType.PROPRIETARY.value,
        help="Model type: Open-source or Proprietary (default: 'proprietary')"
    )
    parser.add_argument(
        '--test-category', 
        type=str, 
        default=LeaderboardCategory.ALL.value,
        help=(
            'Comma-separated list of test categories '
            f"({','.join(category.value for category in LeaderboardCategory)}). "
            "(default: 'all')"
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
    if args.test_category == LeaderboardCategory.ALL.value:
        categories = [category for category in LeaderboardCategory if category != LeaderboardCategory.ALL]
    else:
        categories = []
        for value in args.test_category.split(','):
            if value not in LeaderboardCategory._value2member_map_:
                raise ValueError(f'Invalid test category: "{value}"!')
            categories.append(LeaderboardCategory(value))
    return LeaderboardCategories(categories=categories, version=args.version)


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