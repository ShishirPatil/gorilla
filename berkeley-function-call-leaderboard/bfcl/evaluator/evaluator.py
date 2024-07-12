import json
from pathlib import Path
from typing import List, Dict, Any

from tqdm import tqdm
from pydantic import BaseModel

import bfcl.types as types
from bfcl.model_handler.base import BaseHandler
from bfcl.evaluator.metrics import LeaderboardModelMetrics
from bfcl.evaluator.checker import ExecutableChecker
from bfcl.evaluator import utils as evaluator_utils


class FailedResult(BaseModel):
    example_id: str
    test_category: str
    is_valid: bool
    error_type: str
    error_message: str
    llm_response: str
    decoded_result: Any

    class Config:
        extra = 'allow'


class LeaderboardEvaluator:
    def __init__(
        self, 
        model_handler: BaseHandler, 
        leaderboard: types.Leaderboard,
        perform_api_sanity_check: bool
    ) -> None:
        self.model_name = model_handler.model_name
        self.model_handler = model_handler
        self.leaderboard = leaderboard
        self.test_category_to_data = leaderboard.load_test_data()

        self._checker = ExecutableChecker(leaderboard.cache_dir)
        if perform_api_sanity_check:
            self._checker.perform_api_sanity_checks()
        self._model_metrics = LeaderboardModelMetrics(self.model_name)
        self._test_category_to_metrics = {}

    def __call__(self, file_path: Path, test_category) -> None:
        model_responses = self.model_handler.load_model_responses(file_path.name)
        if model_responses is None:
            print(f'Skipping evaluation of test category "{test_category.value}" due to empty model responses!')
            return

        if test_category == types.LeaderboardCategory.JAVA:
            language = 'java'
        elif test_category == types.LeaderboardCategory.JAVASCRIPT:
            language = 'javascript'
        else:
            language = 'python'

        print('🔍 Running test:', test_category.value)
        self._model_metrics(model_responses)

        result = None
        if test_category == types.LeaderboardCategory.RELEVANCE:
            result = self.run_relevance_evaluator(model_responses)
        elif test_category.value in types.LeaderboardExecutableCategory:
            result = self.run_executable_evaluator(test_category, model_responses)
        
        if result:
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
        for response in tqdm(model_responses, total=len(model_responses), desc="Evaluating"):
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
                    test_category=types.LeaderboardCategory.RELEVANCE.value,
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
        self._save_scores(types.LeaderboardCategory.RELEVANCE, result)
        return result

    def run_executable_evaluator(
        self, 
        test_category: types.LeaderboardCategory, 
        model_responses: List[Dict]
    ) -> Dict:
        """Run executable function/API evaluator.
        
        Invoke function or API for the documentation provided. The accuracy 
        is measured by actually running the function call with function 
        source code loaded."""

        test_data = self.test_category_to_data[test_category]
        assert len(model_responses) == len(test_data)
        test_example_id_to_data = {}
        if test_category != types.LeaderboardExecutableCategory.REST:
            print(f"---- Getting real-time execution result from ground truth for '{test_category.value}' ----")
            exec_dict = {}
            for item in tqdm(test_data, desc="Getting Executable Expected Output"):
                execution_result = item.get('execution_result')
                if execution_result is None or not all(execution_result): # Check if cached value is None then try again.
                    execution_result = []
                    ground_truth = item["ground_truth"]
                    for i in range(len(ground_truth)):
                        exec(
                            "from bfcl.evaluator.exec_python_functions import *" + "\nresult=" + ground_truth[i],
                            exec_dict,
                        )
                        execution_result.append(exec_dict["result"])
                    item["execution_result"] = execution_result
                test_example_id_to_data[item['id']] = item
            
            # Save the test dataset with the added `execution_result` key
            # TODO: Decide if you want to cache the execution results or not.
            # Edge case: We don't validate the `execution_result` value, hence if the user didn't setup the 
            # environment variables correctly and we get incorrect `execution_result` from the 
            # `exec_python_functions`, those values will be cached.
            file_path = self.leaderboard.test_data_cache_dir / self.leaderboard.get_file_name(test_category)
            with open(file_path, 'w') as file:
                for line in test_data:
                    file.write(json.dumps(line) + '\n')

            print(f"---- Ground truth real-time execution result obtained for '{test_category.value}' 🌟 ----")

        failed_model_responses = []
        correct_count = 0
        for idx, response in tqdm(enumerate(model_responses), total=len(model_responses), desc="Evaluating"):
            model_response = response['response']
            try:
                decoded_result = self.model_handler.decode_execute(model_response)
            except Exception as e:
                result = FailedResult(
                    example_id=response['id'],
                    test_category=test_category.value,
                    is_valid=False,
                    error_type='executable_decoder:decoder_failed',
                    error_message=f"Failed to decode executable. {str(e)}",
                    llm_response=model_response,
                    decoded_result=decoded_result,
                )
                failed_model_responses.append(result)
                continue

            if test_category == types.LeaderboardExecutableCategory.REST:
                # REST is always single-functioned. Therefore we take the first one and pass 
                # it to the REST checker.
                if not evaluator_utils.is_rest_format_output(decoded_result):
                    result = FailedResult(
                        example_id=response['id'],
                        test_category=test_category.value,
                        is_valid=False,
                        error_type='executable_decoder:rest_wrong_output_format',
                        error_message=(
                            'Did not output in the specified format. Note: the model_result is wrapped in a '
                            'string to ensure json serializability.'
                        ),
                        llm_response=str(model_response),
                        decoded_result=str(decoded_result),
                    )
                    failed_model_responses.append(result)
                    continue

                checker_result = self._checker.rest_executable_checker(
                    decoded_result[0], 
                    eval_ground_truth=self._checker.rest_eval_response_data[idx]
                )
            else:
                if not evaluator_utils.is_executable_format_output(decoded_result):
                    result = FailedResult(
                        example_id=response['id'],
                        test_category=test_category.value,
                        is_valid=False,
                        error_type='executable_decoder:wrong_output_format',
                        error_message=(
                            'Did not output in the specified format. Note: the model_result is wrapped in a '
                            'string to ensure json serializability.'
                        ),
                        llm_response=str(model_response),
                        decoded_result=str(decoded_result),
                    )
                    failed_model_responses.append(result)
                    continue

                checker_result = self._checker.executable_checker(
                    decoded_result, 
                    test_example_id_to_data[response['id']], 
                    test_category
                )

            if checker_result.is_valid:
                correct_count += 1
            else:
                result = FailedResult(
                    example_id=response['id'],
                    test_category=test_category.value,
                    is_valid=checker_result.is_valid,
                    error_type=checker_result.error_type,
                    error_message=checker_result.error_message,
                    llm_response=model_response,
                    decoded_result=decoded_result,
                )
                if hasattr(checker_result, "model_executed_output"):
                    result.model_executed_output = checker_result.model_executed_output
                failed_model_responses.append(result)

        result = dict(
            accuracy=correct_count / len(model_responses),
            correct_count=correct_count,
            total_count=len(model_responses),
            failed_model_responses=failed_model_responses,
        )
        self._save_scores(test_category, result)
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