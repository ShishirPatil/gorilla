import json
import time

from bfcl.constant import RESULT_PATH, VERSION_PREFIX
from bfcl.eval_checker.multi_turn_eval.multi_turn_utils import (
    execute_multi_turn_func_call,
    is_empty_execute_response,
)
from bfcl.model_handler.constant import (
    DEFAULT_USER_PROMPT_FOR_ADDITIONAL_FUNCTION_FC,
    DEFAULT_USER_PROMPT_FOR_ADDITIONAL_FUNCTION_PROMPTING,
    MAXIMUM_ROUND_LIMIT,
)
from bfcl.model_handler.model_style import ModelStyle


class BaseHandler:
    model_name: str
    model_style: ModelStyle

    def __init__(self, model_name, temperature) -> None:
        self.model_name = model_name
        # Replace the slash with underscore to avoid creating subdirectories
        # Replace the dash and dot with underscore for valid variable name
        self.model_name_underline_replaced = (
            model_name.replace("/", "_").replace("-", "_").replace(".", "_")
        )
        self.temperature = temperature
        self.is_fc_model = False  # Whether the model is a function calling model

    def inference(self, test_entry: dict, include_debugging_log: bool):
        # This method is used to retrive model response for each model.

        # FC model
        # TODO: Let all models have the is_fc_model attribute and remove the "FC" check
        if "FC" in self.model_name or self.is_fc_model:
            if "multi_turn" in test_entry["id"]:
                return self.inference_multi_turn_FC(test_entry, include_debugging_log)
            else:
                return self.inference_single_turn_FC(test_entry, include_debugging_log)
        # Prompting model
        else:
            if "multi_turn" in test_entry["id"]:
                return self.inference_multi_turn_prompting(
                    test_entry, include_debugging_log
                )
            else:
                return self.inference_single_turn_prompting(
                    test_entry, include_debugging_log
                )

    def inference_multi_turn_FC(
        self, test_entry: dict, include_debugging_log: bool
    ) -> tuple[list[list], dict]:
        initial_config: dict = test_entry["initial_config"]
        involved_classes: list = test_entry["involved_classes"]
        test_entry_id: str = test_entry["id"]
        test_category: str = test_entry_id.rsplit("_", 1)[0]

        # This is only for the miss function category
        # A mapping from turn index to function to holdout
        holdout_function: dict[int, list] = test_entry.get("missed_function", {})

        total_input_token_count: list[list[float]] = []
        total_output_token_count: list[list[float]] = []
        total_latency: list[list[float]] = []
        all_model_response: list[list] = (
            []
        )  # The model response that will be used for later evaluation
        all_debugging_log: list[list[dict]] = (
            []
        )  # The debugging log for human to understand
        force_quit = False  # Whether the model has been forced to quit. If True, this whole entry will be failed.

        inference_data: dict = {}
        inference_data = self._pre_query_processing_FC(inference_data, test_entry)
        inference_data = self._compile_tools(inference_data, test_entry)

        all_multi_turn_messages: list[list[dict]] = test_entry["question"]
        for round_idx, current_round_message in enumerate(all_multi_turn_messages):
            current_round_message: list[dict]

            if str(round_idx) in holdout_function:
                test_entry["function"].extend(holdout_function[str(round_idx)])
                # Since we have added new functions, we need to recompile the tools
                inference_data = self._compile_tools(inference_data, test_entry)
                assert (
                    len(current_round_message) == 0
                ), "Holdout round should not have user message."
                current_round_message = [
                    {
                        "role": "user",
                        "content": DEFAULT_USER_PROMPT_FOR_ADDITIONAL_FUNCTION_FC,
                    }
                ]

            if round_idx == 0:
                inference_data = self.add_first_turn_message_FC(
                    inference_data, current_round_message
                )
            else:
                inference_data = self._add_next_turn_user_message_FC(
                    inference_data, current_round_message
                )

            current_round_response = []
            current_round_debugging_log: list[dict] = [current_round_message]
            current_round_input_token_count: list[float] = []
            current_round_output_token_count: list[float] = []
            current_round_latency: list[float] = []

            count = 0
            while True:
                print("-" * 100)
                print(
                    f"ID: {test_entry_id.rsplit('_', 1)[1]}, Round: {round_idx}, Count: {count}"
                )

                start_time = time.time()
                api_response = self._query_FC(inference_data)
                query_latency = time.time() - start_time

                current_round_debugging_log.append(
                    {
                        "role": "handler_log:inference_input",
                        "content": inference_data.get("inference_input_log", ""),
                    }
                )

                # Try parsing the model response
                model_response_data = self._parse_query_response_FC(api_response)
                model_responses = model_response_data["model_responses"]

                # Add the assistant message to the chat history
                inference_data = self._add_assistant_message_FC(
                    inference_data, model_response_data
                )

                # Process the metadata
                current_round_input_token_count.append(model_response_data["input_token"])
                current_round_output_token_count.append(model_response_data["output_token"])
                current_round_latency.append(query_latency)

                # Try decoding the model response
                try:
                    decoded_model_responses = self.decode_execute(model_responses)

                    if is_empty_execute_response(decoded_model_responses):
                        print("Empty response from the model. Proceed to next turn.")
                        current_round_debugging_log.append(
                            {
                                "role": "handler_log",
                                "content": f"Empty response from the model. Proceed to next turn. Model response decoded: {decoded_model_responses}. Model response raw: {model_responses}",
                            }
                        )
                        break

                except Exception as e:
                    print("Failed to decode the model response. Proceed to next turn.")
                    current_round_debugging_log.append(
                        {
                            "role": "handler_log",
                            "content": f"Error decoding the model response. Proceed to next turn. Error: {e}. Model response: {model_responses}.",
                        }
                    )
                    break

                finally:
                    current_round_response.append(model_responses)

                current_round_debugging_log.append(
                    {
                        "role": "handler_log",
                        "content": f"Decoded: {decoded_model_responses}. Raw: {model_responses}",
                    }
                )

                # Obtain the execution results
                execution_results, involved_instances = execute_multi_turn_func_call(
                    decoded_model_responses,
                    initial_config,
                    involved_classes,
                    self.model_name_underline_replaced,
                    test_entry_id,
                    long_context=("long_context" in test_category or "composite" in test_category),
                    is_evaL_run=False,
                )

                # Add the execution results to the chat history for the next round
                inference_data = self._add_execution_results_FC(
                    inference_data, execution_results, model_response_data
                )

                for execution_result in execution_results:
                    current_round_debugging_log.append(
                        {
                            "role": "tool",
                            "content": execution_result,
                        }
                    )

                count += 1
                # Force quit after too many rounds
                if count > MAXIMUM_ROUND_LIMIT:
                    force_quit = True
                    current_round_debugging_log.append(
                        {
                            "role": "handler_log",
                            "content": f"Model has been forced to quit after {MAXIMUM_ROUND_LIMIT} rounds.",
                        }
                    )
                    break

            # Add to the total list
            all_model_response.append(current_round_response)
            all_debugging_log.append(current_round_debugging_log)
            total_input_token_count.append(current_round_input_token_count)
            total_output_token_count.append(current_round_output_token_count)
            total_latency.append(current_round_latency)

            if force_quit:
                break

        metadata = {}
        if include_debugging_log:
            metadata["debugging_log"] = all_debugging_log
        metadata["input_token_count"] = total_input_token_count
        metadata["output_token_count"] = total_output_token_count
        metadata["latency"] = total_latency

        return all_model_response, metadata

    def inference_multi_turn_prompting(
        self, test_entry: dict, include_debugging_log: bool
    ) -> tuple[list[list], dict]:
        initial_config: dict = test_entry["initial_config"]
        involved_classes: list = test_entry["involved_classes"]
        test_entry_id: str = test_entry["id"]
        test_category: str = test_entry_id.rsplit("_", 1)[0]

        # This is only for the miss function category
        # A mapping from turn index to function to holdout
        holdout_function: dict[int, list] = test_entry.get("missed_function", {})

        total_input_token_count: list[list[float]] = []
        total_output_token_count: list[list[float]] = []
        total_latency: list[list[float]] = []
        all_model_response: list[list] = (
            []
        )  # The model response that will be used for later evaluation
        all_debugging_log: list[list[dict]] = (
            []
        )  # The debugging log for human to understand
        force_quit = False  # Whether the model has been forced to quit. If True, this whole entry will be failed.

        inference_data: dict = self._pre_query_processing_prompting(test_entry)

        all_multi_turn_messages: list[list[dict]] = test_entry["question"]
        for round_idx, current_round_message in enumerate(all_multi_turn_messages):
            current_round_message: list[dict]

            if str(round_idx) in holdout_function:
                assert (
                    len(current_round_message) == 0
                ), "Holdout round should not have user message."
                current_round_message = [
                    {
                        "role": "user",
                        "content": DEFAULT_USER_PROMPT_FOR_ADDITIONAL_FUNCTION_PROMPTING.format(
                            functions=holdout_function[str(round_idx)]
                        ),
                    }
                ]

            if round_idx == 0:
                inference_data = self.add_first_turn_message_prompting(
                    inference_data, current_round_message
                )
            else:
                inference_data = self._add_next_turn_user_message_prompting(
                    inference_data, current_round_message
                )

            current_round_response = []
            current_round_debugging_log: list[dict] = [current_round_message]
            current_round_input_token_count: list[float] = []
            current_round_output_token_count: list[float] = []
            current_round_latency: list[float] = []

            count = 0
            while True:
                print("-" * 100)
                print(
                    f"ID: {test_entry_id.rsplit('_', 1)[1]}, Round: {round_idx}, Count: {count}"
                )

                start_time = time.time()
                api_response = self._query_prompting(inference_data)
                query_latency = time.time() - start_time
                current_round_debugging_log.append(
                    {
                        "role": "handler_log:inference_input",
                        "content": inference_data["inference_input_log"],
                    }
                )

                # Try parsing the model response
                model_response_data = self._parse_query_response_prompting(api_response)
                model_responses = model_response_data["model_responses"]

                # Add the assistant message to the chat history
                inference_data = self._add_assistant_message_prompting(
                    inference_data, model_response_data
                )

                # Process the metadata
                current_round_input_token_count.append(model_response_data["input_token"])
                current_round_output_token_count.append(model_response_data["output_token"])
                current_round_latency.append(query_latency)

                # Try decoding the model response
                try:
                    decoded_model_responses = self.decode_execute(model_responses)
                    model_response_data["model_responses_decoded"] = decoded_model_responses
                    if is_empty_execute_response(decoded_model_responses):
                        print("Empty response from the model. Proceed to next turn.")
                        current_round_debugging_log.append(
                            {
                                "role": "handler_log",
                                "content": f"Empty response from the model. Proceed to next turn. Model response decoded: {decoded_model_responses}. Model response raw: {model_responses}",
                            }
                        )
                        break

                except Exception as e:
                    print("Failed to decode the model response. Proceed to next turn.")
                    current_round_debugging_log.append(
                        {
                            "role": "handler_log",
                            "content": f"Error decoding the model response. Proceed to next turn. Error: {e}. Model response: {model_responses}.",
                        }
                    )
                    break

                finally:
                    current_round_response.append(model_responses)

                current_round_debugging_log.append(
                    {
                        "role": "handler_log",
                        "content": f"Decoded: {decoded_model_responses}. Raw: {model_responses}",
                    }
                )

                # Obtain the execution results
                execution_results, involved_instances = execute_multi_turn_func_call(
                    decoded_model_responses,
                    initial_config,
                    involved_classes,
                    self.model_name_underline_replaced,
                    test_entry_id,
                    long_context=("long_context" in test_category or "composite" in test_category),
                    is_evaL_run=False,
                )

                # Add the execution results to the chat history for the next round
                inference_data = self._add_execution_results_prompting(
                    inference_data, execution_results, model_response_data
                )

                for execution_result in execution_results:
                    current_round_debugging_log.append(
                        {
                            "role": "tool",
                            "content": execution_result,
                        }
                    )

                count += 1
                # Force quit after too many rounds
                if count > MAXIMUM_ROUND_LIMIT:
                    force_quit = True
                    current_round_debugging_log.append(
                        {
                            "role": "handler_log",
                            "content": f"Model has been forced to quit after {MAXIMUM_ROUND_LIMIT} rounds.",
                        }
                    )
                    break

            # Add to the total list
            all_model_response.append(current_round_response)
            all_debugging_log.append(current_round_debugging_log)
            total_input_token_count.append(current_round_input_token_count)
            total_output_token_count.append(current_round_output_token_count)
            total_latency.append(current_round_latency)

            if force_quit:
                break

        metadata = {}
        if include_debugging_log:
            metadata["debugging_log"] = all_debugging_log
        metadata["input_token_count"] = total_input_token_count
        metadata["output_token_count"] = total_output_token_count
        metadata["latency"] = total_latency

        return all_model_response, metadata

    def inference_single_turn_FC(
        self, test_entry: dict, include_debugging_log: bool
    ) -> tuple[any, dict]:
        inference_data: dict = {}
        inference_data = self._pre_query_processing_FC(inference_data, test_entry)
        inference_data = self._compile_tools(inference_data, test_entry)
        inference_data = self.add_first_turn_message_FC(
            inference_data, test_entry["question"][0]
        )

        start_time = time.time()
        api_response = self._query_FC(inference_data)
        query_latency = time.time() - start_time

        # Try parsing the model response
        model_response_data = self._parse_query_response_FC(api_response)

        # Process the metadata
        metadata = {}
        if include_debugging_log:
            metadata["debugging_log"] = [
                {
                    "role": "handler_log:inference_input",
                    "content": inference_data["inference_input_log"],
                }
            ]
        metadata["input_token_count"] = model_response_data["input_token"]
        metadata["output_token_count"] = model_response_data["output_token"]
        metadata["latency"] = query_latency

        return model_response_data["model_responses"], metadata

    def inference_single_turn_prompting(
        self, test_entry: dict, include_debugging_log: bool
    ) -> tuple[any, dict]:
        inference_data: dict = self._pre_query_processing_prompting(test_entry)
        inference_data = self.add_first_turn_message_prompting(
            inference_data, test_entry["question"][0]
        )

        start_time = time.time()
        api_response = self._query_prompting(inference_data)
        query_latency = time.time() - start_time

        # Try parsing the model response
        model_response_data = self._parse_query_response_prompting(api_response)

        # Process the metadata
        metadata = {}
        if include_debugging_log:
            metadata["debugging_log"] = [
                {
                    "role": "handler_log:inference_input",
                    "content": inference_data["inference_input_log"],
                }
            ]
        metadata["input_token_count"] = model_response_data["input_token"]
        metadata["output_token_count"] = model_response_data["output_token"]
        metadata["latency"] = query_latency

        return model_response_data["model_responses"], metadata

    def decode_ast(self, result, language="Python"):
        # This method takes raw model output and convert it to standard AST checker input.
        raise NotImplementedError

    def decode_execute(self, result):
        # This method takes raw model output and convert it to standard execute checker input.
        raise NotImplementedError

    def write(self, result):
        model_name_dir = self.model_name.replace("/", "_")
        model_result_dir = RESULT_PATH / model_name_dir
        model_result_dir.mkdir(parents=True, exist_ok=True)

        if type(result) is dict:
            result = [result]

        for entry in result:
            test_category = entry["id"].rsplit("_", 1)[0]
            file_to_write = f"{VERSION_PREFIX}_{test_category}_result.json"
            file_to_write = model_result_dir / file_to_write
            with open(file_to_write, "a+") as f:
                try:
                    f.write(json.dumps(entry) + "\n")
                except Exception as e:
                    print(f"❗️Failed to write result: {e}")
                    f.write(
                        json.dumps(
                            {
                                "id": entry["id"],
                                "result": repr(entry),
                            }
                        )
                        + "\n"
                    )

    #### FC methods ####

    def _query_FC(self, inference_data: dict):
        """
        Call the model API in FC mode to get the response.
        Return the response object that can be used to feed into the decode method.
        """
        raise NotImplementedError

    def _pre_query_processing_FC(self, inference_data: dict, test_entry: dict) -> dict:
        """
        Preprocess the testset entry before sending it to the model.
        This includes transforming the input user message into the format expected by the model, and any other necessary preprocessing steps.
        The inference_data dict is updated in place and returned.
        """
        raise NotImplementedError

    def _compile_tools(self, inference_data: dict, test_entry: dict) -> dict:
        """
        Compile the tools from the test entry and add them to the inference data.
        This method is used to prepare the tools for the model query in FC mode.
        The inference_data dict is updated in place and returned.
        """
        raise NotImplementedError

    def _parse_query_response_FC(self, api_response: any) -> dict:
        """
        Parses the raw response from the model API to extract the result, input token count, and output token count.

        Args:
            api_response (any): The raw response from the model API.

        Returns:
            A dict containing the following elements:
                - model_responses (any): The parsed result that can be directly used as input to the decode method.
                - input_token (int): The number of tokens used in the input to the model.
                - output_token (int): The number of tokens generated by the model as output.
                - tool_call_ids (list[str]): The IDs of the tool calls that are generated by the model. Optional.
                - Any other metadata that is specific to the model.
        """
        raise NotImplementedError

    def add_first_turn_message_FC(
        self, inference_data: dict, first_turn_message: list[dict]
    ) -> dict:
        """
        Add the first turn message to the chat history.
        """
        raise NotImplementedError

    def _add_next_turn_user_message_FC(
        self, inference_data: dict, user_message: list[dict]
    ) -> dict:
        """
        [Only for multi-turn]
        Add next round user message to the chat history for query.
        user_message is a list of 1 element, which is the user message.
        """
        raise NotImplementedError

    def _add_assistant_message_FC(
        self, inference_data: dict, model_response_data: dict
    ) -> dict:
        """
        Add assistant message to the chat history.
        """
        raise NotImplementedError

    def _add_execution_results_FC(
        self, inference_data: dict, execution_results: list[str], model_response_data: dict
    ) -> dict:
        """
        Add the execution results to the chat history to prepare for the next round of query.
        Some models may need to add additional information to the chat history, such as tool call IDs.
        """
        raise NotImplementedError

    #### Prompting methods ####

    def _query_prompting(self, inference_data: dict):
        """
        Call the model API in prompting mode to get the response.
        Return the response object that can be used to feed into the decode method.
        """
        raise NotImplementedError

    def _pre_query_processing_prompting(self, test_entry: dict) -> dict:
        """
        Preprocess the testset entry before sending it to the model.
        Returns a dict that contains all the necessary information for the query method.
        `tools` and `message` must be included in the returned dict.
        Things like `system_prompt` and `chat_history` are optional, specific to the model.
        """
        raise NotImplementedError

    def _parse_query_response_prompting(self, api_response: any) -> dict:
        """
        Parses the raw response from the model API to extract the result, input token count, and output token count.

        Args:
            api_response (any): The raw response from the model API.

        Returns:
            A dict containing the following elements:
                - model_responses (any): The parsed result that can be directly used as input to the decode method.
                - input_token (int): The number of tokens used in the input to the model.
                - output_token (int): The number of tokens generated by the model as output.
                - tool_call_ids (list[str]): The IDs of the tool calls that are generated by the model. Optional.
                - Any other metadata that is specific to the model.
        """
        raise NotImplementedError

    def add_first_turn_message_prompting(
        self, inference_data: dict, first_turn_message: list[dict]
    ) -> dict:
        """
        Add the first turn message to the chat history.
        """
        raise NotImplementedError

    def _add_next_turn_user_message_prompting(
        self, inference_data: dict, user_message: list[dict]
    ) -> dict:
        """
        [Only for multi-turn]
        Add next round user message to the chat history for query.
        user_message is a list of 1 element, which is the user message.
        """
        raise NotImplementedError

    def _add_assistant_message_prompting(
        self, inference_data: dict, model_response_data: dict
    ) -> dict:
        """
        Add assistant message to the chat history.
        """
        raise NotImplementedError

    def _add_execution_results_prompting(
        self, inference_data: dict, execution_results: list[str], model_response_data: dict
    ) -> dict:
        """
        Add the execution results to the chat history to prepare for the next round of query.
        Some models may need to add additional information to the chat history, such as tool call IDs.
        """
        raise NotImplementedError
