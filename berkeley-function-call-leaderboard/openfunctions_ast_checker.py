import json
from json.decoder import JSONDecodeError
import ast
import os 
import argparse
import re
def get_args():
    parser = argparse.ArgumentParser()
    # Refer to model_choice for supported models.
    parser.add_argument("--model", type=str, default="gpt-4-1106-preview")
    # Refer to test_categories for supported categories.
    parser.add_argument("--test_category", type=str, default="multiple_function")

    # If file name, that means we are testing it. It has the highest priority.
    parser.add_argument("--file_name", type=str, default=None)
    # Whether the run will be used for output analysis. 
    parser.add_argument("--output_analysis", action="store_true", default=False)
    #Store the log whether each eval data is correct or not
    parser.add_argument("--log_store", action="store_true", default=False)

    args = parser.parse_args()
    return args
args = get_args() 
if "executable" in args.test_category:
    print("This script is not designed to handle executable test categories.")
    exit() 
# File name for input data
if args.file_name is None:
    file_name= f"./result/{args.model}/gorilla_openfunctions_v1_test_{args.test_category}_result.json"
    # file_name= "./result/gpt-4-1106-preview/gorilla_openfunctions_v1_test_multiple_function_result.json"
else:
    file_name = args.file_name
output_analysis = args.output_analysis # Set to True to output analysis of the results

# File name for possible answer
possible_answer_file = f"./data/possible_answer/gorilla_openfunctions_v1_test_{args.test_category}.json"

# Build AST Tree from the input string
def build_ast(content):
    tree = ast.parse(content)
    # add parent attribute to each node
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            child.parent = node
    # astpretty.pprint(tree)
    return tree

# Parse the argument and value from a string formatted as "(arg='count', value=Constant(value=5))])"
def parse_arg_value_list_integer(text):
    """
    Correctly parses a string with the format "(arg='...', value=List(elts=[Constant(value=...), ...], ctx=Load()))])"
    to extract the argument and a list of values.

    Parameters:
    - text (str): The input string to parse.

    Returns:
    - dict: A dictionary with keys 'arg' and 'values' containing the extracted argument and list of values.
    """
    extracted_values = {'arg': None, 'value': []}

    # Extract the argument
    arg_start = text.find("arg='") + 5
    arg_end = text.find("'", arg_start)
    extracted_values['arg'] = text[arg_start:arg_end]

    # Extract the list of values
    values_start = text.find("[") + 1
    values_end = text.find("]", values_start)
    values_text = text[values_start:values_end]

    # Process each part within the list
    values_parts = values_text.split("), ")
    flag = False
    for part in values_parts:
        if "UnaryOp" in part:
            flag = True
            continue
        elif "Constant(value=" in part:
            # Handling Constant values
            value_start = part.find("Constant(value=") + len("Constant(value=")
            value_end = part.find(")", value_start)
            if value_end == -1:
                value_text = part[value_start:]
            else:
                value_text = part[value_start:value_end]
            # Determine if the value is an integer, float, or string
            if "'" in value_text:
                # String value
                value = value_text.strip("'")
            else:
                try:
                    value = int(value_text)
                except ValueError:
                    try:
                        value = float(value_text)
                    except:
                        value = -1
            if flag:
                value = -value
                flag = False
            extracted_values['value'].append(value)
    return extracted_values

# Parse the argument and value from a string formatted as "(arg='count', value=Constant(value=5))])"
def parse_arg_value_list_strings(text):
    """
    Adjusted function to parse strings with the format 
    "(arg='...', value=List(elts=[Constant(value='...'), ...], ctx=Load()))"
    to extract the argument and a list of string values.

    Parameters:
    - text (str): The input string to parse.

    Returns:
    - dict: A dictionary with keys 'arg' and 'values' containing the extracted argument and list of string values.
    """
    extracted_values = {'arg': None, 'values': []}

    # Extract the argument
    arg_start = text.find("arg='") + 5
    arg_end = text.find("'", arg_start)
    extracted_values['arg'] = text[arg_start:arg_end]

    # Extract the list of values
    values_start = text.find("[Constant(value=") + len("[Constant(value=")
    values_end = text.find("]", values_start)
    values_text = text[values_start:values_end]

    # Clean and split the values_text to extract individual values, considering they are strings
    values_parts = values_text.split("), Constant(value=")
    for part in values_parts:
        value_start = part.find("'") + 1
        value_end = part.find("'", value_start)
        value = part[value_start:value_end]  # Extracting string value between single quotes
        extracted_values['value'].append(value)

    return extracted_values

# Extract the argument and value from a string formatted as "(arg='count', value=Constant(value=5))])"
def extract_arg_value(text):

    """
    Extracts the argument and value from a string formatted as "(arg='count', value=Constant(value=5))])".

    Parameters:
    - text (str): The input string to extract from.

    Returns:
    - dict: A dictionary with keys 'arg' and 'value' containing the extracted values.
    """

    # Initialize an empty dictionary to store the extracted values
    extracted_values = {'arg': None, 'value': None}

    # Split the input text by comma to separate the 'arg' and 'value' parts
    parts = text.split(", ")

    # Extract the argument
    arg_part = parts[0].split("=")
    if len(arg_part) == 2:
        extracted_values['arg'] = arg_part[1].strip("'")

    # Extract the value, considering nested structure for value
    if len(parts) == 4:
        parts[1] = parts[1] + ", " + parts[2]
    value_part = parts[1].split("=")
    # Floats 
    if "UnaryOp(op=USub(), operand=Constant(value=" in text:
        # Handling UnaryOp for negative numbers
        value_text = text.split("UnaryOp(op=USub(), operand=Constant(value=")[1].split(")")[0]
        try:
            value = -int(value_text)
        except ValueError:
            value = -float(value_text)
        extracted_values['value'] = value
        return extracted_values
    # Bools:
    if "Name(id='" in text:
        if "true" in text:
            extracted_values['value'] = True
        else:
            extracted_values['value'] = False
        return extracted_values
    if len(value_part) == 3:  # Assuming the format is always as provided
        extracted_values['value'] = value_part[2].rstrip("))])")
    if extracted_values['value'] is not None and extracted_values['value'].isnumeric():
        extracted_values['value'] = int(extracted_values['value'])
    if extracted_values['value'] == "True" or extracted_values['value'] == "true":
        extracted_values['value'] = True
    if extracted_values['value'] == "False" or extracted_values['value'] == "false":
        extracted_values['value'] = False
    return extracted_values

# Parse the AST tree to extract function names and arguments
def ast_parse(x):
    function_name_list = []
    function_args_list = []
    for node in ast.walk(x):
        if not isinstance(node, ast.Call):
            continue
        # print(ast.dump(node))
        # Figure out function name
        dump = ast.dump(node)
        # This checks for number of functions
        if dump.count("func=") > 1:
            overall_match = False
            break
        function_name = dump.split(", args=[]")[0].split("func=")[1]
        if function_name.startswith("Name(id='"):
            function_name = function_name.split("Name(id='")[1].split("', ctx=Load()")[0]
        else:
            function_name = function_name.split("value=Name(id='")[1].split("ctx=Load()")
            function_rest = function_name[1:]
            function_id = function_name[0].split("'")[0]
            function_attr = []
            for attr in function_rest:
                if "attr='" in attr:
                    function_attr.append(attr.split("attr='")[1].split("'")[0])
            function_name = ".".join([function_id]+function_attr)
        # Figure out argument
        arguments = dump.split("keywords=")[1].split("keyword(")
        args = []
        args_value = []
        arguments = arguments[1:]
        for arg_idx, argument in enumerate(arguments):
            # print(data['question'], answer)
            if "arg=" in argument:
                # TODO: this doesn't handle ** in arguments
                if argument.split("arg='")[1].split("', ")[1].startswith("value=Dict"):
                    # TODO: figure out Dict
                    arg_value = []
                    pass
                elif argument.split("arg='")[1].split("', ")[1].startswith("value=Name"):
                    if "Name(id='" in argument.split("arg='")[1].split("', ")[1]:
                        arg_value = [argument.split("arg='")[1].split("', ")[1].split("Name(id='")[1].split("', ctx=Load()")[0]]
                    else:
                        arg_value = []
                elif argument.split("arg='")[1].split("', ")[1].startswith("value=Constant"):
                    if "Constant(value='" in argument.split("arg='")[1].split("', ")[1] and "', ctx=" in argument:
                        arg_value = [argument.split("arg='")[1].split("', ")[1].split("Constant(value='")[1].split("', ctx=")[0]]
                    elif "Constant(value='" in argument.split("arg='")[1].split("', ")[1] and "', kind=" in argument:
                        arg_value = [argument.split("arg='")[1].split("', ")[1].split("Constant(value='")[1].split("', kind=")[0]]
                    elif "Constant(value=" in argument.split("arg='")[1].split(", ")[1] and ", kind=" in argument:
                        arg_value = [argument.split("arg=")[1].split(", ")[1].split("Constant(value=")[1].split(", kind=")[0]]
                    else:
                        arg_value = []
                # TODO: we don't check for List, Tuple etc. for now
                else:   
                    arg_value = []

                args.append(argument)
                args_value += arg_value
        function_name_list.append(function_name)
        function_args_list.append(args)
    return function_name_list, function_args_list

# Reading input file and possible answer
test_category = args.test_category
example = []
try:
    if args.file_name is not None:
        with open(file_name,"r") as f:
            for line in f:
                example.append(json.loads(line))
        gorilla_testing_data = []
        with open("eval_data_total.json","r") as f:
            for line in f:
                gorilla_testing_data.append(json.loads(line))
        new_example = []
        for i in range(len(gorilla_testing_data)):
            if gorilla_testing_data[i]["question_type"] == args.test_category:
                new_example.append(example[i])
        example = new_example
    else:
        with open(file_name,"r") as f:
            for line in f:
                example.append(json.loads(line)) 
except:
    print(f"🙊 Your {args.model}'s {test_category} evaluation category data is not found, check whether you have finished openfunctions_evaluation.py evaluation data generation.")
    exit()
    
answer = []
if test_category == "miss_param" or test_category == "relevance" or test_category == "chatable":
    pass
else:
    with open(possible_answer_file,"r") as f:
        for line in f:
            answer.append(json.loads(line))
    if "sql" in possible_answer_file:
       example = example[:100]
    else:
        assert len(example) == len(answer)

# Check if the input file is a gpt or gorilla file
if "gpt" in file_name or "glaive" in file_name or "fire" in file_name or "mistral-large-latest" in file_name:
    total = 0
    success = 0
    for k in range(len(example)):
        result_list = []
        if "glaive" in file_name:
            try:
                example[k]["text"] = json.loads(example[k]["text"].split("<functioncall>")[1].replace("\'{","{").replace("\'}","}"))
                example[k]["text"] = [{example[k]["text"]["name"]:example[k]["text"]["arguments"]}]
                if test_category == "miss_param" or test_category == "relevance" or test_category == "chatable":
                    total += 1
                    continue
            except:
                if test_category == "miss_param" or test_category == "relevance" or test_category == "chatable":
                    total += 1
                    success += 1
                    continue
        else:
            if test_category == "miss_param" or test_category == "relevance" or test_category == "chatable":
                if example[k]["result"] == []:
                    total += 1
                    success += 1
                    continue
                if type(example[k]["result"]) is str:
                    total += 1
                    success += 1
                    continue
                else:
                    total += 1
                    continue
            if type(example[k]["result"]) is str:
                total += 1
                if output_analysis:
                    with open("./gpt_failure.json","a+") as f:
                        f.write(json.dumps({"index":k,"answer":example[k]["result"]}) + "\n")
                continue
        if "glaive" in file_name:
            keyword = "text"
        else:
            keyword = "result"
        if len(example[k][keyword]) != len(answer[k].keys()):
            total += 1
            continue
        for item in example[k][keyword]:
            try:
                func_name = list(item.keys())[0]
            except Exception as e:
                continue
            possible_function_result_list = []
            for possible_func_name in answer[k].keys():
                new_possible_func_name = possible_func_name.replace(".","_")
                if func_name in new_possible_func_name:
                    try:
                        function_param_dict = json.loads(item[func_name])
                    except:
                        function_param_dict = item[func_name]    
                    arg_result_dict = []
                    for args in function_param_dict.keys():
                        if type(function_param_dict[args]) is str and len(function_param_dict[args]) > 0 and function_param_dict[args][0] == "{":
                            if "true" in function_param_dict[args]:
                                function_param_dict[args] = function_param_dict[args].replace("true","True")
                            try:
                                result_dict = eval(function_param_dict[args].replace("true","True"))
                            except:
                                total += 1
                                continue
                            answer_dict = eval(str(answer[k][possible_func_name][args]))[0]
                            arg_result_dict.append(result_dict == answer_dict)
                        elif type(function_param_dict[args]) is dict:
                            try:
                                answer_dict = eval(str(answer[k][possible_func_name][args]))[0]
                            except:
                                try:
                                    answer_dict = eval(str(answer[k][possible_func_name][args]))
                                except:
                                    continue
                            arg_result_dict.append(function_param_dict[args] == answer_dict)
                        else:
                            try:
                                if function_param_dict[args] in answer[k][possible_func_name][args]:
                                    arg_result_dict.append(True)
                                else:
                                    if type(function_param_dict[args]) is str and any([function_param_dict[args].lower() == pa.lower() for pa in answer[possible_func_name][args] if type(pa) is str]):
                                        # Check for case insensitive string match
                                        arg_result_dict.append(True)
                                    else:

                                        if type(function_param_dict[args]) == str and function_param_dict[args].isdigit():
                                            arg_result_dict.append(int(function_param_dict[args]) == answer[k][possible_func_name][args])
                            except:
                                if type(function_param_dict[args]) == str and function_param_dict[args].isdigit():
                                    arg_result_dict.append(int(function_param_dict[args]) == answer[k][possible_func_name][args] or int(function_param_dict[args]) in answer[k][possible_func_name][args])
                                else:
                                    arg_result_dict.append(False)
                else:
                    arg_result_dict = [False]
                required_parameter = sum(["" not in val for val in answer[k][possible_func_name].values()])
                optional_parameter = len(answer[k][possible_func_name].keys()) - required_parameter
                possible_function_result_list.append(all(arg_result_dict) and len(function_param_dict) >= required_parameter and len(function_param_dict) <= required_parameter + optional_parameter)
            result_list.append(any(possible_function_result_list))     
        total += 1
        success += all(result_list)
        if not all(result_list):
            if output_analysis:
                with open("./gpt_failure.json","a+") as f:
                    f.write(json.dumps({"index":k,"answer":example[k]["result"]}) + "\n")
    print(f"Testing type: {test_category}, success rate: {success/total}")
else:
    total = 0
    success = 0
    for k in range(len(example)):
        if "gorilla_openfunctions_v2" in file_name or "git" in file_name:
            func = "[" + ", ".join(example[k]["text"].replace("\n","").split("<<function>>")[1:]) + "]"
        elif "gorilla-openfunctions-v0" in str(file_name):
            func = "[" + example[k]["text"] + "]"
        elif "deepseek-7b" in file_name:
            example[k]["text"] = example[k]["text"].replace("\n","")
            try:
                pattern = r"```python(.*?)```"
                pattern1 = r"```(.*?)```"

                # Search for the pattern in the text
                match = re.search(pattern, example[k]["text"], re.DOTALL)
                match1 = re.search(pattern1, example[k]["text"], re.DOTALL)

                if match:
                    func = match.group(1).strip()
                elif match1:
                    func = match1.group(1).strip()
                else:
                    func = example[k]["text"]
            except:
                pass
        else:
            func = str(example[k]["result"]).replace("\", \"",",").replace("[\"","[").replace("\"]","]")
        if args.model == "mistral-medium" or args.model == "mistral-large" or args.model == "mistral-small" or args.model == "mistral-tiny":
            func = func.replace("\\_","_")
            if not func.startswith("["):
                func = "[" + func
            if not func.endswith("]"):
                func = func + "]"
        if "Nexus" in args.model:
            try:
                func = func.split("<human_end>\n \n")[1]
            except:
                total += 1
                continue
            if ";" in func:
                func = func.split(";")[:-1]
            if type(func) is list:
                func = [f[1:] if f[0] == " " else f for f in func]
                func = "["+",".join(func)+"]"
            elif type(func) is str:
                func = "["+func+"]"
        if "claude" in args.model:
            if " " == func[0]:
                func = func[1:]
            if not func.startswith("["):
                func = "[" + func
            if not func.endswith("]"):
                func = func + "]"
        if test_category == "miss_param" or test_category == "relevance" or test_category == "chatable":
            try:
                x = build_ast(func)
                total += 1
                continue
            except Exception as e:
                total += 1
                success += 1    
                continue
        else:
            try:
                x = build_ast(str(func))
            except Exception as e:
                total += 1
                if output_analysis:
                    with open("./gorilla_failure.json","a+") as f:
                        f.write(json.dumps({"index":k,"answer":func}) + "\n")
                continue
        potential_answer = answer[k]
        function_name_list, function_arg_list = ast_parse(x)
        result_list = []
        if len(function_name_list) != len(potential_answer.keys()):
            total += 1
            continue
        for i in range(len(function_name_list)):
            result_sub_list = []
            for func_name in potential_answer.keys():
                result_multiple_list = []
                new_ans_name = func_name.replace(".","_")
                new_func_name = function_name_list[i].replace(".","_")
                if function_name_list[i] in func_name or new_func_name in new_ans_name:
                    for item in function_arg_list[i]:
                        if "Dict" in item or "Tuple" in item:
                            continue
                        if "List" in item:
                            try:
                                arg_data = parse_arg_value_list_integer(item)
                            except Exception as e:
                                arg_data = parse_arg_value_list_strings(item)
                        else:
                            arg_data = extract_arg_value(item)
                        arg_name = arg_data['arg']
                        arg_val = arg_data['value']

                        if type(arg_val) is str and arg_val[0] == '\'':
                            arg_val = arg_val[1:-1]
                        if arg_name in potential_answer[func_name].keys():
                            try:
                                arg_val in potential_answer[func_name][arg_name]
                            except:
                                continue
                            if arg_val in potential_answer[func_name][arg_name]:
                                result_multiple_list.append(True)
                            else:
                                if type(arg_val) is str and any([arg_val.lower() == pa.lower() for pa in potential_answer[func_name][arg_name] if type(pa) is str]):
                                    # Check for case insensitive string match
                                    result_multiple_list.append(True)
                                else:
                                    try:
                                        arg_val = float(arg_val)
                                        if arg_val in potential_answer[func_name][arg_name]:
                                            result_multiple_list.append(True)
                                    except:
                                        result_multiple_list.append(False)
                        else:
                            result_multiple_list.append(False)
                    required_parameter = sum(["" not in val for val in potential_answer[func_name].values()])
                    optional_parameter = len(potential_answer[func_name].keys()) - required_parameter
                    result_sub_list.append(all(result_multiple_list) and len(function_arg_list[i]) >= required_parameter and len(function_arg_list[i]) <= required_parameter + optional_parameter)
            if result_sub_list == []:
                result_list.append(False)
            else:
                result_list.append(any(result_sub_list))
        if False in result_list or len(result_list) == 0:
            total += 1
            if output_analysis:
                with open("./gorilla_failure.json","a+") as f:
                    f.write(json.dumps({"index":k,"answer":func}) + "\n")
        else:
            total += 1
            success += 1
    print(f"Testing type: {test_category}, success rate: {success/total}")
            