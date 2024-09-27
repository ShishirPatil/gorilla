import logging
from typing import Literal, Any
import argparse
import json
import PyPDF2
import random
import os, shutil
from math import ceil
from datasets import Dataset, concatenate_datasets
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM, AutoModelForQuestionAnswering
import torch
# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("huggingface_script")

# Document type literals
DocType = Literal["api", "pdf", "json", "txt"]

# Every N chunks, save a checkpoint
N = 15

def get_args() -> argparse.Namespace:
    """
    Parses and returns the command line arguments specified by the user.
    """
    parser = argparse.ArgumentParser()

    parser.add_argument("--datapath", type=str, default="", help="The path at which the document is located")
    parser.add_argument("--output", type=str, default="./", help="The path at which to save the dataset")
    parser.add_argument("--output-format", type=str, default="hf", help="Format to convert the dataset to. Defaults to hf.")
    parser.add_argument("--output-type", type=str, default="jsonl", help="Type to export the dataset to. Defaults to jsonl.")
    parser.add_argument("--distractors", type=int, default=3, help="The number of distractor documents to include per data point / triplet")
    parser.add_argument("--p", type=float, default=1.0, help="The percentage that the oracle document is included in the context")
    parser.add_argument("--questions", type=int, default=5, help="The number of data points / triplets to generate per chunk")
    parser.add_argument("--chunk_size", type=int, default=512, help="The size of each chunk in number of tokens")
    parser.add_argument("--doctype", type=str, default="pdf", help="The type of the document", choices=["pdf", "txt", "json", "api"])
    parser.add_argument("--fast", action="store_true", help="Run the script in fast mode (no recovery implemented)")

    args = parser.parse_args()
    return args

def get_chunks(file_path: str, doctype: DocType = "pdf", chunk_size: int = 512) -> list[str]:
    """
    Takes in a `file_path` and `doctype`, retrieves the document, breaks it down into chunks of size
    `chunk_size`, and returns the chunks as a list of strings.
    """
    chunks = []

    logger.info(f"Retrieving chunks from {file_path} of type {doctype}")

    if doctype == "api":
        # Load API documentation and process it
        with open(file_path) as f:
            api_docs_json = json.load(f)
        chunks = [str(api_doc_json) for api_doc_json in api_docs_json]

    else:
        if doctype == "json":
            # Load JSON document
            with open(file_path, 'r') as f:
                data = json.load(f)
            text = data["text"]
        elif doctype == "pdf":
            # Load PDF and extract text
            text = ""
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                num_pages = len(reader.pages)
                for page_num in range(num_pages):
                    page = reader.pages[page_num]
                    text += page.extract_text()
        elif doctype == "txt":
            # Load plain text document
            with open(file_path, 'r') as file:
                text = file.read()
        else:
            raise TypeError("Document is not one of the accepted types: api, pdf, json, txt")
        
        # Split the text into chunks
        num_chunks = ceil(len(text) / chunk_size)
        logger.info(f"Splitting text into {num_chunks} chunks.")
        for i in range(0, len(text), chunk_size):
            chunks.append(text[i:i + chunk_size])
            
    return chunks

def generate_instructions_hf(chunk: str, x: int = 5, model_name: str = "t5-small") -> list[str]:
    """
    Uses a Hugging Face model to generate `x` questions based on the given text chunk, utilizing the GPU if available.
    """
    # Load the Hugging Face model and tokenizer for question generation
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

    # Move model to GPU if available
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    input_text = f"Generate questions based on the following text: {chunk}"
    inputs = tokenizer(input_text, return_tensors="pt", truncation=True, padding="longest").to(device)

    outputs = model.generate(
        inputs.input_ids, 
        max_length=64, 
        num_beams=x,  # Using beam search with `x` beams
        num_return_sequences=x  # Returning `x` sequences
    )

    questions = [tokenizer.decode(output, skip_special_tokens=True) for output in outputs]
    
    return questions

def generate_label_hf(question: str, context: str, model_name: str = "deepset/roberta-base-squad2") -> str:
    """
    Uses a Hugging Face model to generate an answer to the given question based on the context, utilizing the GPU if available.
    """
    # Load the Hugging Face model and tokenizer for question-answering
    question_answering_pipeline = pipeline("question-answering", model=model_name, device=0 if torch.cuda.is_available() else -1)
    
    result = question_answering_pipeline(question=question, context=context)
    
    return result['answer']

def add_chunk_to_dataset(
    chunks: list[str], 
    chunk: str, 
    doctype: DocType = "api", 
    x: int = 5, 
    num_distract: int = 3, 
    p: float = 0.8,
    model_name_qg: str = "t5-small",
    model_name_qa: str = "deepset/roberta-base-squad2"
) -> None:
    """
    Given a chunk, create {Q, A, D} triplets and add them to the dataset using Hugging Face models.
    """
    global ds
    i = chunks.index(chunk)
    
    # Use the Hugging Face model to generate questions
    qs = generate_instructions_hf(chunk, x, model_name=model_name_qg)
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

        # Create distractor documents
        docs = [chunk]
        indices = list(range(0, len(chunks)))
        indices.remove(i)
        for j in random.sample(indices, num_distract):
            docs.append(chunks[j])
        # Decide whether to add oracle document
        oracle = random.uniform(0, 1) < p
        if not oracle:
            docs[0] = chunks[random.sample(indices, 1)[0]]
        random.shuffle(docs)

        d = {
            "title": ["placeholder_title"] * (num_distract + 1),
            "sentences": docs
        }
        datapt["context"] = d
        datapt["oracle_context"] = chunk

        # Add the answer generated by the Hugging Face model
        datapt["cot_answer"] = generate_label_hf(q, chunk, model_name=model_name_qa)

        # Construct model instruction
        context = ""
        for doc in docs:
            context += "<DOCUMENT>" + str(doc) + "</DOCUMENT>\n"
        context += q
        datapt["instruction"] = context

        # Add to dataset
        if not ds:
            # Initialize dataset
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
    """
    Saves the current state of processing to a file for recovery.
    """
    with open(filename, 'w') as f:
        f.write(str(state))

def load_checkpoint(filename):
    """
    Loads the processing state from a checkpoint file.
    """
    with open(filename, 'r') as f:
        return int(f.read())

def main():
    global ds

    # Get command line arguments
    args = get_args()

    CHUNK_SIZE = args.chunk_size
    NUM_DISTRACT_DOCS = args.distractors

    # Split the document into chunks
    chunks = get_chunks(args.datapath, args.doctype, CHUNK_SIZE)

    ds = None

    num_chunks = len(chunks)

    if not args.fast:
        start = 0
        if os.path.exists("checkpoint.txt"):
            start = int(load_checkpoint("checkpoint.txt"))

        for i in range((start // N) * N, len(chunks)):
            chunk = chunks[i]
            save_checkpoint(i, "checkpoint.txt")

            perc = ceil(i / num_chunks * 100)
            logger.info(f"Adding chunk {i}/{num_chunks}")
            add_chunk_to_dataset(chunks, chunk, args.doctype, args.questions, NUM_DISTRACT_DOCS)

            if (i + 1) % N == 0:
                ds.save_to_disk(args.output + "-checkpoints-" + str(i))
                ds = None
    
        if ds:
            ds.save_to_disk(args.output + "-checkpoints-last")

        ds_list = []

        for filename in os.listdir(os.path.dirname(args.output)):
            if "-checkpoints-" in filename:
                for f in os.listdir(os.path.dirname(args.output) + "/" + filename):
                    if f.endswith(".arrow"):
                        ds_list.append(Dataset.from_file(os.path.dirname(args.output) + "/" + filename + "/" + f))

        ds = concatenate_datasets(ds_list)
    else:
        for i, chunk in enumerate(chunks):
            perc = ceil(i / num_chunks * 100)
            logger.info(f"Adding chunk {i}/{num_chunks}")
            add_chunk_to_dataset(chunks, chunk, args.doctype, args.questions, NUM_DISTRACT_DOCS)
    
    # Save the final dataset
    ds.save_to_disk(args.output)

    # Save as .jsonl format (dummy functionality)
    # Implement a conversion function if needed, this is just a placeholder
    logger.info("Converting dataset to the desired format...")

    if not args.fast:
        os.remove("checkpoint.txt")
        for filename in os.listdir(os.path.dirname(args.output)):
            if "-checkpoints-" in filename:
                shutil.rmtree(os.path.dirname(args.output) + "/" + filename)

if __name__ == "__main__":
    logger.info("Starting the Hugging Face processing script...")
    main()
