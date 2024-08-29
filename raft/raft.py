from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from mdc import MDC
from tqdm import tqdm
from logconf import log_setup
import logging
from typing import Literal, Any, get_args
import argparse
from openai import OpenAI, BadRequestError
import datasets
from datasets import Dataset, concatenate_datasets
import pyarrow as pa
from transformers import AutoTokenizer
import json
import PyPDF2
import random
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai.embeddings import OpenAIEmbeddings
from client_utils import build_openai_client, build_langchain_embeddings, UsageStats, ChatCompleter
from math import ceil
from format import DatasetConverter, datasetFormats, outputDatasetTypes
from pathlib import Path
from dotenv import load_dotenv
from checkpointing import Checkpointing, checkpointed
import uuid
import shutil
from threading import Thread, Event

log_setup()

load_dotenv()  # take environment variables from .env.

logger = logging.getLogger("raft")

DocType = Literal["api", "pdf", "json", "txt"]
docTypes = list(get_args(DocType))

SystemPromptKey = Literal["gpt", "llama"]
systemPromptKeys = list(get_args(SystemPromptKey))

def get_args() -> argparse.Namespace:
    """
    Parses and returns the arguments specified by the user's command
    """
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("--datapath", type=Path, default="", help="If a file, the path at which the document is located. If a folder, the path at which to load all documents")
    parser.add_argument("--output", type=str, default="./", help="The path at which to save the dataset")
    parser.add_argument("--output-format", type=str, default="hf", help="The format of the output dataset.", choices=datasetFormats)
    parser.add_argument("--output-type", type=str, default="jsonl", help="Type to export the dataset to. Defaults to jsonl.", choices=outputDatasetTypes)
    parser.add_argument("--output-chat-system-prompt", type=str, help="The system prompt to use when the output format is chat")
    parser.add_argument("--output-completion-prompt-column", type=str, default="prompt", help="The prompt column name to use for the completion format")
    parser.add_argument("--output-completion-completion-column", type=str, default="completion", help="The completion column name to use for the completion format")
    parser.add_argument("--distractors", type=int, default=3, help="The number of distractor documents to include per data point / triplet")
    parser.add_argument("--p", type=float, default=1.0, help="The percentage that the oracle document is included in the context")
    parser.add_argument("--questions", type=int, default=5, help="The number of data points / triplets to generate per chunk")
    parser.add_argument("--chunk_size", type=int, default=512, help="The size of each chunk in number of tokens")
    parser.add_argument("--doctype", type=str, default="pdf", help="The type of the document, must be one of the accepted doctypes", choices=docTypes)
    parser.add_argument("--openai_key", type=str, default=None, help="Your OpenAI key used to make queries to GPT-3.5 or GPT-4")
    parser.add_argument("--embedding_model", type=str, default="text-embedding-ada-002", help="The embedding model to use to encode documents chunks (text-embedding-ada-002, ...)")
    parser.add_argument("--completion_model", type=str, default="gpt-4", help="The model to use to generate questions and answers (gpt-3.5, gpt-4, ...)")
    parser.add_argument("--system-prompt-key", default="gpt", help="The system prompt to use to generate the dataset", choices=systemPromptKeys)
    parser.add_argument("--workers", type=int, default=2, help="The number of worker threads to use to generate the dataset")
    parser.add_argument("--auto-clean-checkpoints", type=bool, default=False, help="Whether to auto clean the checkpoints after the dataset is generated")
    parser.add_argument("--qa-threshold", type=int, default=None, help="The number of Q/A samples to generate after which to stop the generation process. Defaults to None, which means generating Q/A samples for all documents")

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

    logger.info(f"Retrieving chunks from {data_path} of type {doctype} using the {model} model.")

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
            file_paths = list(data_path.rglob('**/*.' + doctype))

        futures = []
        with tqdm(total=len(file_paths), desc="Chunking", unit="file") as pbar:
            with ThreadPoolExecutor(max_workers=2) as executor:
                for file_path in file_paths:
                    futures.append(executor.submit(get_doc_chunks, embeddings, file_path, doctype, chunk_size))
                for future in as_completed(futures):
                    doc_chunks = future.result()
                    chunks.extend(doc_chunks)
                    pbar.set_postfix({'chunks': len(chunks)})
                    pbar.update(1)

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
    logger.debug(f"Splitting text into {num_chunks} chunks.")

    text_splitter = SemanticChunker(embeddings, number_of_chunks=num_chunks)
    chunks = text_splitter.create_documents([text])
    chunks = [chunk.page_content for chunk in chunks]
    return chunks

def generate_chunk_instructions(chat_completer: ChatCompleter, chunk: Any, x=5, model: str = None) -> list[str]:
    """
    Generates `x` questions / use cases for `api_call`. Used when the input document is of type `api`.
    """
    response = chat_completer(
        model=model,
        messages=[
            {"role": "system", "content": "You are a synthetic instruction-api pair generator. Given an API endpoint in the form of a JSON object, generate %s example queries of instructions a user could ask and would be answered by invoking the API call. For example, if the given API call is the `service.users().getProfile(userId='me').execute()` call from the Gmail API, an example query could be 'How can I fetch my Gmail account's email address?'" % (x)},
            {"role": "system", "content": "The API endpoint is a JSON object with required params: user_name, api_name, api_call, api_version, api_arguments, functionality, and optional params: env_requirements, example_code, meta_data, Questions"},
            {"role": "system", "content": "For instance, if the api call contains: {'user_name': 'felixzhu555', 'api_name': 'Google Maps - Address Validation', 'api_call': 'Client.addressvalidation(addressLines, regionCode=region_code, locality=locality, enableUspsCass=boolean)', 'api_version': '4.10.0', 'api_arguments': {}, 'functionality': 'Validate an address and its components, standardize the address for mailing, and determine the best known geocode for it.', 'env_requirements': ['googlemaps'], 'example_code': 'client = googlemaps.Client(key='YOUR_API_KEY')\nresponse = client.addressvalidation('1600 Amphitheatre Pk', regionCode='US', locality='Mountain View', enableUspsCass=True)', 'meta_data': {'description': 'The googlemaps python client is an abstraction for the Google Maps API that requires python 3.5+. Each Google Maps web service request requires an API key or client ID. API keys are generated in the 'Credentials' page of the 'APIs & Services' tab of Google Cloud console. This key should be kept secret on your server.'}, 'questions': []}, an example instruction would be 'Validate the following address: University Avenue and, Oxford St, Berkeley, CA 94720.'"},
            {"role": "system", "content": "Don't mention 'API' or use any hints or the name of the API. In one-third of the queries, make sure to include a specific example, like 'Validate this address: 123 Harrison St, Oakland CA'. Include ONLY the queries in your response."},
            {"role": "user", "content": str(chunk)}
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

def generate_instructions_gen(chat_completer: ChatCompleter, chunk: Any, x: int = 5, model: str = None, prompt_key : str = "gpt") -> list[str]:
    """
    Generates `x` questions / use cases for `chunk`. Used when the input document is of general types 
    `pdf`, `json`, or `txt`.
    """
    try:
        response = chat_completer(
            model=model,
            messages=build_qa_messages[prompt_key](chunk, x),
            max_tokens=min(25 * x, 512), # 25 tokens per question
        )
    except BadRequestError as e:
        if e.code == "content_filter":
            logger.warning(f"Got content filter error, skipping chunk: {e.message}")
            return []
        raise e

    content = response.choices[0].message.content
    queries = content.split('\n') if content else []
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

def generate_label(chat_completer: ChatCompleter, question: str, context: Any, doctype: DocType = "pdf", model: str = None, prompt_key : str = "gpt") -> str | None:
    """
    Generates the label / answer to `question` using `context` and GPT-4.
    """
    question = encode_question(question, context) if doctype == "api" else encode_question_gen(question, context, prompt_key)
    response = chat_completer(
        model=model,
        messages=question,
        n=1,
        temperature=0,
        max_tokens=512,
    )
    response = response.choices[0].message.content
    return response

def generate_question_cot_answer(
        chat_completer: ChatCompleter,
        chunks: list[str], 
        chunk: str, 
        chunk_id, 
        question,
        doctype: DocType = "api", 
        num_distract: int = 3, 
        p: float = 0.8,
        model: str = None,
        prompt_key: str = "gpt",
        ):
    datapt = {
            "id": None,
            "type": None,
            "question": None,
            "context": None,
            "oracle_context": None,
            "cot_answer": None
        }

    datapt["id"] = str(uuid.uuid4())
    datapt["type"] = "api call" if doctype == "api" else "general"
    datapt["question"] = question

    # add num_distract distractor docs
    docs = [chunk]
    indices = list(range(0, len(chunks)))
    indices.remove(chunk_id)
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
    datapt["cot_answer"] = generate_label(chat_completer, question, chunk, doctype, model=model, prompt_key=prompt_key)

    # construct model instruction 
    context = ""
    for doc in docs:
        context += "<DOCUMENT>" + str(doc) + "</DOCUMENT>\n"
    context += question
    datapt["instruction"] = context
    return datapt

def build_or_load_chunks(
        datapath: Path, 
        doctype: str,
        CHUNK_SIZE: int, 
        OPENAPI_API_KEY: str,
        embedding_model: str,
        checkpoints_dir: Path, 
        ):
    """
    Builds chunks and checkpoints them if asked
    """
    chunks_ds: Dataset = None
    chunks = None
    checkpoints_chunks_path = checkpoints_dir / "chunks"
    logger.info(f"Using checkpoint chunks {checkpoints_chunks_path}")
    if checkpoints_chunks_path.exists():
        chunks_ds = Dataset.load_from_disk(checkpoints_chunks_path)
        chunks = chunks_ds['chunk']

    if not chunks:
        chunks = get_chunks(datapath, doctype, CHUNK_SIZE, OPENAPI_API_KEY, model=embedding_model)

    if not chunks_ds:
        chunks_table = pa.table({ "chunk": chunks })
        chunks_ds = Dataset(chunks_table)
        chunks_ds.save_to_disk(checkpoints_chunks_path)
    return chunks

def main():

    main_start = time.time()

    # run code
    args = get_args()

    # Validate arguments
    if args.output_chat_system_prompt and args.output_format != "chat":
        raise Exception("Parameter --output-chat-system-prompt can only be used with --output-format chat")

    OPENAPI_API_KEY = args.openai_key

    client = build_openai_client(
        api_key=OPENAPI_API_KEY,
    )
    chat_completer = ChatCompleter(client)

    CHUNK_SIZE = args.chunk_size
    NUM_DISTRACT_DOCS = args.distractors

    output_path = Path(args.output).absolute()

    checkpoints_dir = Path(str(output_path) + "-checkpoints").absolute()
    auto_clean_checkpoints = args.auto_clean_checkpoints
    if auto_clean_checkpoints:
        logger.info(f"Checkpoints will be automatically deleted after dataset generation. Remove --auto-clean-checkpoints to deactivate.")

    datapath: Path = args.datapath

    datasets.disable_progress_bars()

    # Chunks
    chunks = build_or_load_chunks(datapath, args.doctype, CHUNK_SIZE, OPENAPI_API_KEY, args.embedding_model, checkpoints_dir)

    cot_answers_ds = None

    num_chunks = len(chunks)
    num_questions = args.questions
    max_workers = args.workers
    doctype = args.doctype
    completion_model = args.completion_model

    system_prompt_key = args.system_prompt_key

    logger.info(f"Using system prompt key {system_prompt_key}")

    logger.info(f"Using {max_workers} worker threads")

    cot_answers_ds = stage_generate(chat_completer, checkpoints_dir, chunks, num_questions, max_workers, doctype, completion_model, system_prompt_key, num_distract=NUM_DISTRACT_DOCS, p=args.p, qa_threshold=args.qa_threshold)

    # Save as .arrow format
    datasets.enable_progress_bars()
    cot_answers_ds.save_to_disk(str(output_path))

    # Save as .jsonl format
    formatter = DatasetConverter()

    # Extract format specific params
    format_params = {}
    if args.output_chat_system_prompt:
        format_params['system_prompt'] = args.output_chat_system_prompt

    if args.output_format == "completion":
        format_params['prompt_column'] = args.output_completion_prompt_column
        format_params['completion_column'] = args.output_completion_completion_column

    formatter.convert(ds=cot_answers_ds, format=args.output_format, output_path=str(output_path), output_type=args.output_type, params=format_params)

    # Warning, this deletes all intermediary checkpoint files
    if auto_clean_checkpoints:
        shutil.rmtree(checkpoints_dir)

    logger.info(f"Generated {len(cot_answers_ds)} question/answer/CoT/documents samples")
    logger.info(f"Dataset saved to {output_path}")
    logger.info(f"Done in {time.time() - main_start:.2f}s")

class StoppingException(Exception):
    """
    Raised by worker threads when the process is stopping early
    """
    pass

def stage_generate(chat_completer: ChatCompleter, checkpoints_dir, chunks, num_questions, max_workers, doctype, completion_model, system_prompt_key, num_distract, p, qa_threshold):
    """
    Given a chunk, create {Q, A, D} triplets and add them to the dataset.
    """

    questions_checkpointing = Checkpointing(checkpoints_dir / "questions")
    answers_checkpointing = Checkpointing(checkpoints_dir / "answers")
    num_chunks = len(chunks)

    # Tracking when the process is stopping, so we can stop the generation process early
    # Initial value is False
    is_stopping = Event()

    @checkpointed(questions_checkpointing)
    def generate_chunk_instructions_ds(chunk: str, chunk_id: int, doctype: str, *args, **kwargs):
        """
        Generates a dataset of instructions for a given chunk.
        """
        questions = generate_chunk_instructions(chunk=chunk, *args, **kwargs) if doctype == "api" else generate_instructions_gen(chunk=chunk, *args, **kwargs)
        chunk_question_pairs = [{"chunk": chunk, "chunk_id": chunk_id, "question": question} for question in questions]
        questions_ds = Dataset.from_list(chunk_question_pairs)
        return questions_ds

    @checkpointed(answers_checkpointing)
    def generate_question_cot_answers(questions_ds, chunk_id: int, chunk: str, *args, **kwargs):
        def process_example(chunk, question):
            try:
                cot_answer = generate_question_cot_answer(chunk=chunk, chunk_id=chunk_id, chunks=chunks, question=question, *args, **kwargs)
            except BadRequestError as e:
                if e.code == "content_filter":
                    logger.warning(f"Got content filter error, skipping question '{question}': {e.message}")
                    return None
                raise e

            return cot_answer

        results = [process_example(chunk, question) for chunk, question in zip(questions_ds['chunk'], questions_ds['question'])] if len(questions_ds) > 0 else []
        results = [r for r in results if r is not None]
        table = pa.Table.from_pylist(results)
        ds = Dataset(table)
        return ds

    def process_chunk(i):
        if is_stopping.is_set():
            raise StoppingException()
        chunk = chunks[i]
        questions_ds = generate_chunk_instructions_ds(chunk=chunk, chunk_id=i, chat_completer=chat_completer, x=num_questions, model=completion_model, doctype=doctype, prompt_key=system_prompt_key)
        answers_ds = generate_question_cot_answers(questions_ds=questions_ds, chunk=chunk, chunk_id=i, chat_completer=chat_completer, model=completion_model, doctype=doctype, prompt_key=system_prompt_key, num_distract=num_distract, p=p)
        return answers_ds

    futures = []
    answers_ds_list = []
    usage_stats = UsageStats()

    # we use the checkpointing to keep track of the chunks that have already been processed
    # the answers are generated after the questions so the process might have been stopped in between a batch of answers and matching questions
    # so we need to use the answers checkpointing to keep track of which chunks we need to process
    # if the questions for a given chunk have already been checkpointed, they will just be loaded from the checkpoint
    # we set the tqdm's initial position to avoid having cached data skew the stats
    missing_chunks = answers_checkpointing.missing_checkpoints(num_chunks)

    gen_questions_count = 0
    if answers_checkpointing.has_checkpoints():
        ds = answers_checkpointing.collect_checkpoints()
        gen_questions_count = len(ds)

    done_chunks = num_chunks - len(missing_chunks)
    if done_chunks > 0 or gen_questions_count > 0:
        logger.info(f"Resuming generation from chunk {done_chunks}/{num_chunks} and {gen_questions_count} questions")

    # If we have a QA threshold, it makes more sense to keep track of the number of questions generated
    # Otherwise, track chunks
    track_questions = qa_threshold is not None

    if qa_threshold:
        logger.info(f"Will stop early as soon as the QA threshold is met: {qa_threshold}")

    if track_questions:
        tqdm_args = {"total": qa_threshold, "unit": "qa", "initial": gen_questions_count}
    else:
        tqdm_args = {"total": num_chunks, "unit": "chunk", "initial": done_chunks}

    tps = 0
    with tqdm(desc="Generating", **tqdm_args) as pbar:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for i in missing_chunks:
                futures.append(executor.submit(process_chunk, i))
            for future in as_completed(futures):
                if qa_threshold and gen_questions_count >= qa_threshold:
                    logger.info(f"Met threshold {gen_questions_count} >= {qa_threshold} questions, stopping generation")
                    is_stopping.set()
                    break
                answers_ds = future.result()
                answers_ds_list.append(answers_ds)
                increment = min(len(answers_ds), qa_threshold - gen_questions_count) if track_questions else 1
                gen_questions_count += len(answers_ds)
                done_chunks += 1
                stats = chat_completer.get_stats_and_reset()
                if stats:
                    tps = stats.total_tokens / stats.duration
                    usage_stats += stats
                postfix = {'last tok/s': tps, 'avg tok/s': usage_stats.total_tokens / usage_stats.duration if usage_stats.duration > 0 else 0}
                if track_questions:
                    postfix['chunks'] = done_chunks
                else:
                    postfix['qa'] = gen_questions_count
                pbar.set_postfix(postfix)
                pbar.update(increment)

    ds = answers_checkpointing.collect_checkpoints()
    ds = ds.select(range(qa_threshold)) if qa_threshold else ds
    logger.info(f"Consumed {usage_stats.prompt_tokens} prompt tokens, {usage_stats.completion_tokens} completion tokens, {usage_stats.total_tokens} total tokens")

    return ds

if __name__ == "__main__":
    with MDC(progress="0%"):
        main()
