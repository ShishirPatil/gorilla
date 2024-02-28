### RAFT

RAFT takes an input document from the user and creates a dataset using the document, consisting of synthetically generated `{ question, answer, documents }` triplets. The dataset can then be used to fine-tune models for improved question-answering and retrieval. 

The input data from the user can be either a pdf document for general QA or an API documentation in the API Zoo JSON format for API calling. 

### Install Dependencies

Dependencies can be installed using the following command: 

```bash
pip install -r requirements.txt
```

### Usage

Run the following command with your desired arguments.  
```bash 
python3 raft.py --datapath PATH_TO_DATA --output OUTPUT_PATH --distractors 3 --questions 5 --chunk_size 512 --is_api False
```  
`raft.py` does the following:  
- Takes a pdf/API doc located at `PATH_TO_DATA`, breaks it into chunks of size `chunk_size` tokens if the data is a pdf, or chunks of one API endpoint if the data is an API documentation, as denoted by `is_api`.
- For each chunk, uses GPT-4 to synthetically generate `questions` question-answer pairs and adds `distractors` distractor chunks to each pair, creating {Q, A, D} triplets. Each triplet represents one datapoint in the dataset, where Q is the question/use-case, A is the answer, and D is the relevant chunk + distractor chunks. 
- Uses the HuggingFace Dataset API to create a dataset from all triplets and saves it at `OUTPUT_PATH`.