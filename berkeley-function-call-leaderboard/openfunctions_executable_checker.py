import os
import json
import re
import argparse
from data.REST_Eval.eval_exec_rest import is_exec_valid
from tqdm import tqdm

parser = argparse.ArgumentParser()
parser.add_argument(
    "--model_name", type=str, default="gpt-4-1106-preview"
   
)  # Refer to model_choice for supported models.
parser.add_argument(
     "--test_category", type=str, default="executable_generic"
)  # Refer to the type of testing data.
parser.add_argument(
    "--input_file", type=str, default= None
)  # Refer to the testing input file. It has the highest priority. 
parser.add_argument(
    "--log_store", action="store_true", default=False
)  # Refer to whether we want to log the result or not.
args = parser.parse_args()
if "executable" not in args.test_category and "rest" not in args.test_category:
    print("This script is only for executable testing.")
    exit()
model_name = args.model_name
test_category = args.test_category
input_file = args.input_file
log_store = args.log_store

def convert_to_function_call(data_str):
    """
    Parse OAI param list into executable function calls.
    """
    # Step 1: Remove the outer square brackets
    data_str = data_str[1:-1]
    data_str = data_str.split("}, {")
    output_func_list = []
    for func in data_str:
        # Step 2: Split the string into function name and parameters parts
        func_name_part, params_part = func.split(":", 1)

        # Step 3: Clean and extract the function name
        func_name = func_name_part.strip("{").strip(" '")

        # Step 4: Extract and clean the parameters string
        if params_part[-1] == "}":
            params_part = params_part[:-2]
        params_str = params_part.strip(" '")
        # Step 5: Replace single quotes with double quotes for JSON parsing
        params_str = params_str.replace("'", '"')
        params_str = params_str.replace("\\" + "n", "")
        # Step 6: Load the parameters string as a dictionary
        params = json.loads(params_str)
        function_string = func_name + "("
        for k,v in params.items():
            if isinstance(v, str):
               function_string += f"{k}=\"{v}\""
            else:
               function_string += f"{k}={v}"
            function_string += ","
        function_string = function_string[:-1] + ")"
        output_func_list.append(function_string)
    # Step 7: Format the function call
    return output_func_list

# Load the result file from the model and the testing data file.
result_data = []
if input_file:
    with open(input_file,"r") as f:
        for line in f:
            result_data.append(json.loads(line))
    gorilla_testing_data = []
    with open("eval_data_total.json","r") as f:
        for line in f:
            gorilla_testing_data.append(json.loads(line))
    new_example = []
    for i in range(len(gorilla_testing_data)):
        if gorilla_testing_data[i]["question_type"] == args.test_category:
            new_example.append(result_data[i])
    result_data = new_example
    num_existing_result = 0
else:
    for filename in os.listdir("./result/" + model_name):
        file_path = os.path.join("./result/" + model_name, filename)
        if "gorilla" in filename and test_category in filename:
            with open(file_path) as f:
                for line in f:
                    result_data.append(json.loads(line))
            break
    for i in range(len(result_data)):
        result = result_data[i]["result"]
        result = re.sub("functions.", "", str(result))
        result_data[i]["result"] = result
    num_existing_result = 0
    filename = filename.replace("_result.json", "_check_result.json")
    if os.path.exists("./result/" + model_name + "/check/" + filename):
        with open("./result/" + model_name + "/check/" + filename) as f:
            for line in f:
                num_existing_result += 1

# Load the testing data and execution result from the data folder.
testing_data = []
with open(f"./data/gorilla_openfunctions_v1_test_{test_category}.json") as f:
    for line in f:
        testing_data.append(json.loads(line))
total = 0
success = 0
if len(result_data) == 0:
    print(f"🙊 Your {model_name}'s {test_category} evaluation category data is not found, check whether you have finished openfunctions_evaluation.py evaluation data generation.")
    exit()
for i in tqdm(range(len(result_data))):
    # if i < num_existing_result:
    #     continue
    if "rest" not in test_category:
        execution_result = testing_data[i]["execution_result"]
        execution_result_type = testing_data[i]["execution_result_type"]
        if type(execution_result_type) is str and len(execution_result) > 1:
                execution_result_type = [execution_result_type] * len(execution_result)
    if ("gpt" in model_name or "fire" in model_name or "mistral-large-latest" in model_name) and     is None:
        try:
            result = convert_to_function_call(result_data[i]["result"])
        except:     
            total += 1
            continue
    if input_file is not None and "gorilla" in input_file:
        result = result_data[i]["text"] 
        print(result)
    if "gorilla-openfunctions-v2" in model_name:
        result = result_data[i]["result"]
        regex = r"\w+\([^()]*\)"
        # Find all matches of function calls
        result = re.findall(regex, result)
    if input_file is not None and "deepseek" in input_file:
        result_data[i]["text"] = result_data[i]["text"].replace("\n","")
        try:
            pattern = r"```python(.*?)```"
            pattern1 = r"```(.*?)```"

            # Search for the pattern in the text
            match = re.search(pattern, result_data[i]["text"], re.DOTALL)
            match1 = re.search(pattern1, result_data[i]["text"], re.DOTALL)

            if match:
                result = match.group(1).strip()
            elif match1:
                result = match1.group(1).strip()
            else:
                result = result_data[i]["text"]
            result = convert_to_function_call(result_data[i]["result"])
        except:
            pass
    elif "mistral-medium" == model_name or "mistral-tiny" == model_name or "mistral-small" == model_name:
        func = result_data[i]["result"]
        result = func.replace("\\_","_")
        if func.startswith("["):
            result = result[1:]
        if func.endswith("]"):
            result = result[:-1]
        result = result.split("),")
        result = [r + ")" for r in result]
        result[-1] = result[-1][:-1]
    elif "Nexus" in model_name:
        try:
            func = result_data[i]["result"].split("<human_end>\n \n")[1]
        except:
            total += 1
            continue
        if ";" in func:
            func = func.split(";")[:-1]
        if type(func) is list:
            func = [f[1:] if f[0] == " " else f for f in func]
        elif type(func) is str:
            func = [func]
        result = func
    elif "claude" in model_name:
        try:
            func = result_data[i]["result"]
        except:
            total += 1
            continue
        if " " == func[0]:
            func = func[1:]
        if func.startswith("["):
            func = func[1:]
        if func.endswith("]"):
            func = func[:-1]
        result = func.split("),")
        result = [r + ")" for r in result]
        result[-1] = result[-1][:-1]
    elif "glaiveai" in model_name or "glaiveai" in input_file:
        try:
            result_data[i]["text"] = json.loads(result_data[i]["text"].split("<functioncall>")[1].replace("\'{","{").replace("\'}","}"))
            result = result_data[i]["text"]["name"] + "(" + ",".join([f"{k}={v}" for k,v in result_data[i]["text"]["arguments"].items()]) + ")"
            if test_category == "miss_param" or test_category == "no_function_call" or test_category == "chatable":
                total += 1
                continue
        except Exception as e:
            if test_category == "miss_param" or test_category == "no_function_call" or test_category == "chatable":
                total += 1
                success += 1
                continue
            total += 1
            continue
    if type(result) == str:
            result = [result]
    exec_dict = {}
    test_result_list = []
    reason_list = []
    if "rest" in test_category:
        rest_result = is_exec_valid(result[0], i) 
        try:
            rest_result = is_exec_valid(result[0], i)
        except:
            total += 1
            continue
        if rest_result:
            success += 1
        total += 1
        continue
    if len(result) != len(execution_result):
        total += 1
        continue
    for function_call, exec_result in zip(result, execution_result):
        try:
            exec(
                "from data.function.gorilla_openfunctions_v1_test_function import *"
                + "\nresult="
                + function_call,
                exec_dict,
            )
            output = exec_dict["result"]
        except Exception as e:
            test_result_list.append(False)
            reason_list.append(str(e))
            continue
        if execution_result_type == "exact_match":
            test_result_list.append(output == exec_result or [output] == exec_result)
        else:
            try:
                test_result_list.append(type(output) == type(exec_result))
                reason_list.append(f"intended_result:{exec_result},code_result:{output}")
            except:
                test_result_list.append(False)
                reason_list.append(f"intended_result:{exec_result}")
    if False in test_result_list:
        match = False
        reason = reason_list
        total += 1
    else:
        match = True
        reason = ""
        total += 1
        success += 1
    if log_store:
        name = input_file if input_file else filename
        if os.path.exists("./result/" + model_name + "/check/") is False:
            os.mkdir("./result/" + model_name + "/check/")
        with open("./result/" + model_name + "/check/" + name, "a+") as f:
            f.write(json.dumps({"match": match, "reason": reason}))
            f.write("\n")
print(f"Testing type: {args.test_category}, success rate: {success/total}")