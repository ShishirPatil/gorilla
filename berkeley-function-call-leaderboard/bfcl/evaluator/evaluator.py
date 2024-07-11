import json
from pathlib import Path
from typing import List, Dict, Any

from pydantic import BaseModel

from bfcl.model_handler.base import BaseHandler
from bfcl.types import Leaderboard, LeaderboardCategory
from bfcl.evaluator.metrics import LeaderboardModelMetrics
from bfcl.evaluator import utils as evaluator_utils


class FailedResult(BaseModel):
    example_id: str
    test_category: str
    is_valid: bool
    error_type: str
    error_message: str
    llm_response: str
    decoded_result: Any


class LeaderboardEvaluator:
    def __init__(self, model_handler: BaseHandler, leaderboard: Leaderboard) -> None:
        self.model_name = model_handler.model_name
        self.model_handler = model_handler
        self.leaderboard = leaderboard
        self._model_metrics = LeaderboardModelMetrics(self.model_name)
        self._test_category_to_metrics = {}

    def __call__(self, file_path: Path, test_category) -> None:
        model_responses = self.model_handler.load_model_responses(file_path.name)
        if model_responses is None:
            print(f'Skipping evaluation of test category "{test_category.value}" due to empty model responses!')
            return

        if test_category == LeaderboardCategory.JAVA:
            language = 'java'
        elif test_category == LeaderboardCategory.JAVASCRIPT:
            language = 'javascript'
        else:
            language = 'python'

        print('🔍 Running test:', test_category.value)
        self._model_metrics(model_responses)

        accuracy = None
        if test_category == LeaderboardCategory.RELEVANCE:
            result = self.run_relevance_evaluator(model_responses)
            accuracy = result['accuracy']
            
        self._test_category_to_metrics[test_category] = dict(
            accuracy=accuracy, 
            total_count=result['total_count']
        )
        print(f"✅ Test completed: {test_category.value} | 🎯 Accuracy: {accuracy:.4f}")

    def get_leaderboard_metrics(self) -> Dict:
        model_metrics = self._model_metrics.compute()
        total_count = 0
        weighted_total_accuracy = unweighted_total_accuracy = 0
        test_category_to_accuracy = {}
        for test_category, metrics in self._test_category_to_metrics.items():
            test_category_to_accuracy[test_category.value] = metrics['accuracy']
            total_count += metrics['total_count']
            weighted_total_accuracy += metrics['accuracy'] * metrics['total_count']
            unweighted_total_accuracy += metrics['accuracy']
        return dict(
            overall_accuracy_weighted=weighted_total_accuracy / total_count,
            overall_accuracy_unweighted=unweighted_total_accuracy / len(self._test_category_to_metrics),
            **test_category_to_accuracy,
            **model_metrics,
        )

    def run_relevance_evaluator(self, model_responses: List[Dict]) -> Dict:
        """Run function relevance detection. 

        In relevance detection, we design a scenario where none of the provided functions 
        are relevant and supposed to be invoked. We expect the model's output to be no 
        function call."""

        failed_model_responses = []
        correct_count = 0
        for response in model_responses:
            model_response = response['response']
            success = False
            decoded_result = None
            try:
                decoded_result = self.model_handler.decode_ast(model_response, language='python')
                success = evaluator_utils.is_empty_output(decoded_result)
            except Exception:
                success = True

            if success:
                correct_count += 1
            else:
                result = FailedResult(
                    example_id=response['id'],
                    test_category=LeaderboardCategory.RELEVANCE.value,
                    is_valid=False,
                    error_type='relevance_error:decoder_success',
                    error_message='Valid syntax. Successfully decode AST when it should not.',
                    llm_response=model_response,
                    decoded_result=decoded_result,
                )
                failed_model_responses.append(result)
        
        result = dict(
            accuracy=correct_count / len(model_responses),
            correct_count=correct_count,
            total_count=len(model_responses),
            failed_model_responses=failed_model_responses,
        )
        self._save_scores(LeaderboardCategory.RELEVANCE, result)
        return result

    def _save_scores(self, test_category, result) -> None:
        if (
            (failed_model_responses := result.get('failed_model_responses'))
            and isinstance(failed_model_responses[0], FailedResult)
        ):
            result['failed_model_responses'] = [rp.model_dump() for rp in failed_model_responses]

        file_name = self.leaderboard.get_file_name(test_category).replace('.json', '_score.json')
        file_path = self.model_handler.model_dir / file_name
        file_path.write_text(json.dumps(result, indent=2))
        print(f'Saved {test_category.value} evaluation result at "{file_path}".')