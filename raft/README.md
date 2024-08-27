## RAFT

RAFT is a recipe to adapting LLMs to domain-specific RAG. You can learn more in our release-blogs [here](https://gorilla.cs.berkeley.edu/blogs/9_raft.html) and [here](https://techcommunity.microsoft.com/t5/ai-ai-platform-blog/bg-p/AIPlatformBlog). RAFT takes an input document from the user and creates a dataset using the document, consisting of synthetically generated `{ question, answer, documents }` triplets. The dataset can then be used to fine-tune models for improved question-answering and retrieval. 

The input data from the user can be either a general text document (pdf, json, or txt) for general QA or an API documentation in the API Zoo JSONL format for API calling. 

## Dev environment with Codespaces

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/ShishirPatil/gorilla/tree/codespaces?devcontainer_path=.devcontainer%2Fraft%2Fdevcontainer.json)

Everything is setup automatically in the dev container, open a terminal into the `raft` folder:

Note: The `raft` virtual env will be activated in your shell when entering into the `raft` folder.

## Install Dependencies

Dependencies can be installed using the following command: 

```bash
pip install -r requirements.txt
```

Arguments:
- `--datapath` - if a file, the path at which the document is located. If a folder, the path at which to load all documents
- `--output` - the path at which to save the dataset
- `--output-format` - the format of the output dataset. Defaults to `hf` for HuggingFace. Can be one of `hf`, `completion`, `chat`, `eval`.
- `--output-type` - the type of the output dataset file. Defaults to `jsonl`. Can be one of `jsonl`, `parquet`.
- `--output-chat-system-prompt` - The system prompt to use when the output format is `chat`. Optional.
- `--output-completion-prompt-column` - The column (json field name) for the `prompt` / `instruction` when using the `completion` output format. Defaults to `prompt`.
- `--output-completion-completion-column` - The column (json field name) for the `completion` when using the `completion` output format. Defaults to `completion`.
- `--distractors` - the number of distractor documents to include per data point / triplet
- `--doctype` - the type of the document, must be one of the accepted doctypes
  - currently accepted doctypes: `pdf`, `txt`, `json`, `api`
  - documents in `json` format must have a "text" attribute containing the content from which chunks are extracted
  - documents in `api` format must follow the API json format detailed in the Gorilla [API Store](https://github.com/ShishirPatil/gorilla/blob/main/data/README.md)
- `--p` - the percentage of including the oracle documents in the context
- `--chunk_size` - the size of each chunk in number of tokens
- `--questions` - the number of data points / triplets to generate per chunk
- `--openai_key` - your OpenAI key used to make queries to GPT-3.5 or GPT-4
- `--embedding-model` - The embedding model to use to encode documents chunks. Defaults to `text-embedding-ada-002`.
- `--completion-model` - The model to use to generate questions and answers. Defaults to `gpt-4`.
- `--system-prompt-key` - The system prompt key to use to generate the dataset. Defaults to `gpt`. Can by one of `gpt`, `llama`.
- `--workers` - The number of worker threads to use to generate the dataset. Defaults to 2.
- `--auto-clean-checkpoints` - Whether to auto clean the checkpoints after the dataset is generated. Defaults to `false`.

*Note*: The `--fast` mode flag has been removed, checkpointing is now always active.

## Usage

### Usage with OpenAI API

Run the following command with your desired arguments to generate the dataset.  
```bash 
python3 raft.py \
  --datapath PATH_TO_DATA \
  --output OUTPUT_PATH \
  --output-format hf \ # or completion or chat
  --distractors 3 \
  --p 1.0 \
  --doctype pdf \
  --chunk_size 512 \
  --questions 5 \
  --openai_key YOUR_OPENAI_KEY
```

**Note**: As an alternative to passing the OpenAI key with the `--openai_key` argument, you also store the standard OpenAI environment variables in a file called `.env` like so. All standard OpenAI env variables are supported.

```
# OpenAI
OPENAI_API_KEY=<replace_me>
```

`raft.py` does the following:  
- Takes a document located at `PATH_TO_DATA`, breaks it into chunks of size `chunk_size` tokens if the data is a pdf, json, or txt, or chunks of one API endpoint if the data is an API documentation, as denoted by `doctype`.
- For each chunk, uses GPT-4 to synthetically generate `questions` question-answer pairs and adds `distractors` distractor chunks to each pair, creating {Q, A, D} triplets. Each triplet represents one datapoint in the dataset, where Q is the question/use-case, A is the answer, and D is the relevant chunk + distractor chunks. 
- Each data point / triplet also contains other attributes (e.g. metadata), such as `id`, `type`, and `cot_answer`.
- Uses the HuggingFace Dataset API to create a dataset from all triplets and saves it at `OUTPUT_PATH` in the .arrow and .jsonl formats.

### Usage with Azure OpenAI API

Create a file `.env` like so. All standard Azure OpenAI environment variables are supported.

```
# Azure OpenAI API
AZURE_OPENAI_ENDPOINT=https://<endpoint_sub_domain>.openai.azure.com/
AZURE_OPENAI_API_KEY=<replace_me>
OPENAI_API_VERSION=2023-05-15
```

**Note**: make sure your strip the path from the endpoint and keep just the domain. The full base URL will automatically be built based on the other env variables.

In addition, if you used non default Azure OpenAI deployment names, you'll need to specify them using the following CLI arguments:

```
--completion-model my-gpt-deployment-name
--embedding-model my-ada-deployment-name
```

### Configuring different endpoints for the completion and embedding models

When using a non OpenAI endpoint, it is often the case that the endpoints for the embedding and completion models
are different.

In that situation, it is possible to override default OpenAI and Azure OpenAI environment variables with `COMPLETION_` or `EMBEDDING_` prefixed environment variables. Here is an example:

```
# Llama 3 70b Instruct completion model
# Uses an OpenAI v1 compatible endpoint on Azure MaaS

COMPLETION_OPENAI_BASE_URL=https://Meta-Llama-3-70B-Instruct-<replace_me>-serverless.eastus2.inference.ai.azure.com/v1
COMPLETION_OPENAI_API_KEY=<replace_me>

# Ada 2 embedding model
# Uses an Azure OpenAI endpoint

EMBEDDING_AZURE_OPENAI_ENDPOINT=https://<replace_me>.openai.azure.com/
EMBEDDING_AZURE_OPENAI_API_KEY=<replace_me>
EMBEDDING_OPENAI_API_VERSION=<replace_me>
```

Running the `raft.py` CLI will look like:

```
cd raft
python3 raft.py \
    --datapath $PWD/sample_data/UC_Berkeley.pdf \
    --output $PWD/output \
    --distractors 3 \
    --doctype pdf \
    --chunk_size 512 \
    --questions 5 \
    --completion-model Meta-Llama-3-70B-Instruct-<replace_me> \
    --embedding-model text-embedding-ada-002
```

**Note**: The `--completion-model` and `--embedding-model` in the case of an Azure OpenAI endpoint must be set to the deployment name.

### Example Usage

This details the command and process used to generate the example dataset found in `./sample_ds4`. The document is a pdf of the Wikipedia page on the United States of America. 
```bash 
python3 raft.py --datapath sample_data/United_States_PDF.pdf --output ./sample_ds4 --distractors 4 --doctype pdf --chunk_size 512 --questions 5 --openai_key OPENAI_KEY
```
### Usage with Completely locally using hugging-face models

This details the command and process used to generate the example dataset found in `./sample_ds4`. The document is a pdf of the Wikipedia page on the United States of America. 
To run the script completely locally use 
```
python3 raft_local.py --datapath sample_data/UC_Berkeley_short.pdf --output ./sample_ds4 --chunk_size 512 --questions 5 --doctype pdf --fast
```

#### 1. Chunk generation
RAFT takes pdf and divides text into chunks of size 512 tokens. A sample chunk:  
 ```python
 "[CLS] United States of America Flag Coat of arms Motto : \" In God We Trust \" [ 1 ] Other traditional mottos : [ 2 ] \" E pluribus unum \" ( Latin ) \" Out of many, one \" \" Annuit cœptis \" ( Latin ) \" Providence favors our undertakings \" \" Novus ordo seclorum \" ( Latin ) \" New order of the ages \" Anthem : \" The Star - Spangled Banner \" [ 3 ] United States The United States of America ( USA or U. S. A. ), commonly know n as the United States ( US or U. S. ) or America, is a country primarily located in North America, between Canada and Mexico. It is a liberal democracy and republic of 50 federated states, a federal capital district ( Washington, D. C. ), and 326 Indian reservations that overlap with state boundaries. Outside the union of states, it asserts sovereignty over five major unincorporated island territories and various uninhabited islands. [ i ] The country has the world\'s third - largest land area, [ c ] largest maritime exclusive economic zone, and the third - largest population ( over 334 million ). [ j ] The federal government uses a presidential system with three separate branches : legislative, executive, and judicial. American territory was first settled by Paleo - Indians who migrated across the Bering land bridge over 12, 000 years ago. Colonization by the British began in 1607. Thirteen colonies eventually rebelled against the British Crown over taxation and political representation, declaring independence on July 4, 1776. Their victory in the American Revolutionary War ( 1775 – 83 ) resulted in a confederation of states before the U. S. Constitution and Bill of Rights were ratified. The young nation continued to acquire neighbor ing territories and spanned North America by the late 1840s. Longstanding disagreements over slavery led to the secession of the southern Confederate States of America, which were defeated by the remaining Union in the American Civil War ( 1861 – 65 ). Slavery was abolished, but discriminatory laws persisted in the South. By 1900, rapid industrialization established the United States as a great power and the world\'s largest economy. Following the Japanese attack on Pearl Harbor in December 1941, the United States joined the Allies of World War II. After their victory, it competed against the Soviet Union for dominance in nuclear and conventional"
  ```

#### 2. Question and answer generation
RAFT then uses GPT-4 to generate 5 questions per chunk as well as the label (answer) for each question. Proceeding with the previous example chunk:  

**Questions:**  

```python
['What is the official motto of the United States of America?',
  'How many states are there in the United States of America?',
  'Which territories does the United States claim sovereignty over, outside the union of states?',
  'When did the thirteen colonies declare independence from the British Crown?',
  'What caused the secession of the southern Confederate States of America?']
 ```

 **Answers:**
```python
['"In God We Trust"',
 '50 federated states',
 'Five major unincorporated island territories.',
 'July 4, 1776',
 'Disagreements over slavery']
 ```
#### 3. Append distractor documents
For each question-answer pair, append 4 randomly selected chunks as distractor documents to form the {Q, A, D} triplet. Proceeding with the current example, a {Q, A, D} triplet, or one datapoint, would look like: 

```python
{
  'id': 'seed_task_0', 
  'type': 'general', 
  'question': 'What is the official motto of the United States of America?', 
  'context': {
    'sentences': [
      ["the Gulf of Mexico are prone to hurricanes, ... and enforces the Act. [ 189 ] As of 2022, the U. S",
    "energy from fossil fuel and the largest ... there are 19, 969 airports in the U. S., of which 5, 193 are designated",
    'weaponry, ideology, and international i... and is a permanent member of the UN Security Council. The first documentary evidence of the phrase " United States',
    '[CLS] United States of America Flag Coat of arms ... dominance in nuclear and conventional',
    '##om ic soft pow er. [ 405 ] [ 406 ] Nearly all present ... rights in the United States are advanced by global standards.']
    ],
    'title': [
      ['placeholder_title',
      'placeholder_title',
      'placeholder_title',
      'placeholder_title',
      'placeholder_title']
    ]
  },
  'answer': '"In God We Trust"',
  'cot_answer': None
}

```

#### 4. Generate and save dataset
RAFT repeats steps 2 and 3 for each chunk and saves the dataset to the path specified by the `--output` argument.


#### 5. Convert the dataset to the format expected for fine tuning

If you specified the `--output-format completion` or `--output-format chat` argument for the `raft.py` script, you can skip this part.

Otherwise, you need to convert the dataset to the format expected for fine-tuning a `completion` model in Azure with the following command:

```
python3 format.py --input output/data-00000-of-00001.arrow --output output.completion.jsonl --output-format completion
```

**Note**: the `format.py` script also has its own help

```
python3 format.py --help

usage: format.py [-h] --input INPUT [--input-type {arrow,jsonl}] --output OUTPUT --output-format {hf,completion,chat,eval} [--output-type {parquet,jsonl}] [--output-chat-system-prompt OUTPUT_CHAT_SYSTEM_PROMPT] [--output-completion-prompt-column OUTPUT_COMPLETION_PROMPT_COLUMN] [--output-completion-completion-column OUTPUT_COMPLETION_COMPLETION_COLUMN] [--output-completion-stop OUTPUT_COMPLETION_STOP]

options:
  -h, --help            show this help message and exit
  --input INPUT         Input HuggingFace dataset file (default: None)
  --input-type {arrow,jsonl}
                        Format of the input dataset. Defaults to arrow. (default: arrow)
  --output OUTPUT       Output file (default: None)
  --output-format {hf,completion,chat,eval}
                        Format to convert the dataset to (default: None)
  --output-type {parquet,jsonl}
                        Type to export the dataset to. Defaults to jsonl. (default: jsonl)
  --output-chat-system-prompt OUTPUT_CHAT_SYSTEM_PROMPT
                        The system prompt to use when the output format is chat (default: None)
  --output-completion-prompt-column OUTPUT_COMPLETION_PROMPT_COLUMN
                        The prompt column name to use for the completion format (default: prompt)
  --output-completion-completion-column OUTPUT_COMPLETION_COMPLETION_COLUMN
                        The completion column name to use for the completion format (default: completion)
  --output-completion-stop OUTPUT_COMPLETION_STOP
                        The stop keyword to use for the completion format (default: <STOP>)
```

**Note**: If fine tuning a chat model, then you need to use `--output-format chat` and optionally add the `--output-chat-system-prompt` parameter to configure the system prompt included in the dataset.

#### 6. Finetune your own model on Microsoft AI Studio
Once the dataset is prepared, follow the instructions in [azure-ai-studio-ft/howto.md](azure-ai-studio-ft/howto.md) to finetune and deploy your own RAFT model. Make sure to use `prompt` as input and `completion` as output when fine tuning a `completion` model and the `messages` column as input when fine tuning a `chat` model.

#### 7. Evaluate RAFT model
After deploying your model in AI Studio, use command to evaluate the RAFT model. Make sure to fill in `base_url`, `api_key` and `model_name` in the `eval.py`, these can be found in the AI Studio. 
```bash 
python3 eval.py --question-file YOUR_EVAL_FILE.jsonl --answer-file YOUR_ANSWER_FILE
```

The `YOUR_EVAL_FILE.jsonl` is in the format where
```python
{
  'instruction': '<DOCUMENT> document1 </DOCUMENT>\n<DOCUMENT> document2 </DOCUMENT> ...\n{question}",
  'gold_answer': '{answer}'
}
```
