"""External services sometimes require user credentials for authentication. Users can add credentials to Gorilla and specify their preferred technique to pass their credentials."""

import os
import json
import os
import shutil
from pathlib import Path

CREDS_FOLDER_PATH = os.path.dirname(os.path.realpath(__file__))
CREDS_SUPPORTED_PATH = os.path.join(os.path.dirname(Path(os.path.realpath(__file__))), "supported.txt")
SECRET_STORE_PATH = os.path.join(CREDS_FOLDER_PATH, "secret_store.json")

'''
check if the Gorilla supports the provided credential
'''
def cred_is_supported(cred):
    creds_list = []
    with open(CREDS_SUPPORTED_PATH, 'r') as f:
        for line in f:
            creds_list.append(line.strip())
    if cred not in creds_list:
        return False
    return True


"""
Insert the service and its corresponding api key.
Example: service = "gmail", key = "SOME_API_KEY"
"""
def insert_creds(service, key, target = CREDS_FOLDER_PATH, cred_type="raw"):
    #create secret store if it doesn't exist
    secret_store_path = os.path.join(target, "secret_store.json")
    secrets = {}
    try:
        with open(secret_store_path, "r") as secret_store:
            secrets = json.load(secret_store)
    except Exception as e:
        "target folder doesn't contain secret store, creating..."

    with open(secret_store_path, "w") as secret_store:
        secrets[service.lower()] = [key, cred_type]
        json.dump(secrets, secret_store)

def remove_creds(services, target = CREDS_FOLDER_PATH):
    secret_store_path = os.path.join(target, "secret_store.json")
    secrets = {}
    try:
        with open(secret_store_path, "r") as secret_store:
            secrets = json.load(secret_store)
    except Exception as e:
        print("No previous authorization.")
        return

    if(services[0]=='ALL'):
        services = list(secrets.keys())
    
    for service in services:
        if(service.lower() in secrets):
            try:
                del secrets[service.lower()]
                cred_path = os.path.join(target, service.lower())
                if os.path.exists(cred_path):
                    shutil.rmtree(cred_path)
                print(f"Succesfully removed {service}.")
            except Exception as e:
                print(f"Could not remove credentials for {service}.")
        else:
            print(f"Authorization for {service} was not found.")
    if(not secrets):
        os.remove(secret_store_path)
    else:
        with open(secret_store_path, "w") as secret_store:
            json.dump(secrets, secret_store)

def list_creds(target = CREDS_FOLDER_PATH):
    secret_store_path = os.path.join(target, "secret_store.json")
    if not os.path.exists(secret_store_path ):
        "target folder doesn't contain secret store, aborting..."

    with open(secret_store_path, "r") as secret_store:
        try:
            secrets = json.load(secret_store)
            return secrets
        except Exception as e:
            print(e)
            return {}

def creds_from_prompt(prompt, target_folder, technique = "lut", llm_code_output = None):
    creds_set = set(list_creds(target_folder))
    creds_set = list_creds(target_folder)
    formatted_prompt = prompt.lower()

    found = []
    if technique == "lut":
        for service in creds_set:
            if service in formatted_prompt:
                if not isinstance(creds_set[service], list) or len(creds_set[service]) != 2:
                    print("Error: credential for {service} in the secret store is not in the correct format".format(service=service))
                else:
                    cred, cred_type = creds_set[service]
                    found.append([service, cred, cred_type])
        return found

    elif technique == "openai":
        found = []
        if llm_code_output:
            generated_list = openai_generate_credentials_list("generate a list of credentials or keys I need to execute the following code {c}".format(c=llm_code_output))
        else:
            generated_list = openai_generate_credentials_list("generate a list of credentials or keys I need to execute code for the following prompt {p}".format(p=prompt))
        
        found = [key for key in generated_list if key in creds_set]
        return found

    else:
        print("technique has not been implemented yet...")
        return
    
def get_cred_paths(creds, target = CREDS_FOLDER_PATH):
    secret_store_path = os.path.join(target, "secret_store.json")
    if not os.path.exists(secret_store_path ):
        "target folder doesn't contain secret store, aborting..."

    with open(secret_store_path, "r") as secret_store:
        try:
            secrets = json.load(secret_store)
            found, missing = {}, []
            for c in creds:
                if c in secrets:
                    found[c] = secrets[c][0]
                else:
                    missing.append(c)
            return found, missing
        except Exception as e:
            print(e)
            return {}, []

def openai_generate_credentials_list(prompt):
    from openai import OpenAI
    client = OpenAI()

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.choices[0].message.content

def list_supported_services():
    with open(os.path.join(CREDS_FOLDER_PATH, "supported.txt")) as f:
         services = f.readlines()
    for i, s in enumerate(services):
        services[i] = s.replace("\n", "")

    return services
