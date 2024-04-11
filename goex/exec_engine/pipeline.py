import requests
import os
from openai import OpenAI, APIError
from collections import defaultdict
from exec_engine.credentials.credentials_utils import *
from exec_engine.utils import SQL_Type, Filesystem_Type, RESTful_Type

import re

python_pattern = r"```python\n(.*?)\n```"
sql_pattern = r"```sql\n(.*?)\n```"
bash_pattern = r"```(?:bash|shell|sh)\n(.*?)\n```"

INSTRUCTION_TEXT = """
    You are an assistant that outputs executable Python code that perform what the user requests. 
    It is important that you only return one and only one code block with all the necessary imports inside ```python and nothing else.
    The code block should print the output(s) when appropriate.

    If the action can't be successfully completed, throw an exception
    
    This is what the user requests: {request}\n
    """

REVERSE_INSTRUCTION_TEXT = """
    Given an action and a Python code block that performs that action from the user,
    you are an assistant that outputs executable Python code that perform the REVERSE (can make more/new API calls if needed) of what's been done.

    It is important that the REVERSE code only revert the changes if any and nothing else, and that you only return
    one and only one code block with all the necessary imports inside ```python and nothing else.

    The code block should print the output(s) when appropriate.

    If the action can't be successfully completed, throw an exception

    This is the action: {prompt}
    This is the action code block: {forward_call}

    If no revert action exists, return a python code with a print statement explaining why so.
    """

FUNCTION_IN_CONTEXT_TEXT = """
    You are an assistant that outputs executable Python code according to a given list of python functions that perform what the user requests.
    It is important that you only return one and only one code block with all the necessary imports inside ```python and nothing else.
    The code block should print the output(s) when appropriate.

    If the action can't be successfully completed, throw an exception

    Don't change the available functions listed below except for feeding parameters.
    
    Only use the functions defined below, don't add new functions.

    Here is a list of python functions available:\n
    {functions}\n

    This is what the user requests: {request}\n
    """

REVERSE_FUNCTION_IN_CONTEXT_TEXT = """
    Given a list of available functions, an action and a Python code block that performs that action from the user,
    you are an assistant that outputs executable Python code using the available functions provided that perform the REVERSE (can make more/new API calls if needed) of what's been done.

    It is important that the REVERSE code only revert the changes if any and nothing else, and that you only return
    one and only one code block with all the necessary imports inside ```python and nothing else.

    The code block should print the output(s) when appropriate.

    Don't change the available functions listed below except for feeding parameters.
    
    Only use the functions defined below, don't add new functions.

    If the action can't be successfully completed, throw an exception

    Here is a list of python functions available:\n
    {functions}\n

    This is the action: {prompt}
    This is the action code block: {forward_call}

    If no revert action exists, return a python code with a print statement explaining why so.
    """

FUNCTION_CALLING_NATIVE_TEXT = """
    {request}
    """

REVERSE_FUNCTION_CALLING_NATIVE_TEXT = """
    Given an action and a Python code block that performs that action from the user,
    perform the REVERSE of what's been done.

    This is the action: {prompt}
    This is the action code block: {forward_call}
    """

def read_available_functions():
    FUNCTION_DIR = "./function/"
    avail_functions = {}
    functions = os.listdir(FUNCTION_DIR)
    for function in functions:
        if not function.endswith(".py"):
            continue
        with open(FUNCTION_DIR + function, "r") as file:
            avail_functions[function.replace(".py", "")] = file.read()
    return avail_functions


def convert_to_function_call(function_call_list):
    if type(function_call_list) == dict:
        function_call_list = [function_call_list]
    execution_list = []
    for function_call in function_call_list:
        for key, value in function_call.items():
            execution_list.append(
                f"{key}({','.join([f'{k}={repr(v)}' for k,v in json.loads(value).items()])})"
            )
    return execution_list
    

def generate_command(content, credentials = None, api_type=RESTful_Type, generate_mode='default', openai_model="gpt-4-turbo-preview"):
    client = OpenAI()

    # defaults to getting the key using os.environ.get("OPENAI_API_KEY")
    # if you saved the key under a different environment variable name, you can do something like:
    # client = OpenAI(
    #   api_key=os.environ.get("CUSTOM_ENV_NAME"),
    # )

    if api_type == SQL_Type:
        prompt = content
        pattern = sql_pattern
    elif api_type == Filesystem_Type:
        prompt = content
        pattern = bash_pattern
    elif api_type == RESTful_Type or True:
        if generate_mode == 'default':
            prompt = INSTRUCTION_TEXT.format(request=content)
        elif generate_mode == 'function_in_context': 
            avail_functions = read_available_functions()
            prompt_functions = ""
            for idx, function in enumerate(list(avail_functions.values())):
                prompt_functions += "<<function" + str(idx) + ">>: " + str(function) + "\n"
            prompt = FUNCTION_IN_CONTEXT_TEXT.format(functions=prompt_functions, request=content)
        elif generate_mode == 'function_calling_native':
            prompt = FUNCTION_CALLING_NATIVE_TEXT.format(request=content)
        else:
            raise Exception("Error: {} is not a supported argument for generate_mode, please select again from 'default', 'function_in_context', 'function_calling_native'"
                            .format(generate_mode))

        if credentials:
            prompt += generate_credentials_prompt_info(credentials)
            
        else:
            prompt += "Equally importantly, try to do so without requiring any API key. If and only if one is really needed, give the code block assuming those keys are provided."

        pattern = python_pattern

    if generate_mode == 'function_calling_native':
        function_calls = json.load(open('./function/function.json'))
        response = client.chat.completions.create(
            model=openai_model,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            tools=function_calls,
            tool_choice=None,
        )

        if response.choices[0].message.tool_calls == None:
            raise Exception("Unable able to retreive the relevant command to perform the action from Function Calling.\n" +
                            "Try again with a different prompt or generate_mode setting")
            
        output = [
                {func_call.function.name: func_call.function.arguments}
                for func_call in response.choices[0].message.tool_calls
            ]
        assert len(output) == 1
        output = output[0]
        python_code = open(f"./function/{list(output.keys())[0]}.py", 'r').read()
        output = convert_to_function_call(output)[0]
        output = "```python\n" + python_code + "\n" + output + "\n```"
    else:
        response = client.chat.completions.create(
            model=openai_model,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        output = response.choices[0].message.content

    #print(output) #Intentionally left here for future debugging purpose
    matches = re.search(pattern, output, re.DOTALL)
    if matches:
        code = matches.group(1)
        return code
    
def generate_reverse_command(forward_call, prompt, credentials=None, api_type=RESTful_Type, generate_mode='default', openai_model="gpt-4-turbo-preview"):
    client = OpenAI()

    if api_type == RESTful_Type:

        if generate_mode == 'default':
            reverse_prompt = REVERSE_INSTRUCTION_TEXT.format(prompt=prompt, forward_call=forward_call)
        elif generate_mode == 'function_in_context':
            avail_functions = read_available_functions()
            prompt_functions = ""
            for idx, function in enumerate(list(avail_functions.values())):
                prompt_functions += "<<function" + str(idx) + ">>: " + str(function) + "\n"
            reverse_prompt = REVERSE_FUNCTION_IN_CONTEXT_TEXT.format(prompt=prompt, forward_call=forward_call, functions=prompt_functions) 
        elif generate_mode == 'function_calling_native':
            reverse_prompt = REVERSE_FUNCTION_CALLING_NATIVE_TEXT.format(prompt=prompt, forward_call=forward_call)
        else:
            raise Exception("Error: {} is not a supported argument for generate_mode, please select again from 'default', 'function_in_context', 'function_calling_native'"
                            .format(generate_mode))

        if credentials:
            reverse_prompt += generate_credentials_prompt_info(credentials)
        else:
            reverse_prompt += "Equally importantly, try to do so without requiring any API key. If and only if one is really needed, give the code block assuming those keys are provided."
    else:
        raise Exception("generate_reverse_command not supported for execution type other than REST")

    if generate_mode == 'function_calling_native':
            function_calls = json.load(open('./function/function.json'))
            response = client.chat.completions.create(
                model=openai_model,
                messages=[
                    {
                        "role": "user",
                        "content": reverse_prompt
                    }
                ],
                tools=function_calls,
                tool_choice=None,
            )
            output = [
                    {func_call.function.name: func_call.function.arguments}
                    for func_call in response.choices[0].message.tool_calls
                ]
            assert len(output) == 1
            output = output[0]
            python_code = open(f"./function/{list(output.keys())[0]}.py", 'r').read()
            output = convert_to_function_call(output)[0]
            output = "```python\n" + python_code + "\n" + output + "\n```"
            
    else:
        response = client.chat.completions.create(
            model=openai_model,
            temperature=0.3,
            messages=[
                {
                    "role": "user",
                    "content": reverse_prompt
                }
            ]
        )
        output = response.choices[0].message.content

    #print(output) #Intentionally left here for future debugging purpose
    matches = re.search(python_pattern, output, re.DOTALL)
    if matches:
        code = matches.group(1)
        return code
    
def prompt_execute(engine, prompt, services=None, creds=None, max_attempt=3, model="gpt-4-turbo-preview"):
    ret = defaultdict(list)
    for _ in range(max_attempt):
        forward_call, backward_call = engine.gen_api_pair(prompt, api_type=RESTful_Type, credentials=creds, model=model)
        response = engine.api_executor.execute_api_call(forward_call, services)
        
        if response and response['output']:
            ret['output'].append(response['output'])
            return ret, forward_call, backward_call
        elif response and response['debug']:
            ret['debug'].append(response['debug'])

        engine._add_api_reverse_to_queue(RESTful_Type, (forward_call, backward_call))

    return ret, forward_call, None


def generate_credentials_prompt_info(credentials):
    #credential comes in a [service_name, value, cred_type] format
    token_in_path = []
    raw_key = []
    try:
        for service_name, value, cred_type in credentials:
            if cred_type == "path":
                token_in_path.append([service_name, value])
            elif cred_type == "raw":
                raw_key.append([service_name, value])
    except:
        raise Exception("Error: credentials have to be passed in as a list of [service_name, value, cred_type] pairs")

    if token_in_path != []:
        cred_paths = {}
        for service_name, value in token_in_path:
            prefix = "./credentials/" + service_name + "/"
            cred_paths[service_name] = [prefix + file_name for file_name in os.listdir(value)]

            return "The credentials (such as API keys) are stored in the following paths: {keys_list}. Open the file(s) to access them".format(keys_list=cred_paths)

    if raw_key != []:
        return "Additionally, these api keys are available for the following services {key_list}".format(
            key_list=" ,".join("{name}={cred}".format(name=name, cred=cred) for name,cred in raw_key))
    

