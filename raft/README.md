## RAFT

RAFT is a recipe to adapting LLMs to domain-specific RAG. You can learn more in our release-blogs [here](https://gorilla.cs.berkeley.edu/blogs/9_raft.html) and [here](https://techcommunity.microsoft.com/t5/ai-ai-platform-blog/bg-p/AIPlatformBlog). RAFT takes an input document from the user and creates a dataset using the document, consisting of synthetically generated `{ question, answer, documents }` triplets. The dataset can then be used to fine-tune models for improved question-answering and retrieval. 

The input data from the user can be either a general text document (pdf, json, or txt) for general QA or an API documentation in the API Zoo JSONL format for API calling. 

## Install Dependencies

Dependencies can be installed using the following command: 

```bash
pip install -r requirements.txt
```
Arguments:
- `--datapath` - the path at which the document is located
- `--output` - the path at which to save the dataset
- `--distractors` - the number of distractor documents to include per data point / triplet
- `--doctype` - the type of the document, must be one of the accepted doctypes
  - currently accepted doctypes: `pdf`, `txt`, `json`, `api`
  - documents in `json` format must have a "text" attribute containing the content from which chunks are extracted
  - documents in `api` format must follow the API json format detailed in the Gorilla [API Store](https://github.com/ShishirPatil/gorilla/blob/main/data/README.md)
- `--p` - the percentage of including the oracle documents in the context
- `--chunk_size` - the size of each chunk in number of tokens
- `--questions` - the number of data points / triplets to generate per chunk
- `--openai_key` - your OpenAI key used to make queries to GPT-3.5 or GPT-4



## Usage

Run the following command with your desired arguments to generate the dataset.  
```bash 
python3 raft.py --datapath PATH_TO_DATA --output OUTPUT_PATH --distractors 3 --doctype pdf --chunk_size 512 --questions 5 --openai_key YOUR_OPENAI_KEY
```
`raft.py` does the following:  
- Takes a document located at `PATH_TO_DATA`, breaks it into chunks of size `chunk_size` tokens if the data is a pdf, json, or txt, or chunks of one API endpoint if the data is an API documentation, as denoted by `doctype`.
- For each chunk, uses GPT-4 to synthetically generate `questions` question-answer pairs and adds `distractors` distractor chunks to each pair, creating {Q, A, D} triplets. Each triplet represents one datapoint in the dataset, where Q is the question/use-case, A is the answer, and D is the relevant chunk + distractor chunks. 
- Each data point / triplet also contains other attributes (e.g. metadata), such as `id`, `type`, and `cot_answer`.
- Uses the HuggingFace Dataset API to create a dataset from all triplets and saves it at `OUTPUT_PATH` in the .arrow and .jsonl formats.

### Example Usage

This details the command and process used to generate the example dataset found in `./sample_ds4`. The document is a pdf of the Wikipedia page on the United States of America. 
```bash 
python3 raft.py --datapath sample_data/United_States_PDF.pdf --output ./sample_ds4 --distractors 4 --doctype pdf --chunk_size 512 --questions 5 --openai_key OPENAI_KEY
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


 #### 5. Finetune your own model on Microsoft AI Studio
 Once the dataset is prepared, follow the instructions in `azure-ai-studio-ft/howto.md` to finetune and deploy your own RAFT model. Make sure to use domain `instruction` as input and `cot_answer` as output.

 #### 6. Evaluate RAFT model
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
