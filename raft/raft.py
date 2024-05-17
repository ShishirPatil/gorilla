import mdc
from mdc import MDC
from logconf import log_setup
import logging
from typing import Literal, Any
import argparse
from openai import OpenAI
import datasets
from datasets import Dataset, load_dataset
import pyarrow as pa
from transformers import AutoTokenizer
import json
import PyPDF2
import random
import os, shutil
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai.embeddings import OpenAIEmbeddings
from client_utils import build_openai_client, build_langchain_embeddings
from math import ceil
from format import DatasetConverter, datasetFormats, outputDatasetTypes
from pathlib import Path
from dotenv import load_dotenv

log_setup()

load_dotenv()  # take environment variables from .env.

logger = logging.getLogger("raft")

DocType = Literal["api", "pdf", "json", "txt"]

def get_args() -> argparse.Namespace:
    """
    Parses and returns the arguments specified by the user's command
    """
    parser = argparse.ArgumentParser()

    parser.add_argument("--datapath", type=Path, default="", help="The path at which the document is located")
    parser.add_argument("--output", type=str, default="./", help="The path at which to save the dataset")
    parser.add_argument("--output-format", type=str, default="hf", help="Format to convert the dataset to. Defaults to hf.", choices=datasetFormats)
    parser.add_argument("--output-type", type=str, default="jsonl", help="Type to export the dataset to. Defaults to jsonl.", choices=outputDatasetTypes)
    parser.add_argument("--output-chat-system-prompt", type=str, help="The system prompt to use when the output format is chat")
    parser.add_argument("--output-completion-prompt-column", type=str, default="prompt", help="The prompt column name to use for the completion format")
    parser.add_argument("--output-completion-completion-column", type=str, default="completion", help="The completion column name to use for the completion format")
    parser.add_argument("--distractors", type=int, default=3, help="The number of distractor documents to include per data point / triplet")
    parser.add_argument("--p", type=float, default=1.0, help="The percentage that the oracle document is included in the context")
    parser.add_argument("--questions", type=int, default=5, help="The number of data points / triplets to generate per chunk")
    parser.add_argument("--chunk_size", type=int, default=512, help="The size of each chunk in number of tokens")
    parser.add_argument("--doctype", type=str, default="pdf", help="The type of the document, must be one of the accepted doctypes", choices=["pdf", "txt", "json", "api"])
    parser.add_argument("--openai_key", type=str, default=None, help="Your OpenAI key used to make queries to GPT-3.5 or GPT-4")
    parser.add_argument("--embedding_model", type=str, default="text-embedding-ada-002", help="The embedding model to use to encode documents chunks (text-embedding-ada-002, ...)")
    parser.add_argument("--completion_model", type=str, default="gpt-4", help="The model to use to generate questions and answers (gpt-3.5, gpt-4, ...)")
    parser.add_argument("--fast", action="store_true", help="Run the script in fast mode (no recovery implemented)")
    parser.add_argument("--checkpoint-size", default=15, type=int, help="The size of checkpoints. Ignored when --fast is set.)")
    parser.add_argument("--system-prompt-key", default="gpt", help="The system prompt to use to generate the dataset")

    args = parser.parse_args()
    return args


def get_chunks(
    data_path: Path, 
    doctype: DocType = "pdf", 
    chunk_size: int = 512, 
    openai_key: str | None = None,
    model: str = None
) -> list[str]:
    """
    Takes in a `data_path` and `doctype`, retrieves the document, breaks it down into chunks of size
    `chunk_size`, and returns the chunks.
    """
    chunks = []

    logger.info(f"Retrieving chunks from {data_path} of type {doctype}")

    if doctype == "api":
        with open(data_path) as f:
            api_docs_json = json.load(f)
        chunks = list(api_docs_json)
        chunks = [str(api_doc_json) for api_doc_json in api_docs_json]

        for field in ["user_name", "api_name", "api_call", "api_version", "api_arguments", "functionality"]:
            if field not in chunks[0]:
                raise TypeError(f"API documentation is not in the format specified by the Gorilla API Store: Missing field `{field}`")

    else:
        embeddings = build_langchain_embeddings(openai_api_key=openai_key, model=model)
        chunks = []
        file_paths = [data_path]
        if data_path.is_dir():
            file_paths = data_path.rglob('**/*.' + doctype)
        for file_path in file_paths:
            logger.info(f"Retrieving chunks from {file_path} using the {model} model.")
            doc_chunks = get_doc_chunks(embeddings, file_path, doctype, chunk_size)
            chunks.extend(doc_chunks)

    return chunks

def get_doc_chunks(
    embeddings: OpenAIEmbeddings,
    file_path: Path, 
    doctype: DocType = "pdf", 
    chunk_size: int = 512,
 ) -> list[str]:
    if doctype == "json":
        with open(file_path, 'r') as f:
            data = json.load(f)
        text = data["text"]
    elif doctype == "pdf":
        text = ""
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            num_pages = len(reader.pages)
            for page_num in range(num_pages):
                page = reader.pages[page_num]
                text += page.extract_text()
    elif doctype == "txt":
        with open(file_path, 'r') as file:
            data = file.read()
        text = str(data)
    else:
        raise TypeError("Document is not one of the accepted types: api, pdf, json, txt")
    
    num_chunks = ceil(len(text) / chunk_size)
    logger.info(f"Splitting text into {num_chunks} chunks.")

    text_splitter = SemanticChunker(embeddings, number_of_chunks=num_chunks)
    chunks = text_splitter.create_documents([text])
    chunks = [chunk.page_content for chunk in chunks]
    return chunks

def generate_instructions(client: OpenAI, api_call: Any, x=5, model: str = None) -> list[str]:
    """
    Generates `x` questions / use cases for `api_call`. Used when the input document is of type `api`.
    """
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a synthetic instruction-api pair generator. Given an API endpoint in the form of a JSON object, generate %s example queries of instructions a user could ask and would be answered by invoking the API call. For example, if the given API call is the `service.users().getProfile(userId='me').execute()` call from the Gmail API, an example query could be 'How can I fetch my Gmail account's email address?'" % (x)},
            {"role": "system", "content": "The API endpoint is a JSON object with required params: user_name, api_name, api_call, api_version, api_arguments, functionality, and optional params: env_requirements, example_code, meta_data, Questions"},
            {"role": "system", "content": "For instance, if the api call contains: {'user_name': 'felixzhu555', 'api_name': 'Google Maps - Address Validation', 'api_call': 'Client.addressvalidation(addressLines, regionCode=region_code, locality=locality, enableUspsCass=boolean)', 'api_version': '4.10.0', 'api_arguments': {}, 'functionality': 'Validate an address and its components, standardize the address for mailing, and determine the best known geocode for it.', 'env_requirements': ['googlemaps'], 'example_code': 'client = googlemaps.Client(key='YOUR_API_KEY')\nresponse = client.addressvalidation('1600 Amphitheatre Pk', regionCode='US', locality='Mountain View', enableUspsCass=True)', 'meta_data': {'description': 'The googlemaps python client is an abstraction for the Google Maps API that requires python 3.5+. Each Google Maps web service request requires an API key or client ID. API keys are generated in the 'Credentials' page of the 'APIs & Services' tab of Google Cloud console. This key should be kept secret on your server.'}, 'questions': []}, an example instruction would be 'Validate the following address: University Avenue and, Oxford St, Berkeley, CA 94720.'"},
            {"role": "system", "content": "Don't mention 'API' or use any hints or the name of the API. In one-third of the queries, make sure to include a specific example, like 'Validate this address: 123 Harrison St, Oakland CA'. Include ONLY the queries in your response."},
            {"role": "user", "content": str(api_call)}
        ]
    )

    content = response.choices[0].message.content
    queries = content.split('\n')
    queries = [strip_str(q) for q in queries]
    queries = [q for q in queries if any(c.isalpha() for c in q)]

    return queries

build_qa_messages = {
    "gpt": lambda chunk, x : [
            {"role": "system", "content": """You are a synthetic question-answer pair generator. Given a chunk of context about 
             some topic(s), generate %s example questions a user could ask and would be answered using information from the chunk. 
             For example, if the given context was a Wikipedia paragraph about the United States, an example question could be 
             'How many states are in the United States?'""" % (x)},
            {"role": "system", "content": "The questions should be able to be answered in a few words or less. Include only the questions in your response."},
            {"role": "user", "content": str(chunk)}
        ],
    "llama": lambda chunk, x : [
            {"role": "system", "content": 
                """You are a synthetic question generator.
                
                Instructions:
                - Given a chunk of context about some topic(s), generate %s example questions a user could ask
                - Questions should be answerable using only information from the chunk.
                - Generate one question per line
                - Generate only questions
                - Questions should be succinct

                Here are some samples:
                Context: A Wikipedia paragraph about the United States, 
                Question: How many states are in the United States?

                Context: A Wikipedia paragraph about vampire bats, 
                Question: What are the different species of vampire bats?
                """ % (x)},
            {"role": "system", "content": "The questions should be able to be answered in a few words or less. Include only the questions in your response."},
            {"role": "user", "content": str(chunk)}
        ]
}

def generate_instructions_gen(client: OpenAI, chunk: Any, x: int = 5, model: str = None, prompt_key : str = "gpt") -> list[str]:
    """
    Generates `x` questions / use cases for `chunk`. Used when the input document is of general types 
    `pdf`, `json`, or `txt`.
    """
    response = client.chat.completions.create(
        model=model,
        messages=build_qa_messages[prompt_key](chunk, x)
    )

    content = response.choices[0].message.content
    queries = content.split('\n')
    #queries = [strip_str(q) for q in queries]
    queries = [q for q in queries if any(c.isalpha() for c in q)]

    return queries 

def strip_str(s: str) -> str:
    """
    Helper function for helping format strings returned by GPT-4.
    """
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

def encode_question(question: str, api: Any) -> list[str]:
    """
    Encode multiple prompt instructions into a single string for the `api` case.
    """
    prompts = []
        
    prompt = question + "\nWrite a python program to call API in " + str(api) + ".\n\nThe answer should follow the format: <<<domain>>> $DOMAIN \n, <<<api_call>>>: $API_CALL \n, <<<api_provider>>>: $API_PROVIDER \n, <<<explanation>>>: $EXPLANATION \n, <<<code>>>: $CODE}. Here are the requirements:\n \n2. The $DOMAIN should be the domain of the API ('N/A' if unknown). The $API_CALL should have only 1 line of code that calls api.\n3. The $API_PROVIDER should be the programming framework used.\n4. $EXPLANATION should be a numbered, step-by-step explanation.\n5. The $CODE is the python code.\n6. Do not repeat the format in your answer."
    prompts.append({"role": "system", "content": "You are a helpful API writer who can write APIs based on requirements."})
    prompts.append({"role": "user", "content": prompt})
    return prompts


prompt_templates = {
    "gpt": """
        Question: {question}\nContext: {context}\n
        Answer this question using the information given in the context above. Here is things to pay attention to: 
        - First provide step-by-step reasoning on how to answer the question. 
        - In the reasoning, if you need to copy paste some sentences from the context, include them in ##begin_quote## and ##end_quote##. This would mean that things outside of ##begin_quote## and ##end_quote## are not directly copy paste from the context. 
        - End your response with final answer in the form <ANSWER>: $answer, the answer should be succinct.
        You MUST begin your final answer with the tag "<ANSWER>:".
    """,
    "llama": """
        Question: {question}
        Context: {context}

        Answer this question using the information given in the context above.
        
        Instructions:
        - Provide step-by-step reasoning on how to answer the question.
        - Explain which parts of the context are meaningful and why.
        - Copy paste the relevant sentences from the context in ##begin_quote## and ##end_quote##.
        - Provide a summary of how you reached your answer.
        - End your response with the final answer in the form <ANSWER>: $answer, the answer should be succinct.
        - You MUST begin your final answer with the tag "<ANSWER>:".

        Here are some samples:

        Example question: What movement did the arrest of Jack Weinberg in Sproul Plaza give rise to?
        Example answer: To answer the question, we need to identify the movement that was sparked by the arrest of Jack Weinberg in Sproul Plaza. 
        The context provided gives us the necessary information to determine this.
        First, we look for the part of the context that directly mentions Jack Weinberg's arrest. 
        We find it in the sentence: ##begin_quote##The arrest in Sproul Plaza of Jack Weinberg, a recent Berkeley alumnus and chair of Campus CORE, 
        prompted a series of student-led acts of formal remonstrance and civil disobedience that ultimately gave rise to the Free Speech Movement##end_quote##.
        From this sentence, we understand that the arrest of Jack Weinberg led to student-led acts which then gave rise to a specific movement. 
        The name of the movement is explicitly mentioned in the same sentence as the "Free Speech Movement."
        Therefore, based on the context provided, we can conclude that the arrest of Jack Weinberg in Sproul Plaza gave rise to the Free Speech Movement.
        <ANSWER>: Free Speech Movement
    """
    }

def encode_question_gen(question: str, chunk: Any, prompt_key : str = "gpt") -> list[str]:
    """
    Encode multiple prompt instructions into a single string for the general case (`pdf`, `json`, or `txt`).
    """
    
    prompts = []

    prompt = prompt_templates[prompt_key].format(question=question, context=str(chunk))
    prompts.append({"role": "system", "content": "You are a helpful question answerer who can provide an answer given a question and relevant context."})
    prompts.append({"role": "user", "content": prompt})
    return prompts

def generate_label(client: OpenAI, question: str, context: Any, doctype: DocType = "pdf", model: str = None, prompt_key : str = "gpt") -> str | None:
    """
    Generates the label / answer to `question` using `context` and GPT-4.
    """
    question = encode_question(question, context) if doctype == "api" else encode_question_gen(question, context, prompt_key)
    response = client.chat.completions.create(
        model=model,
        messages=question,
        n=1,
        temperature=0
    )
    response = response.choices[0].message.content
    return response

def add_chunk_to_dataset(
    client: OpenAI,
    chunks: list[str], 
    chunk: str, 
    doctype: DocType = "api", 
    x: int = 5, 
    num_distract: int = 3, 
    p: float = 0.8,
    model: str = None,
    prompt_key: str = "gpt"
) -> None:
    """
    Given a chunk, create {Q, A, D} triplets and add them to the dataset.
    """
    global ds
    i = chunks.index(chunk)
    qs = generate_instructions(client, chunk, x, model) if doctype == "api" else generate_instructions_gen(client, chunk, x, model, prompt_key)
    for q in qs:
        datapt = {
            "id": None,
            "type": None,
            "question": None,
            "context": None,
            "oracle_context": None,
            "cot_answer": None
        }

        datapt["id"] = f"seed_task_{0 if not ds else ds.num_rows}"
        datapt["type"] = "api call" if doctype == "api" else "general"
        datapt["question"] = q

        # add num_distract distractor docs
        docs = [chunk]
        indices = list(range(0, len(chunks)))
        indices.remove(i)
        for j in random.sample(indices, num_distract):
            docs.append(chunks[j])
        # decides whether to add oracle document
        oracle = random.uniform(0, 1) < p
        if not oracle:
            docs[0] = chunks[random.sample(indices, 1)[0]]
        random.shuffle(docs)

        d = {
            "title": [],
            "sentences": []
        }

        d["title"].append(["placeholder_title"]*(num_distract+1))
        d["sentences"].append(docs)
        datapt["context"] = d
        datapt["oracle_context"] = chunk

        # add answer to q
        datapt["cot_answer"] = generate_label(client, q, chunk, doctype, model=model, prompt_key=prompt_key)

        # construct model instruction 
        context = ""
        for doc in docs:
            context += "<DOCUMENT>" + str(doc) + "</DOCUMENT>\n"
        context += q
        datapt["instruction"] = context

        # add to dataset
        if not ds:
            # init ds
            datapt["id"] = [datapt["id"]]
            datapt["type"] = [datapt["type"]]
            datapt["question"] = [datapt["question"]]
            datapt["context"] = [datapt["context"]]
            datapt["oracle_context"] = [datapt["oracle_context"]]
            datapt["cot_answer"] = [datapt["cot_answer"]]
            datapt["instruction"] = [datapt["instruction"]]
            ds = Dataset.from_dict(datapt)
        else:
            ds = ds.add_item(datapt)

def save_checkpoint(state, filename):
    with open(filename, 'w') as f:
        f.write(str(state))

def load_checkpoint(filename):
    with open(filename, 'r') as f:
        return int(f.read())

def build_chunks_with_checkpoint(
        datapath: Path, 
        doctype: str,
        CHUNK_SIZE: int, 
        OPENAPI_API_KEY: str,
        embedding_model: str,
        checkpoint: bool, 
        checkpoints_dir: Path, 
        ):
    """
    Builds chunks and checkpoints them if asked
    """
    chunks_ds: Dataset = None
    chunks = None
    checkpoints_chunks_path = checkpoints_dir / "chunks"
    if checkpoint:
        logger.info(f"Using checkpoint chunks {checkpoints_chunks_path}")
        if checkpoints_chunks_path.exists():
            chunks_ds = Dataset.load_from_disk(checkpoints_chunks_path)
            chunks = chunks_ds['chunk']

    if not chunks:
        chunks = get_chunks(datapath, doctype, CHUNK_SIZE, OPENAPI_API_KEY, model=embedding_model)

    if checkpoint and not chunks_ds:
        chunks_table = pa.table({ "chunk": chunks })
        chunks_ds = Dataset(chunks_table)
        chunks_ds.save_to_disk(checkpoints_chunks_path)
    return chunks

def main():
    global ds

    # run code
    args = get_args()

    # Validate arguments
    if args.output_chat_system_prompt and args.output_format != "chat":
        raise Exception("Parameter --output-chat-system-prompt can only be used with --output-format chat")

    OPENAPI_API_KEY = args.openai_key

    client = build_openai_client(
        api_key=OPENAPI_API_KEY,
    )

    CHUNK_SIZE = args.chunk_size
    NUM_DISTRACT_DOCS = args.distractors

    output_path = Path(args.output).absolute()

    checkpoints_dir = Path(str(output_path) + "-checkpoints").absolute()
    datapath: Path = args.datapath

    chunks = build_chunks_with_checkpoint(
        datapath, args.doctype, CHUNK_SIZE, OPENAPI_API_KEY, args.embedding_model, not args.fast, checkpoints_dir)

    ds = None

    num_chunks = len(chunks)

    system_prompt_key = args.system_prompt_key
    logger.info(f"Using system prompt key {system_prompt_key}")

    N = args.checkpoint_size

    datasets.disable_progress_bars()
    if not args.fast:
        checkpoints_state_path = checkpoints_dir / "checkpoint.txt"
        logger.info(f"Using checkpoint file {checkpoints_state_path}")

        start = 0
        if checkpoints_state_path.exists():
            # Resume from last chunk not checkpointed
            start = int(load_checkpoint(checkpoints_state_path))

        for i in range(start, len(chunks)):
            chunk = chunks[i]
            checkpoint_path = checkpoints_dir / ("checkpoint-" + str(i))

            perc = ceil((i+1) / num_chunks * 100)
            with MDC(progress=f"{perc}%"):
                logger.info(f"Adding chunk {i+1}/{num_chunks}")
                add_chunk_to_dataset(client, chunks, chunk, args.doctype, args.questions, NUM_DISTRACT_DOCS, model=args.completion_model, prompt_key=system_prompt_key)

            if (i+1) % N == 0:
                ds.save_to_disk(checkpoint_path)
                if N > 1 and logger.isEnabledFor(logging.INFO):
                    logger.info(f"Saving checkpoint {checkpoint_path}")

                # Save next chunk as checkpoint
                save_checkpoint(i + 1, checkpoints_state_path)
                ds = None
    
    
        if ds:
            ds.save_to_disk(str(output_path) + "-checkpoints-last")

        ds_list = []

        for dir_path in checkpoints_dir.iterdir():
            if dir_path.is_dir() and dir_path.name.startswith("checkpoint-"):
                for f in dir_path.iterdir():
                    if f.is_file() and f.suffix == ".arrow":
                        ds_list.append(Dataset.from_file(str(f)))

        ds = datasets.concatenate_datasets(ds_list)
    else:
        for i, chunk in enumerate(chunks):
            perc = ceil((i+1) / num_chunks * 100)
            with MDC(progress=f"{perc}%"):
                logger.info(f"Adding chunk {i+1}/{num_chunks}")
                add_chunk_to_dataset(client, chunks, chunk, args.doctype, args.questions, NUM_DISTRACT_DOCS, model=args.completion_model, prompt_key=system_prompt_key)
    
    # Save as .arrow format
    datasets.enable_progress_bars()
    ds.save_to_disk(str(output_path))

    # Save as .jsonl format
    formatter = DatasetConverter()

    # Extract format specific params
    format_params = {}
    if args.output_chat_system_prompt:
        format_params['system_prompt'] = args.output_chat_system_prompt

    if args.output_format == "completion":
        format_params['prompt_column'] = args.output_completion_prompt_column
        format_params['completion_column'] = args.output_completion_completion_column

    formatter.convert(ds=ds, format=args.output_format, output_path=str(output_path), output_type=args.output_type, params=format_params)

    if not args.fast:
        shutil.rmtree(checkpoints_dir)

if __name__ == "__main__":
    with MDC(progress="0%"):
        main()