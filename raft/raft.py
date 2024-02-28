import argparse
from openai import OpenAI
from datasets import Dataset, load_dataset
from transformers import AutoTokenizer
import json
import PyPDF2
import random

def get_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--datapath", type=str, default="")
    parser.add_argument("--output", type=str, default="./")
    parser.add_argument("--distractors", type=int, default=3)
    parser.add_argument("--questions", type=int, default=5)
    parser.add_argument("--chunk_size", type=int, default=512)
    parser.add_argument("--is_api", type=str, default="")
    parser.add_argument("--openai_key", type=str, default="")
    parser.add_argument("--tokenizer", type=str, default="bert-base-cased")

    args = parser.parse_args()
    return args

def get_chunks(file_path, tokenizer=None, is_api=False, chunk_size=512):
    chunks = []
    
    if is_api:
        with open(file_path) as f:
            api_docs_json = json.load(f)
        chunks = list(api_docs_json)
    else:
        text = ""
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            num_pages = len(reader.pages)
            for page_num in range(num_pages):
                page = reader.pages[page_num]
                text += page.extract_text()
        
        tokens = tokenizer(text)['input_ids']
        for i in range(0, len(tokens), chunk_size):
            chunk = tokens[i:min(i + chunk_size,len(tokens))]
            chunk_string = tokenizer.decode(chunk)
            chunks.append(chunk_string)

    return chunks

def generate_instructions(api_call, x=5):
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

    queries = response.choices[0].message.content.split('\n')
    queries = [strip_str(q) for q in queries]
    queries = [q for q in queries if any(c.isalpha() for c in q)]

    return queries

def generate_instructions_gen(chunk, x=5):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a synthetic question-answer pair generator. Given a chunk of context about some topic(s), generate %s example questions a user could ask and would be answered using information from the chunk. For example, if the given context was a Wikipedia paragraph about the United States, an example question could be 'How many states are in the United States?'" % (x)},
            {"role": "system", "content": "The questions should be able to be answered in a few words or less."},
            {"role": "user", "content": str(chunk)}
        ]
    )

    queries = response.choices[0].message.content.split('\n')
    queries = [strip_str(q) for q in queries]
    queries = [q for q in queries if any(c.isalpha() for c in q)]

    return queries 

def strip_str(s):
    l, r = 0, len(s)-1
    beg_found = False
    for i in range(len(s)):
        if s[i].isalpha():
            if not beg_found:
                l = i
                beg_found = True
            else:
                r = i 
    r += 2
    return s[l:min(r, len(s))]

def encode_question(question, api):
    """Encode multiple prompt instructions into a single string."""
    
    prompts = []
        
    prompt = question + "\nWrite a python program to call API in " + str(api) + ".\n\nThe answer should follow the format: <<<domain>>> $DOMAIN \n, <<<api_call>>>: $API_CALL \n, <<<api_provider>>>: $API_PROVIDER \n, <<<explanation>>>: $EXPLANATION \n, <<<code>>>: $CODE}. Here are the requirements:\n \n2. The $DOMAIN should be the domain of the API ('N/A' if unknown). The $API_CALL should have only 1 line of code that calls api.\n3. The $API_PROVIDER should be the programming framework used.\n4. $EXPLANATION should be a numbered, step-by-step explanation.\n5. The $CODE is the python code.\n6. Do not repeat the format in your answer."
    prompts.append({"role": "system", "content": "You are a helpful API writer who can write APIs based on requirements."})
    prompts.append({"role": "user", "content": prompt})
    return prompts

def encode_question_gen(question, chunk):
    """Encode multiple prompt instructions into a single string."""
    
    prompts = []
        
    prompt = question + "\nAnswer this question using the information given in the following context: " + str(chunk) + ".\n\nThe answer should be no more than five words. Include ONLY the answer in your response."
    prompts.append({"role": "system", "content": "You are a helpful question answerer who can provide an answer given a question and relevant context."})
    prompts.append({"role": "user", "content": prompt})
    return prompts

def generate_label(question, context, is_api=False):
    question = encode_question(question, context) if is_api else encode_question_gen(question, context)
    response = client.chat.completions.create(
        model="gpt-4",
        messages=question,
        n=1,
        temperature=0
    )
    response = response.choices[0].message.content
    return response

# Create {Q, A, D} triplets using chunk / API call and add to dataset
def add_chunk_to_dataset(chunks: list, chunk: str, is_api: bool = False, x: int = 5, num_distract: int = 3):
    global ds
    i = chunks.index(chunk)
    qs = generate_instructions(chunk, x) if is_api else generate_instructions_gen(chunk, x)
    for q in qs:
        datapt = {
            "id": None,
            "type": None,
            "question": None,
            "context": None,
            "answer": None,
            "cot_answer": None
        }

        datapt["id"] = f"seed_task_{0 if not ds else ds.num_rows}"
        datapt["type"] = "api call" if is_api else "general"
        datapt["question"] = q

        # add 4 distractor docs
        docs = [chunk]
        indices = list(range(0, len(chunks)))
        indices.remove(i)
        for j in random.sample(indices, num_distract):
            docs.append(chunks[j])
        random.shuffle(docs)

        d = {
            "title": [],
            "sentences": []
        }

        d["title"].append(["placeholder_title"]*(num_distract+1))
        d["sentences"].append(docs)
        datapt["context"] = d

        # add answer to q
        datapt["answer"] = chunk["api_call"] if is_api else generate_label(q, chunk)
        datapt["cot_answer"] = generate_label(q, chunk) if is_api else None

        # print(datapt)

        # add to dataset
        if not ds:
            # init ds
            datapt["id"] = [datapt["id"]]
            datapt["type"] = [datapt["type"]]
            datapt["question"] = [datapt["question"]]
            datapt["context"] = [datapt["context"]]
            datapt["answer"] = [datapt["answer"]]
            datapt["cot_answer"] = [datapt["cot_answer"]]
            ds = Dataset.from_dict(datapt)
        else:
            ds = ds.add_item(datapt)

if __name__ == "__main__":
    # run code
    args = get_args()
    
    OPENAPI_API_KEY = args.openai_key

    client = OpenAI(
        api_key=OPENAPI_API_KEY,
    )
    
    if(args.is_api == "False"):
        args.is_api = False

    CHUNK_SIZE = args.chunk_size
    NUM_DISTRACT_DOCS = args.distractors

    tokenizer = AutoTokenizer.from_pretrained(args.tokenizer)

    chunks = get_chunks(args.datapath, tokenizer, args.is_api, CHUNK_SIZE)

    ds = None

    for chunk in chunks[:3]:
        add_chunk_to_dataset(chunks, chunk, args.is_api, args.questions, NUM_DISTRACT_DOCS)
        print("chunk done")
    
    ds.save_to_disk(args.output)