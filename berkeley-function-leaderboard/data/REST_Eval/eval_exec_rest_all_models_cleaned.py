import json
import requests
import time
from urllib.parse import urlparse, urlunparse
import datetime 
import argparse
import os


MODEL_USED = "gorilla"

model_qa_file_name = f"rest-eval-set-qa-v5-{MODEL_USED}.json"
model_qa_file = f'gorilla-responses/{model_qa_file_name}' # Path to the generated model QA file
eval_response_file = "./eval_responses/" + model_qa_file_name.replace(".json", "_eval_response.json")
eval_GT_file = "./data/REST_Eval/rest-eval-response-eval-json2024-02-24-23-00-53_v5.jsonl" # Ground truth file for v5
eval_statistics_file = f"eval_responses/{model_qa_file_name.replace('.json', '_eval_statistics.json')}"
if not os.path.exists(eval_response_file):
    os.makedirs(os.path.dirname(eval_response_file), exist_ok=True)
with open(eval_response_file, 'w') as f:
    f.write("")
with open(eval_statistics_file, 'w') as f:
    f.write("")
# load rest-eval-set.json
# with open(model_qa_file) as f:
#     qa_datas = f.readlines()
# qa_datas = qa_datas[890:960]

# cleaning
# for idx, qa in enumerate(qa_datas):
#     temp = json.loads(qa)
#     temp["answer"] = temp["text"].split("<<function>>")[1]
#     qa_datas[idx] = json.dumps(temp)
    



# print("Number of data", len(qa_datas))
with open(eval_GT_file) as f:
    evals_GT = f.readlines()

# def get_base_url(url):
#     # Parse the given URL
#     parsed_url = urlparse(url)
    
#     # Reconstruct the URL with the scheme, netloc, and the first two path components
#     # Assuming the API key and the base currency are the first two path components after the host
#     path_parts = parsed_url.path.split('/')  # Split the path into components
#     base_path =  '/'.join(path_parts[:3])  # Join the first three parts ('', 'v6', '{YOUR-API-KEY}')
#     base_url = urlunparse((parsed_url.scheme, parsed_url.netloc, base_path, '', '', ''))
    
#     return base_url



# def eval_rest(data):
#     if "https://geocode.maps.co" in data["answer"]:
#         time.sleep(1)
#     response = eval(data["answer"])
#     return response
    
# success_count = 0
# error_index = []


# Fanjia look here!!!
with open(eval_GT_file) as f:
    evals_GT = f.readlines()
    
def is_exec_valid(func_call, idx):
    if "https://geocode.maps.co" in func_call:
        time.sleep(1)
    if "requests_get" in func_call:
        func_call = func_call.replace("requests_get", "requests.get")
    try:
        response = eval(func_call)
    except Exception as e:
        return False
    
    if response.status_code == 200:
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
    else:
        return False
###### End of Fanjia looks here






# for idx, data in enumerate(qa_datas):
#     print("Processing data", idx)
#     data = json.loads(data)
#     if idx >= 23 and idx <= 28: # Fanjia look here!!!
#         data["answer"] = data["answer"].replace('819adf6855mshb0468a09d6401edp142d6ejsn7fc25f6af618', 'c10ad0c47fmshb412d9404a836e3p10f9fajsnf6e6a86710d9')
#         print(data["answer"])
#         time.sleep(1)
#     response = eval_rest(data)
    
#     if response.status_code == 200:
#         print("Eval Success")
#         print(json.loads(evals_GT[idx]))
#         # print(json.loads(evals_GT[idx]).keys())
#         print(type(json.loads(evals_GT[idx])))
#         eval_GT_json = json.loads(evals_GT[idx])
#         if isinstance(eval_GT_json, dict) and isinstance(response.json(), dict) and set(eval_GT_json.keys()) == set(response.json().keys()):
#             print(f"NICEEEEEEEEEE {idx}")
#             success_count += 1
#         elif isinstance(eval_GT_json, list):
#             if len(json.loads(evals_GT[idx])) != len(response.json()):
#                 print(f"2. Key consistency ERROR in {idx}")
#                 error_index.append(idx)
#             else:
#                 for i in range(len(json.loads(evals_GT[idx]))):
#                     if set(json.loads(evals_GT[idx])[i].keys()) != set(response.json()[i].keys()):
#                         print(f"2. Key consistency ERROR in {idx}")
#                         print(data)
#                         error_index.append(idx)
#                         break
#                 success_count += 1
#         else:
#             print(f"2. Key consistency ERROR in {idx}")
#             print(data)
#             error_index.append(idx)
#     else:
#         print(f"1. Eval ERROR in {idx}")
#         print(data)
    
#     # store the response json for the model locally
#     with open(eval_response_file, 'a') as f:
#         try:
#             f.write(json.dumps(response.json()) + '\n')
#         except Exception as e:
#             print(f"Error writing response to file: {e}")
#             print(f"Response: {response}")
#             error_index.append(idx)
#             f.write(json.dumps({}) + '\n')
# with open(eval_statistics_file, 'w') as f:
#     f.write(json.dumps({"success_count": success_count, "total_count": len(qa_datas), "proportion_success": success_count/len(qa_datas), "error_index": error_index}) + '\n')
    
# print("Success count", success_count)
# print("Proportion of success", success_count/len(qa_datas))
