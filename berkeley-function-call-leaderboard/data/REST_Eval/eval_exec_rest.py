import json
import requests
import time

eval_GT_file = "./data/REST_Eval/rest-eval-response_v5.jsonl" # Ground truth file for v5

with open(eval_GT_file) as f:
    evals_GT = f.readlines()

def is_exec_valid(func_call, idx):
    if "https://geocode.maps.co" in func_call:
        time.sleep(2)
    if "requests_get" in func_call:
        func_call = func_call.replace("requests_get", "requests.get")
    try:
        response = eval(func_call)
    except Exception as e:
        return False
    
    if response.status_code == 200:
        try:
            eval_GT_json = json.loads(evals_GT[idx])
            if isinstance(eval_GT_json, dict) and isinstance(response.json(), dict) and set(eval_GT_json.keys()) == set(response.json().keys()):
                return True
            elif isinstance(eval_GT_json, list):
                if len(eval_GT_json) != len(response.json()):
                    return False
                else:
                    for i in range(len(eval_GT_json)):
                        if set(eval_GT_json[i].keys()) != set(response.json()[i].keys()):
                            return False
                    return True
            else:
                return False
        except:
            return False
    else:
        return False
