import json
import warnings
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
from tqdm import tqdm
from pydantic import BaseModel

import bfcl.types as types
from bfcl.model_handler.base import BaseHandler
from bfcl.evaluator.metrics import LeaderboardModelMetrics
from bfcl.evaluator import checker, utils as evaluator_utils
from bfcl.evaluator.constants import MODEL_METADATA_MAPPING


class FailedResult(BaseModel):
    example_id: str
    test_category: str
    is_valid: bool
    error_type: str
    error_message: str
    llm_response: str
    decoded_result: Any | None = None

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
        self.perform_api_sanity_check = perform_api_sanity_check
        self.test_category_to_data = leaderboard.load_test_data()

        self._executable_checker = None
        self._ast_checker = None
        self._model_metrics = LeaderboardModelMetrics(self.model_name)
        self._test_category_to_metrics = {}

    def __call__(self, file_path: Path, test_category) -> None:
        model_responses = self.model_handler.load_model_responses(file_path.name)
        if model_responses is None:
            print(f'Skipping evaluation of test category "{test_category.value}" due to empty model responses!')
            return

        print('🔍 Running test:', test_category.value)
        self._model_metrics(model_responses)

        result = None
        if test_category.value == types.LeaderboardCategory.RELEVANCE.value:
            result = self.run_relevance_evaluator(model_responses)
        elif test_category.value in types.LeaderboardExecutableCategory:
            if self._executable_checker is None:
                self._executable_checker = checker.ExecutableChecker(self.leaderboard.cache_dir)
                if self.perform_api_sanity_check:
                    self._executable_checker.perform_api_sanity_checks()
            result = self.run_executable_evaluator(test_category, model_responses)
        elif test_category.value in types.LeaderboardAstCategory:
            if self._ast_checker is None:
                self._ast_checker = checker.AstChecker(self.model_name, self.leaderboard)
            result = self.run_ast_evaluator(test_category, model_responses)
        
        if result:
            accuracy = result['accuracy']
            self._test_category_to_metrics[test_category.value] = dict(
                accuracy=accuracy, 
                total_count=result['total_count']
            )
            print(f"✅ Test completed: {test_category.value} | 🎯 Accuracy: {accuracy:.4f}")
    
    def generate_leaderboard_csv(self) -> None:
        metrics = self._test_category_to_metrics
        C = types.LeaderboardCategory

        python_simple_ast = metrics.get(C.SIMPLE.value, dict(accuracy=0, total_count=0))
        python_multiple_ast = metrics.get(C.MULTIPLE_FUNCTION.value, dict(accuracy=0, total_count=0))
        python_parallel_ast = metrics.get(C.PARALLEL_FUNCTION.value, dict(accuracy=0, total_count=0))
        python_parallel_multiple_ast = metrics.get(C.PARALLEL_MULTIPLE_FUNCTION.value, dict(accuracy=0, total_count=0))
        python_simple_exec = metrics.get(C.EXECUTABLE_SIMPLE.value, dict(accuracy=0, total_count=0))
        python_multiple_exec = metrics.get(C.EXECUTABLE_MULTIPLE_FUNCTION.value, dict(accuracy=0, total_count=0))
        python_parallel_exec = metrics.get(C.EXECUTABLE_PARALLEL_FUNCTION.value, dict(accuracy=0, total_count=0))
        python_parallel_multiple_exec = metrics.get(C.EXECUTABLE_PARALLEL_MULTIPLE_FUNCTION.value, dict(accuracy=0, total_count=0))
        java_simple_ast = metrics.get(C.JAVA.value, dict(accuracy=0, total_count=0))
        javascript_simple_ast = metrics.get(C.JAVASCRIPT.value, dict(accuracy=0, total_count=0))
        rest_simple_exec = metrics.get(C.REST.value, dict(accuracy=0, total_count=0))
        relevance = metrics.get(C.RELEVANCE.value, dict(accuracy=0, total_count=0))

        simple_ast = evaluator_utils.calculate_weighted_accuracy(
            [python_simple_ast, java_simple_ast, javascript_simple_ast]
        )
        multiple_ast = python_multiple_ast
        parallel_ast = python_parallel_ast
        parallel_multiple_ast = python_parallel_multiple_ast
        simple_exec = evaluator_utils.calculate_weighted_accuracy(
            [python_simple_exec, rest_simple_exec]
        )
        multiple_exec = python_multiple_exec
        parallel_exec = python_parallel_exec
        parallel_multiple_exec = python_parallel_multiple_exec

        summary_ast = evaluator_utils.calculate_unweighted_accuracy(
            [simple_ast, multiple_ast, parallel_ast, parallel_multiple_ast]
        )
        summary_exec = evaluator_utils.calculate_unweighted_accuracy(
            [simple_exec, multiple_exec, parallel_exec, parallel_multiple_exec]
        )
        overall_accuracy = evaluator_utils.calculate_weighted_accuracy(
            [
                simple_ast,
                multiple_ast,
                parallel_ast,
                parallel_multiple_ast,
                simple_exec,
                multiple_exec,
                parallel_exec,
                parallel_multiple_exec,
                relevance,
            ]
        )

        # if overall_accuracy["total_count"] != 1700:
        #     print("-" * 100)
        #     print(f"❗️Warning: Total count for {self.model_name} is {overall_accuracy['total_count']}")

        # Model metrics - cost, mean_latency, std_latency, p95_latency
        model_metrics = self._model_metrics.compute()
        model_metadata = MODEL_METADATA_MAPPING.get(self.model_name)
        if model_metadata is None:
            warnings.warn(
                f'Metadata not found for the model "{self.model_name}"! '
                'Please add your model metadata in the `MODEL_METADATA_MAPPING` variable '
                'in the `bfcl/evaluator/constants.py` file.'
            )
        
        f_acc = lambda acc: "{:.2f}%".format(acc * 100)
        rv_f_acc = lambda acc_str: float(acc_str.replace('%', '')) / 100
        
        row = {
            "Rank": 0, # Temporary value of 0. Updated below.
            "Overall Acc": f_acc(overall_accuracy["accuracy"]),
            "Model": model_metadata[0] if model_metadata else self.model_name,
            "Model Link": model_metadata[1] if model_metadata else "N/A",
            "Organization": model_metadata[2] if model_metadata else "N/A",
            "License": model_metadata[3] if model_metadata else "N/A",
            "AST Summary": f_acc(summary_ast["accuracy"]),
            "Exec Summary": f_acc(summary_exec["accuracy"]),
            "Simple Function AST": f_acc(simple_ast["accuracy"]),
            "Python Simple Function AST": f_acc(python_simple_ast["accuracy"]),
            "Java Simple Function AST": f_acc(java_simple_ast["accuracy"]),
            "JavaScript Simple Function AST": f_acc(javascript_simple_ast["accuracy"]),
            "Multiple Functions AST": f_acc(multiple_ast["accuracy"]),
            "Parallel Functions AST": f_acc(parallel_ast["accuracy"]),
            "Parallel Multiple AST": f_acc(parallel_multiple_ast["accuracy"]),
            "Simple Function Exec": f_acc(simple_exec["accuracy"]),
            "Python Simple Function Exec": f_acc(python_simple_exec["accuracy"]),
            "REST Simple Function Exec": f_acc(rest_simple_exec["accuracy"]),
            "Multiple Functions Exec": f_acc(multiple_exec["accuracy"]),
            "Parallel Functions Exec": f_acc(parallel_exec["accuracy"]),
            "Parallel Multiple Exec": f_acc(parallel_multiple_exec["accuracy"]),
            "Relevance Detection": f_acc(relevance["accuracy"]),
            "Cost ($ Per 1k Function Calls)": str(model_metrics['cost']),
            "Latency Mean (s)": str(model_metrics['mean_latency']),
            "Latency Standard Deviation (s)": str(model_metrics['std_latency']),
            "Latency 95th Percentile (s)": str(model_metrics['p95_latency']),
        }

        df_new = pd.DataFrame([row])
        file_path = self.model_handler.result_dir / 'BFCL_leaderboard_result.csv'
        if file_path.exists():
            print('Found existing BFCL leaderboard file! Loading...')
            existing_df = pd.read_csv(file_path, dtype=str)

            # Check if model name already exists
            if df_new["Model"].iloc[0] in existing_df["Model"].values:
                print('Model already exists. Overwriting the row...')
                existing_df.loc[existing_df["Model"] == df_new["Model"].iloc[0], :] = df_new.values
            else:
                print('Appending new model to the existing dataframe...')
                existing_df = pd.concat((existing_df, df_new), ignore_index=True)
            df = existing_df
        else:
            print('No existing BFCL leaderboard file found. Creating a new one...')
            df = df_new

        df["Overall Acc"] = df["Overall Acc"].apply(rv_f_acc)
        df.sort_values("Overall Acc", ascending=False, inplace=True)
        df["Overall Acc"] = df["Overall Acc"].apply(f_acc)
        df['Rank'] = list(range(1, len(df) + 1))

        df.to_csv(file_path, index=False)
        print(f'🔒 Saved BFCL leaderboard result at "{file_path}".')

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
        if test_category.value != types.LeaderboardExecutableCategory.REST.value:
            print(f"---- Getting real-time execution result from ground truth for '{test_category.value}' ----")
            exec_dict = {}
            for item in tqdm(test_data, desc="Getting Executable Expected Output"):
                execution_result = item.get('execution_result')
                if execution_result is None or not all(execution_result): # Check if cached value is None then try again.
                    execution_result = []
                    ground_truth = item["ground_truth"]
                    for i in range(len(ground_truth)):
                        exec(
                            "from bfcl.evaluator.checker.executable.exec_python_functions import *" 
                            + "\nresult=" + ground_truth[i],
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

            if test_category.value == types.LeaderboardExecutableCategory.REST.value:
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

                checker_result = self._executable_checker.rest_executable_checker(
                    decoded_result[0], 
                    eval_ground_truth=self._executable_checker.rest_eval_response_data[idx]
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

                checker_result = self._executable_checker.executable_checker(
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

    def run_ast_evaluator(
        self, 
        test_category: types.LeaderboardCategory, 
        model_responses: List[Dict]
    ) -> Dict:

        self._ast_checker.load_possible_answers(test_category)
        test_data = self.test_category_to_data[test_category]
        possible_answers = self._ast_checker.test_category_to_possible_ans[test_category]
        language = self._ast_checker.get_language(test_category)
        assert len(model_responses) == len(test_data) == len(possible_answers), (
            "No. of the model responses does not match the no. of test data or "
            "no. of possible answers. Please check the input files for completeness."
        )

        test_example_id_to_data = {data['id']: data for data in test_data}
        failed_model_responses = []
        correct_count = 0
        for idx, response in tqdm(enumerate(model_responses), total=len(model_responses), desc="Evaluating"):
            model_result_item = response['response']
            possible_answer_item = possible_answers[idx]

            try:
                model_result_item_raw = model_result_item
                model_result_item = self.model_handler.decode_ast(model_result_item, language)
            except Exception as e:
                failed_model_responses.append(
                    FailedResult(
                        example_id=response['id'],
                        test_category=test_category.value,
                        is_valid=False,
                        error_message=f"Invalid syntax. Failed to decode AST. {str(e)}",
                        error_type="ast_decoder:decoder_failed",
                        llm_response=model_result_item_raw,
                        possible_answer=possible_answer_item,
                    )
                )
                continue

            decoder_output_valid = evaluator_utils.is_function_calling_format_output(model_result_item)
            if not decoder_output_valid:
                failed_model_responses.append(
                    FailedResult(
                        example_id=response['id'],
                        test_category=test_category.value,
                        is_valid=False,
                        error_message="Did not output in the specified format. Note: the model_result is wrapped in a string to ensure json serializability.",
                        error_type="ast_decoder:decoder_wrong_output_format",
                        llm_response=str(model_result_item_raw),
                        decoded_result=str(model_result_item),
                        possible_answer=possible_answer_item,
                    )
                )
                continue

            checker_result = self._ast_checker(
                idx,
                test_example_id_to_data[response['id']]['function'],
                model_result_item,
                test_category,
            )

            if checker_result.is_valid:
                correct_count += 1
            else:
                failed_model_responses.append(
                    FailedResult(
                        example_id=response['id'],
                        test_category=test_category.value,
                        is_valid=checker_result.is_valid,
                        error_message=checker_result.error_message,
                        error_type=checker_result.error_type,
                        llm_response=model_result_item_raw,
                        decoded_result=model_result_item,
                        possible_answer=possible_answer_item,
                    )
                )
        
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