import os
import argparse

from dotenv import load_dotenv

from bfcl.evaluation import evaluate
from bfcl.llm_generation import collect_model_responses
from bfcl.model_handler.base import BaseHandler
from bfcl.types import (LeaderboardCategory, Leaderboard, LeaderboardVersion, 
                        ModelType, LeaderboardCategoryGroup)

load_dotenv()


def main():
    args = _get_args()
    leaderboard = _load_leaderboard(args)
    model_handler = _load_model_handler(args)

    if args.command == 'llm_generation':
        collect_model_responses(leaderboard, model_handler, args)
    else:
        evaluate(leaderboard, model_handler, args)


def _get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog='bfcl',
        description='Berkeley Function Calling Leaderboard (BFCL)'
    )

    subparsers = parser.add_subparsers(dest='command', required=True, help='Sub-command to run')

    # Common arguments for both benchmark and evaluation
    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument(
        '--model', 
        type=str, 
        default='gorilla-openfunctions-v2',
        help="Name of the LLM. (default: 'gorilla-openfunctions-v2')"
    )
    common_parser.add_argument(
        '--model-type', 
        type=ModelType,
        choices=[mtype.value for mtype in ModelType], 
        default=ModelType.PROPRIETARY.value,
        help="Model type: Open-source or Proprietary (default: 'proprietary')"
    )
    common_parser.add_argument(
        '--test-group', 
        type=LeaderboardCategoryGroup, 
        choices=[group.value for group in LeaderboardCategoryGroup],
        default=None,
        help='Test category group (default: None)'
    )
    common_parser.add_argument(
        '--test-categories', 
        type=str, 
        default=None,
        help=(
            'Comma-separated list of test categories '
            f"({','.join(cat.value for cat in LeaderboardCategory)}). "
            "(default: None)"
        )
    )
    common_parser.add_argument(
        '--version', 
        type=LeaderboardVersion, 
        default=LeaderboardVersion.V1.value,
        choices=[category.value for category in LeaderboardVersion],
        help="Leaderboard version. (default: 'v1')",
    )

    _add_llm_generation_args(subparsers, common_parser)
    _add_evaluation_args(subparsers, common_parser)

    args = parser.parse_args()
    return args


def _add_llm_generation_args(subparsers, common_parser):
    """Add LLM generation specific arguments."""

    benchmark_parser = subparsers.add_parser('llm_generation', parents=[common_parser], help='Collect LLM responses')
    benchmark_parser.add_argument('--temperature', type=float, default=0.7, help='Temperature (default: 0.7)')
    benchmark_parser.add_argument('--top-p', type=float, default=1, help='Top-p (default: 1)')
    benchmark_parser.add_argument('--max-tokens', type=int, default=1000, help='Max tokens (default: 1000)')
    benchmark_parser.add_argument('--num-gpus', default=1, type=int, help='No. of GPUs (default: 1)')
    benchmark_parser.add_argument('--timeout', default=60, type=int, help='Timeout (default: 60)')


def _add_evaluation_args(subparsers, common_parser):
    """Add evaluation-specific arguments."""

    evaluator_parser = subparsers.add_parser('evaluation', parents=[common_parser], help='Run evaluation')
    evaluator_parser.add_argument(
        '--perform-api-sanity-check',
        action='store_true',
        default=False,
        help='Perform the REST API status sanity check before running the evaluation. (default: False)',
    )


def _load_leaderboard(args: argparse.Namespace) -> Leaderboard:
    if args.test_categories:
        categories = []
        for value in args.test_categories.split(','):
            if value not in LeaderboardCategory._value2member_map_:
                raise ValueError(f'Invalid test category: "{value}"!')
            categories.append(LeaderboardCategory(value))
        args.test_categories = categories
    return Leaderboard(
        test_group=args.test_group, 
        test_categories=args.test_categories, 
        version=args.version
    )


def _load_model_handler(args: argparse.Namespace) -> BaseHandler:
    if args.model_type == ModelType.OSS:
        from bfcl.model_handler.oss_model import MODEL_TO_HANDLER_CLS
    elif args.model_type == ModelType.PROPRIETARY:
        from bfcl.model_handler.proprietary_model import MODEL_TO_HANDLER_CLS
    
    if os.getenv('USE_COHERE_OPTIMIZATION') and 'command-r-plus' in args.model:
        args.model += '-optimized'
    
    assert (handler_cls := MODEL_TO_HANDLER_CLS.get(args.model)), (
        f'Invalid model name "{args.model}"! Please select a {args.model_type.value} '
        f'model from {tuple(MODEL_TO_HANDLER_CLS)}'
    )

    # This model handler function is shared by `benchmark` and `evaluate` functions
    # `evaluate` cli args doesn't required temperature, top_p and max_tokens,
    # since for evaluation we won't be calling the inference method.
    if hasattr(args, 'temperature'):
        return handler_cls(
            model_name=args.model, 
            temperature=args.temperature,
            top_p=args.top_p,
            max_tokens=args.max_tokens,
        )
    else:
        return handler_cls(model_name=args.model)


if __name__ == "__main__":    
    main()
