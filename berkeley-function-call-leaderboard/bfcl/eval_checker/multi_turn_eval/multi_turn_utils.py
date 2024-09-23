import importlib
import inspect
import json
import re
import copy

CLASS_FILE_PATH_MAPPING = {
    "GorillaFileSystem": "bfcl.eval_checker.multi_turn_eval.func_source_code.gorilla_file_system",
    "MathAPI": "bfcl.eval_checker.multi_turn_eval.func_source_code.math_api",
    "MessageAPI": "bfcl.eval_checker.multi_turn_eval.func_source_code.message_api",
    "TwitterAPI": "bfcl.eval_checker.multi_turn_eval.func_source_code.posting_api",
    "TicketAPI": "bfcl.eval_checker.multi_turn_eval.func_source_code.ticket_api",
    "TradingBot": "bfcl.eval_checker.multi_turn_eval.func_source_code.trading_bot",
    "TravelAPI": "bfcl.eval_checker.multi_turn_eval.func_source_code.travel_booking",
    "VehicleControlAPI": "bfcl.eval_checker.multi_turn_eval.func_source_code.vehicle_control",
}

# These classes are stateless and do not require any initial configuration
STATELESS_CLASSES = [
    "MathAPI",
]


def execute_multi_turn_func_call(
    func_call_list: list[str],  # a list of strings of func calls
    initial_config: dict,
    involved_classes: list,
    model_name: str,
    test_entry_id: str,
    long_context: bool = False,
    is_evaL_run: bool = False,
) -> tuple[list[str], dict]:
    """
    TODO: Add docstring
    """
    if is_evaL_run:
        model_name += "_eval"

    class_method_name_mapping = {}
    involved_instances = {}
    for class_name in involved_classes:
        module_name = CLASS_FILE_PATH_MAPPING[class_name]
        # TODO: Handler the model name issue from handler more elegantly
        instance_name = (
            f"{model_name.replace('-', '_').replace('.', '_').replace('/', '_')}_{test_entry_id}_{class_name.lower()}_instance"
        )
        if instance_name not in globals():
            module = importlib.import_module(module_name)
            class_ = getattr(module, class_name)
            class_instance = class_()
            if class_name not in STATELESS_CLASSES:
                class_initial_config = initial_config.get(class_name, {})
                # Deep copy the initial configuration to avoid mutation issues
                class_instance._load_scenario(
                    copy.deepcopy(class_initial_config), long_context=long_context
                )
            globals()[instance_name] = class_instance
        # This happens in subsequent turns
        else:
            class_instance = globals()[instance_name]

        involved_instances[class_name] = class_instance

        # Retrieve all method names and map them to the instance
        for method_name, method in inspect.getmembers(
            class_instance, predicate=inspect.ismethod
        ):
            # Skip private methods
            if method_name.startswith("_"):
                continue
            class_method_name_mapping[method_name] = instance_name

    execution_results = []
    for func_call in func_call_list:
        # Add the instance name to the method calls
        func_call = _process_method_calls(func_call, class_method_name_mapping)

        # Evaluate the function call
        try:
            func_call_result = eval(func_call)
            execution_results.append(func_call_result)
        except Exception as e:
            execution_results.append(f"Error during execution: {str(e)}")

    for index in range(len(execution_results)):
        if type(execution_results[index]) == str:
            continue
        elif type(execution_results[index]) == dict:
            # Some function returns a object instance, which is not serializable
            try:
                execution_results[index] = json.dumps(execution_results[index])
            except:
                execution_results[index] = str(execution_results[index])
        else:
            execution_results[index] = str(execution_results[index])

    return execution_results, involved_instances


def is_empty_execute_response(input_list: list):
    if len(input_list) == 0:
        return True
    if len(input_list) == 1 and len(input_list[0]) == 0:
        return True
    return False


def _process_method_calls(function_call_string: str, instance_mapping: dict) -> str:
    """
    Prepends the instance name to the function name for each of the function name represented in the string, you will
    also be provided with the mapping of method name to instance name.

    Example input:
    ```
    f(x = g((1, 2), h(3)), y = (4), z = (5, 6))
    ```

    Example return:
    ```
    a.f(x=a.g((1, 2), a.h(3)), y=(4), z=(5, 6))
    ```

    Args:
        function_call_string (str): The function call string to parse.
        class_mapping (dict): A dictionary mapping method names to instance names.

    Returns:
        str: The parsed function call string with instance names prepended to method names.
    """

    def replace_function(match):
        func_name = match.group(1)
        if func_name in instance_mapping:
            return f"{instance_mapping[func_name]}.{func_name}"
        return func_name

    # Regular expression to match function names
    pattern = r"\b([a-zA-Z_]\w*)\s*(?=\()"

    # Replace function names with their class-prepended versions
    processed_string = re.sub(pattern, replace_function, function_call_string)

    return processed_string
