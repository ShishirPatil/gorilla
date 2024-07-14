import argparse
from pathlib import Path

from bfcl.evaluator import LeaderboardEvaluator
from bfcl.types import Leaderboard, LeaderboardCategory
from bfcl.model_handler.base import BaseHandler


def evaluate(
    leaderboard: Leaderboard, 
    model_handler: BaseHandler, 
    args: argparse.Namespace
) -> None:

    print('🦍 Model:', args.model)
    evaluator = LeaderboardEvaluator(
        model_handler=model_handler, 
        leaderboard=leaderboard,
        perform_api_sanity_check=args.perform_api_sanity_check
    )
    file_name_to_test_category = {}
    for test_category in leaderboard.test_categories:
        if test_category.value in (LeaderboardCategory.SQL.value, LeaderboardCategory.CHATABLE.value):
            print(f'Evaluation for test category "{test_category.value}" is not currently supported!')
        else:
            file_name = leaderboard.get_file_name(test_category)
            file_name_to_test_category[Path(file_name).stem] = test_category

    for file_path in model_handler.model_dir.glob('*.jsonl'):
        test_category = file_name_to_test_category.get(file_path.stem.replace('_result', ''))
        if test_category is None:
            continue
        evaluator(file_path, test_category)
    
    evaluator.generate_leaderboard_csv()
    print('🏁 Evaluation completed.')