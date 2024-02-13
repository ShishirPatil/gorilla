'''
1. Take API documentation, for each API endpoint generate X real-world use case (instruction, api) pairs.
2. Convert each pair to a user-agent chat-style conversation, where each data-point is a conversation with
one round each for the user and the agent.
3. Fine-tune on this dataset.
'''
from datasets import load_dataset, Dataset

OPENAPI_API_KEY = "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"
API_PATH = "felixzhu1.json"

from openai import OpenAI
import json

client = OpenAI(
   api_key=OPENAPI_API_KEY,
)

with open(API_PATH) as f:
    api_docs = json.load(f)

X = 5

def encode_question(question, api):
    """Encode multiple prompt instructions into a single string."""
    
    prompts = []
        
    prompt = question + "\nWrite a python program to call API in " + str(api) + ".\n\nThe answer should follow the format: <<<domain>>> $DOMAIN, <<<api_call>>>: $API_CALL, <<<api_provider>>>: $API_PROVIDER, <<<explanation>>>: $EXPLANATION, <<<code>>>: $CODE}. Here are the requirements:\n \n2. The $DOMAIN should be the domain of the API ('N/A' if unknown). The $API_CALL should have only 1 line of code that calls api.\n3. The $API_PROVIDER should be the programming framework used.\n4. $EXPLANATION should be a step-by-step explanation.\n5. The $CODE is the python code.\n6. Do not repeat the format in your answer."
    prompts.append({"role": "system", "content": "You are a helpful API writer who can write APIs based on requirements."})
    prompts.append({"role": "user", "content": prompt})
    return prompts

def generate_instructions(api_call, x=X):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a synthetic instruction-api pair generator. Given an API endpoint in the form of a JSON object, generate %s example queries of instructions a user could ask and would be answered by invoking the API call. For example, if the given API call is the `service.users().getProfile(userId='me').execute()` call from the Gmail API, an example query could be 'How can I fetch my Gmail account's email address?'" % (x)},
            {"role": "system", "content": "The API endpoint is a JSON object with required params: user_name, api_name, api_call, api_version, api_arguments, functionality, and optional params: env_requirements, example_code, meta_data, Questions"},
            {"role": "system", "content": "For instance, if the api call contains: {'user_name': 'felixzhu555', 'api_name': 'Google Maps - Address Validation', 'api_call': 'Client.addressvalidation(addressLines, regionCode=region_code, locality=locality, enableUspsCass=boolean)', 'api_version': '4.10.0', 'api_arguments': {}, 'functionality': 'Validate an address and its components, standardize the address for mailing, and determine the best known geocode for it.', 'env_requirements': ['googlemaps'], 'example_code': 'client = googlemaps.Client(key='YOUR_API_KEY')\nresponse = client.addressvalidation('1600 Amphitheatre Pk', regionCode='US', locality='Mountain View', enableUspsCass=True)', 'meta_data': {'description': 'The googlemaps python client is an abstraction for the Google Maps API that requires python 3.5+. Each Google Maps web service request requires an API key or client ID. API keys are generated in the 'Credentials' page of the 'APIs & Services' tab of Google Cloud console. This key should be kept secret on your server.'}, 'questions': []}, an example instruction would be 'Validate the following address: University Avenue and, Oxford St, Berkeley, CA 94720.'"},
            {"role": "system", "content": "Don't mention 'API' or use any hints or the name of the API. In one-third of the queries, make sure to include a specific example, like 'Validate this address: 123 Harrison St, Oakland CA'. Include ONLY the queries in your response."},
            {"role": "user", "content": str(api_call)}
        ]
    )

    queries = response.choices[0].message.content
    
    lines = queries.split('\n')
    queries = [line[:len(line)-1].split('. "')[1] for line in lines if line.strip() != '']
    
    return queries

def generate_label(question, api):
    question = encode_question(question, api)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=question,
        n=1,
        temperature=0
    )
    response = response.choices[0].message.content
    return response

def encode_queries(queries):
    lines = queries.split('\n')
    questions = [line[:len(line)-1].split('. "')[1] for line in lines if line.strip() != '']

    print(questions)

def create_dataset(doc):
    ds_dict = {"instruction": [], "api": []}
    
    for ac in doc:
        instructions = generate_instructions(ac)
        for i in instructions:
            l = generate_label(i, ac)
            ds_dict["instruction"].append(i)
            ds_dict["api"].append(l)

    return ds_dict

DS = create_dataset(api_docs)
ds = Dataset.from_dict(DS)
ds.save_to_disk("sample_ds")


