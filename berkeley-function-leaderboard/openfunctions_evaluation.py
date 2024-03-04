import os
import re
import json
from tqdm import tqdm
import requests
import argparse
from dataclasses import asdict
from anthropic import Anthropic
from time import sleep
import subprocess


def get_args():
    parser = argparse.ArgumentParser()
    # Refer to model_choice for supported models.
    parser.add_argument("--model", type=str, default="gorilla-openfunctions-v2")
    # Refer to test_categories for supported categories.
    parser.add_argument("--test_category", type=str, default="all")

    # Parameters for the model that you want to test.
    parser.add_argument("--temperature", type=float, default=0.3)
    parser.add_argument("--top_p", type=float, default=1)
    parser.add_argument("--max_tokens", type=int, default=1200)
    parser.add_argument("--num-gpus", default=1, type=int)
    parser.add_argument("--timeout", default=60, type=int)

    args = parser.parse_args()
    return args


def build_client(model_name):
    # Fill in the API key for the model you want to test.
    if "gpt" in model_name:
        from openai import OpenAI
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    elif "claude" in model_name:
        from anthropic import Anthropic
        client = Anthropic(
            api_key= os.environ.get("ANTHROPIC_API_KEY"))
    elif "mistral-medium" in model_name or "mistral-tiny" in model_name or "mistral-small" in model_name or "mistral-large-latest" in model_name:
        from mistralai.client import MistralClient
        client = MistralClient(api_key= os.environ.get("MISTRAL_API_KEY"))
    elif "Nexus" in model_name:
        return None
    elif "gorilla-openfunctions-v2" in model_name:
        import openai
        openai.api_key = "EMPTY"
        openai.api_base = "http://luigi.millennium.berkeley.edu:8000/v1"
        return None
    elif "firework" in model_name:
        from openai import OpenAI
        client = OpenAI(api_key=os.environ.get("FIRE_WORKS_API_KEY"),base_url = "https://api.fireworks.ai/inference/v1")
    else:
        return None
    return client


test_categories = {
    "executable_generic": "gorilla_openfunctions_v1_test_executable_simple.json",
    "executable_parallel_function": "gorilla_openfunctions_v1_test_executable_parallel_function.json",
    "executable_multiple_function": "gorilla_openfunctions_v1_test_executable_multiple_function.json",
    "executable_parallel_multiple_function": "gorilla_openfunctions_v1_test_executable_parallel_multiple_function.json",
    "generic": "gorilla_openfunctions_v1_test_simple.json",
    "no_function_call": "gorilla_openfunctions_v1_test_no_function_call.json",
    "parallel_function": "gorilla_openfunctions_v1_test_parallel_function.json",
    "multiple_function": "gorilla_openfunctions_v1_test_multiple_function.json",
    "parallel_multiple_function": "gorilla_openfunctions_v1_test_parallel_multiple_function.json",
    "java": "gorilla_openfunctions_v1_test_java.json",
    "javascript": "gorilla_openfunctions_v1_test_javascript.json",
    "rest": "gorilla_openfunctions_v1_test_rest.json",
    "sql": "gorilla_openfunctions_v1_test_sql.json",
    "chatable": "gorilla_openfunctions_v1_test_chatable.json",
    "fix": "gorilla_openfunctions_v1_test_fix.json",
}

model_choice = {
    "gorilla-openfunctions-v0": "http://luigi.millennium.berkeley.edu:8000/v1",
    "gorilla-openfunctions-v1": "http://luigi.millennium.berkeley.edu:8000/v1",
    "gorilla-openfunctions-v2": "FILL_UP_HOSTING_HERE",
    "gpt-3.5-turbo-0613": "gpt-3.5-turbo-0613",
    "gpt-3.5-turbo-1106": "gpt-3.5-turbo-1106",
    "gpt-3.5-turbo-0125": "gpt-3.5-turbo-0125",
    "gpt-4-0613": "gpt-4-0613",
    "gpt-4-1106-preview": "gpt-4-1106-preview",
    "gpt-4-0125-preview": "gpt-4-0125-preview",
    "mistral-medium": "mistral-medium",
    "mistral-large": "mistral-large",
    "mistral-tiny": "mistral-tiny",
    "mistrl-small": "mistral-small",
    "fireworks-ai": "https://api.fireworks.ai/inference/v1",
    "Nexusflow-Raven-v2": "http://38.142.9.20:10240",
    "claude-2.1": "claude-2.1",
    "claude-instant-1.2": "claude-instant-1.2",
    "deepseek-7b": "deepseek-ai/deepseek-coder-7b-instruct-v1.5",
    "glaiveai": "glaiveai/glaive-function-calling-v1",
    "llama-v2-7b": "meta-llama/Llama-2-7b",
    "llama-v2-13b": "meta-llama/Llama-2-13b",
    "llama-v2-70b": "meta-llama/Llama-2-70b",
    "dolphin-2.2.1-mistral-7b": "cognitivecomputations/dolphin-2.2.1-mistral-7b",
}

model_id_dict = {
    "deepseek-7b": "deepseek-coder",
    "glaiveai": "vicuna_1.1",
    "llama-v2-7b": "llama-2",
    "llama-v2-13b": "llama-2",
    "llama-v2-70b": "llama-2",
    "dolphin-2.2.1-mistral-7b": "dolphin-2.2.1-mistral-7b",
    "gorilla-openfunctions-v0": "gorilla",
}

SYSTEM_PROMPT_FOR_CHAT_MODEL = """"
    You are an expert in composing functions. You are given a question and a set of possible functions. 
    Based on the question, you will need to make one or more function/tool calls to achieve the purpose. 
    If none of the function can be used, point it out. If the given question lacks the parameters required by the function,
    also point it out. You should only return the function call in tools call sections.
    """
USER_PROMPT_FOR_CHAT_MODEL = "Questions:{user_prompt}\nHere is a list of functions in JSON format that you can invoke:\n{functions}. Should you decide to return the function call(s), NO other text MUST be included."


def call_to_model(
    client, model, user_prompt, function, max_tokens, temperature, top_p, timeout
):
    """
    Perform A single request to selected model based on the parameters.
    """
    if "gpt" in model or "firework" in model:
        # Build OAI tool calls.
        oai_tool = []
        for item in function:
            if "." in item["name"]:
                item["name"] = re.sub(
                    r"\.", "_", item["name"]
                )  # OAI does not support "." in the function name so we replace it with "_". ^[a-zA-Z0-9_-]{1,64}$ is the regex for the name.
            item["parameters"]["type"] = "object"  # If typing is missing, we assume it is an object since OAI requires a type.
            if "properties" not in item["parameters"]:
                item["parameters"]["properties"] = item["parameters"].copy()
                item["parameters"]["type"] = "object"
                for key in list(item["parameters"].keys()).copy():
                    if key != "properties" and key != "type" and key != "required":
                        del item["parameters"][key]
                for key in list(item["parameters"]["properties"].keys()).copy():
                    if key == "required" or key == "type":
                        del item["parameters"]["properties"][key]
            item["parameters"]["properties"] = cast_multi_param_type(
                item["parameters"]["properties"]
            )
            oai_tool.append({"type": "function", "function": item})
        message = [
            {
                "role": "user",
                "content": "Questions:"
                + user_prompt
                + "\n Return Nothing if no tool or function calls are involved.",
            }
        ]
        if len(oai_tool) > 0:
            response = client.chat.completions.create(
                messages=message,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                timeout=timeout,
                tools=oai_tool,
            )
        else:
            response = client.chat.completions.create(
                messages=message,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                timeout=timeout,
            )
        try:
            result = [
                {func_call.function.name: func_call.function.arguments}
                for func_call in response.choices[0].message.tool_calls
            ]
        except:
            result = response.choices[0].message.content
    elif "gemini" in model:
        tools = []
        for item in function:
            if "." in item["name"]:
                item["name"] = re.sub(
                    r"\.", "_", item["name"]
                )  # OAI does not support "." in the function name so we replace it with "_". ^[a-zA-Z0-9_-]{1,64}$ is the regex for the name.
            item["parameters"]["type"] = "object"  # If typing is missing, we assume it is an object since OAI requires a type.
            if "properties" not in item["parameters"]:
                item["parameters"]["properties"] = item["parameters"].copy()
                item["parameters"]["type"] = "object"
                for key in list(item["parameters"].keys()).copy():
                    if key != "properties" and key != "type" and key != "required":
                        del item["parameters"][key]
                for key in list(item["parameters"]["properties"].keys()).copy():
                    if key == "required" or key == "type":
                        del item["parameters"]["properties"][key]
            item["parameters"]["properties"] = cast_multi_param_type(
                item["parameters"]["properties"]
            )
            # Remove fields that are not supported by Gemini today.
            if "api_call" in item:
                del item["api_call"]
            if "optional" in item["parameters"]:
                del item["parameters"]["optional"]
            for params in item["parameters"]["properties"].values():
                if "default" in params:
                    del params["default"]
                if "optional" in params:
                    del params["optional"]
                if "maximum" in params:
                    del params["maximum"]
            tools.append(item)
        query = "Questions:" + user_prompt + "\n Return Nothing if no tool or function calls are involved."
        result = query_gemini(query, tools)
    elif "claude" in model:
        message = f"""{SYSTEM_PROMPT_FOR_CHAT_MODEL}\n\nHuman: {USER_PROMPT_FOR_CHAT_MODEL.format(user_prompt=user_prompt,functions=str(function))} Put it in the format of [func1(params_name=params_value, params_name2=params_value2...), func2(params)]\n\nAssistant:"""
        response = client.completions.create(
            model=model,
            prompt=message,
            max_tokens_to_sample=max_tokens,
            temperature=temperature,
            top_p=top_p,
        )
        result = response.completion
    elif "mistral-large-latest" in model:
        from mistralai.models.chat_completion import ChatMessage
        oai_tool = []
        for item in function:
            if "." in item["name"]:
                item["name"] = re.sub(
                    r"\.", "_", item["name"]
                )  # OAI does not support "." in the function name so we replace it with "_". ^[a-zA-Z0-9_-]{1,64}$ is the regex for the name.
            item["parameters"]["type"] = "object"  # If typing is missing, we assume it is an object since OAI requires a type.
            if "properties" not in item["parameters"]:
                item["parameters"]["properties"] = item["parameters"].copy()
                item["parameters"]["type"] = "object"
                for key in list(item["parameters"].keys()).copy():
                    if key != "properties" and key != "type" and key != "required":
                        del item["parameters"][key]
                for key in list(item["parameters"]["properties"].keys()).copy():
                    if key == "required" or key == "type":
                        del item["parameters"]["properties"][key]
            item["parameters"]["properties"] = cast_multi_param_type(
                item["parameters"]["properties"]
            )
            oai_tool.append({"type": "function", "function": item})
        message = [
            ChatMessage(role="user", content=user_prompt),
        ]
        chat_response = client.chat(
            model=model,
            messages=message,
            tools = oai_tool,
            temperature=temperature,
            top_p=top_p,
        )   
        try:
            result = [
                {func_call.function.name: func_call.function.arguments}
                for func_call in chat_response.choices[0].message.tool_calls
            ]
        except:
            result = chat_response.choices[0].message.content
    elif "mistral-medium" in model or "mistral-tiny" in model or "mistral-small" in model:
        from mistralai.models.chat_completion import ChatMessage
        message = [
            ChatMessage(role="system", content=SYSTEM_PROMPT_FOR_CHAT_MODEL),
            ChatMessage(
                role="user",
                content=USER_PROMPT_FOR_CHAT_MODEL.format(
                    user_prompt=user_prompt, functions=str(function)
                )
                + "Put it in the format of [func1(params_name=params_value, params_name2=params_value2...), func2(params)]. Don't include any special characters in function_name.",
            ),
        ]
        try:
            chat_response = client.chat(
                model=model,
                messages=message,
                temperature=temperature,
                top_p=top_p,
            )
        except:
            chat_response = client.chat(
                model=model,
                messages=message,
                temperature=temperature,
                top_p=top_p,
            )
        result = chat_response.choices[0].message.content
    elif "gorilla-openfunctions-v2" in model:
        import openai
        completion = openai.ChatCompletion.create(
            model="gorilla-openfunctions-v2",
            temperature=args.temperature,
            messages=[{"role": "user", "content": user_prompt}],
            functions=function,
        )
        print(completion.choices[0].message.content)
        result = completion.choices[0].message.content

    elif "Nexus" in model:
        raven_prompt = format_raven_function(user_prompt, function)
        result = query_raven(raven_prompt, max_tokens, temperature, top_p)
    return result

def cast_multi_param_type(properties):
    """
    OpenAI rejects parameters type other than JSON serializable type.
    Since our evaluation contains Python specific types, we need some casting
    """
    for key, value in properties.items():
        if "type" not in value:
            properties[key]["type"] = "string"
        else:
            value["type"] = value["type"].lower()
            if value["type"] not in [
                "object",
                "string",
                "number",
                "boolean",
                "array",
                "integer",
            ]:
                properties[key]["type"] = "string"
            elif value["type"] == "array" and "items" not in properties[key].keys():
                properties[key]["items"] = {"type": "object"}
            elif value["type"] == "array" and "type" not in properties[key]["items"].keys():
                properties[key]["items"]["type"] = "object"
            elif value["type"] == "array" and properties[key]["items"]["type"] not in [
                "object",
                "string",
                "number",
                "boolean",
                "array",
                "integer"
            ]:
                properties[key]["items"]["type"] = "string"
    return properties

def construct_format_tool_for_claude_prompt(name, description, parameters):
    param = construct_format_parameters_prompt(parameters["properties"])
    constructed_prompt = (
        "<tool_description>\n"
        f"<tool_name>{name}</tool_name>\n"
        "<description>\n"
        f"{description}\n"
        "</description>\n"
        "<parameters>\n"
        f"{param}\n"
        "</parameters>\n"
        "</tool_description>"
    )
    return constructed_prompt

def construct_format_parameters_prompt(parameters):
    constructed_prompt = "\n".join(f"<parameter>\n<name>{parameter}</name>\n<type>{parameters[parameter]['type']}</type>\n<description>{parameters[parameter]['description']}</description>\n</parameter>" for parameter in parameters.keys())

    return constructed_prompt

def format_raven_function(user_prompt, functions):
    """
    Nexus-Raven requires a specific format for the function description.
    This function formats the function description in the required format.
    """
    raven_prompt = """"""
    for function in functions:
        # Extracting details from the JSON
        func_name = function["name"]  # Extracting the function name
        func_desc = function["description"]
        if "properties" not in function["parameters"]:
            function["parameters"]["properties"] = function["parameters"].copy()
            function["parameters"]["type"] = "object"
            for key in list(function["parameters"].keys()).copy():
                if key != "properties" and key != "type" and key != "required":
                    del function["parameters"][key]
            for key in list(function["parameters"]["properties"].keys()).copy():
                if key == "required" or key == "type":
                    del function["parameters"]["properties"][key]
        params = function["parameters"]["properties"]

        raven_prompt += "Function: " + "\n"
        raven_prompt += f"def {func_name}(" + "\n"
        raven_prompt += '"""\n'
        raven_prompt += func_desc + "\n\n"
        raven_prompt += "Args:" + "\n"
        for param in params:
            if "type" not in params[param].keys():
                param_type = "object"
            else:
                param_type = params[param]["type"]
            if "description" not in params[param].keys():
                param_desc = ""
            else:
                param_desc = params[param]["description"]
            raven_prompt += f"\t{param}({param_type}): {param_desc}" + "\n"
        raven_prompt += "\n"
    raven_prompt += "User Query:" + user_prompt + "<human_end>"
    return raven_prompt


def query_raven(prompt, max_tokens, temperature, top_p):
    """
    Query Nexus-Raven.
    """

    API_URL = "http://38.142.9.20:10240"
    headers = {"Content-Type": "application/json"}
    response = requests.post(
        API_URL,
        headers=headers,
        json={
            "inputs": prompt,
            "parameters": {
                "temperature": temperature,
                "stop": ["<bot_end>"],
                "do_sample": False,
                "max_new_tokens": max_tokens,
            },
        },
    )
    call = response.json()[0]["generated_text"].replace("Call:", "").strip()
    return call


def query_gemini(user_query, functions):
    """
    Query Gemini Pro model.
    """

    token = subprocess.run(
        'gcloud auth print-access-token',
        check=False,
        shell=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    json_data = {
        "contents": {
            "role": "user",
            "parts": {
                "text": user_query,
            },
        },
        "generation_config": {
            "max_output_tokens": 1024,
            "temperature": 0.0,
        },
        "tools": {
            'function_declarations': functions
        }
    }

    API_URL = "https://us-central1-aiplatform.googleapis.com/v1beta1/projects/cloud-llm-preview1/locations/us-central1/publishers/google/models/gemini-pro:generateContent"
    headers = {"Authorization": "Bearer " + token, "Content-Type": "application/json"}
    response = requests.post(
        API_URL,
        headers=headers,
        data = json.dumps(json_data),
    )
    result = json.loads(response.content)
    print("HTTP content: ", result, "\n")
    if 'error' in result:
      return result["error"]["message"]
    contents = result['candidates'][0]['content']['parts'][0]

    if "functionCall" in contents:
        if "name" in contents["functionCall"] and "args" in contents["functionCall"]:
            return [
                {contents["functionCall"]["name"] : json.dumps(contents["functionCall"]["args"])}
            ]
        else:
            return "Parsing error: " + json.dumps(contents["functionCall"])
    else:
        return contents["text"]


if __name__ == "__main__":
    args = get_args()
    model = args.model
    client = build_client(args.model)
    if all([model_name not in args.model for model_name in ["gemini", "firework","gpt","claude","mistral-medium","Nexus","openfunctions","mistral-medium","mistral-tiny","mistral-small","gorilla-openfunctions-v2","mistral-large-latest"]]):
        if model in model_id_dict:
            model_id = model_id_dict[model]
            if not os.path.exists("./result/" + model):
                os.makedirs("./result/" + model)
            answer_file = "./result/" + model + "/result.json"
            if not os.path.exists("./model" + model):
                os.makedirs("./model" + model)
            model_path = "./model/" + model
            os.system(f"python openfunctions_evaluation_vllm.py --model-path {model_path} --model-id {model_id} --question-file eval_data_total.json --answer-file {answer_file} --num-gpus {args.num_gpus}")
    else:
        if args.test_category == "all":
            files_to_open = list(test_categories.values())
        else:
            files_to_open = [test_categories[args.test_category]]
        for file_to_open in files_to_open:
            print("Generating: " + file_to_open)
            test_cases = []
            with open("./data/" + file_to_open) as f:
                for line in f:
                    test_cases.append(json.loads(line))

            num_existing_result = 0  # if the result file already exists, skip the test cases that have been tested.
            if os.path.exists(
                "./result/" + args.model + "/" + file_to_open.replace(".json", "_result.json")
            ):
                with open(
                    "./result/"
                    + args.model
                    + "/"
                    + file_to_open.replace(".json", "_result.json")
                ) as f:
                    for line in f:
                        num_existing_result += 1

            for index, test_case in enumerate(tqdm(test_cases)):
                if index < num_existing_result:
                    continue

                user_question = (
                    test_case["question"]
                    if type(test_case["question"]) is str
                    else test_case["question"][0]
                )
                function = (
                    [test_case["function"]]
                    if type(test_case["function"]) is dict
                    else test_case["function"]
                )
                ground_truth = test_case["human_eval_answer"]
                result = call_to_model(
                    client,
                    model,
                    user_question,
                    function,
                    args.max_tokens,
                    args.temperature,
                    args.top_p,
                    args.timeout,
                )
                # Sleep 1 sec to avoid being throttled.
                sleep(1)
                if not os.path.exists("./result/" + args.model):
                    os.makedirs("./result/" + args.model)
                with open(
                    "./result/"
                    + args.model
                    + "/"
                    + file_to_open.replace(".json", "_result.json"),
                    "a",
                ) as f:
                    json.dump(
                        {
                            "question": user_question,
                            "function": function,
                            "ground_truth": ground_truth,
                            "result": result,
                        },
                        f,
                    )
                    f.write("\n")
