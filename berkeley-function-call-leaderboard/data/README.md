---
license: apache-2.0
language:
  - en
---

# Berkeley Function Calling Leaderboard

The Berkeley function calling leaderboard is a live leaderboard to evaluate the ability of different LLMs to call functions (also referred to as tools).
We built this dataset from our learnings to be representative of most users' function calling use-cases, for example, in agents, as a part of enterprise workflows, etc.
To this end, our evaluation dataset spans diverse categories, and across multiple languages.

Checkout the Leaderboard at [gorilla.cs.berkeley.edu/leaderboard.html](https://gorilla.cs.berkeley.edu/leaderboard.html)
and our release blogs:

[BFCL V1](https://gorilla.cs.berkeley.edu/blogs/8_berkeley_function_calling_leaderboard.html): Our initial BFCL release

[BFCL V2](https://gorilla.cs.berkeley.edu/blogs/12_bfcl_v2_live.html): Our second release, employing enterprise and OSS-contributed live data

[BFCL V3](https://gorilla.cs.berkeley.edu/blogs/13_bfcl_v3_multi_turn.html#composition): Introduces multi-turn and multi-step function calling scenarios

**_Latest Version Release Date_**: 09/22/2024

**_Original Release Date_**: 02/26/2024

## Prepare Evaluation Dataset

To use the BFCL dataset, please follow the instructions detailed in the README [here](https://github.com/ShishirPatil/gorilla/tree/main/berkeley-function-call-leaderboard).

The BFCL dataset is organized in multiple JSON files, where each file representing a test category. Each line in the JSON file is a JSON object. You can use the following helper functions to load the dataset:

```python
def load_file(file_path: str):
    result = []
    with open(file_path) as f:
        file = f.readlines()
        for line in file:
            result.append(json.loads(line))
    return result
```

If you prefer a Hugging Face Datasets–compatible format, you can use the following helper function to convert the list of dictionaries (returned by `load_file`) into a Dataset object.

> Note: This process will convert the function parameters field into a JSON string due to its complex structure. You may need to parse them back into dictionaries during evaluation.

```python
from datasets import Dataset
import copy
import json

def load_json_dataset(test_entries: List[Dict[str, Any]]):
    data = {"id": [], "question": [], "function": []}
    test_entries_copy = copy.deepcopy(test_entries)

    for item in test_entries_copy:
        data["id"].append(item["id"])
        data["question"].append(item["question"])

        for func in item["function"]:
            func["parameters"]["properties"] = json.dumps(
                func["parameters"]["properties"]
            )
        data["function"].append(func)
    return Dataset.from_dict(data)

# Example usage
test_entries = load_file("path_to_your_file.json")
ds = load_json_dataset(test_entries)
```

## Dataset Composition

We break down our dataset into our 3 major releases. The composition of each release is as follows:

**BFCL V1**:

![image/png](https://cdn-uploads.huggingface.co/production/uploads/63814d392dd1f3e7bf59862f/IE-HwJL1OUSi-Tc2fT-oo.png)

**BFCL V2 Live**:

![image/png](https://gorilla.cs.berkeley.edu/assets/img/blog_post_12_composition.png)

**BFCL V3 Multi-Turn**:

<p align="center">
  <img src="https://gorilla.cs.berkeley.edu/assets/img/blog_post_13_data_composition.png" alt="BFCL V3 data composition"/>
</p>

### Dataset Description

## BFCL V1:

In our first release, the majority of our evaluation is broken into two categories:

- **Python**: Simple Function, Multiple Function, Parallel Function, Parallel Multiple Function
- **Non-Python**: Chatting Capability, Function Relevance Detection, REST API, SQL, Java, Javascript

#### Python

**Simple (400 AST/100 Exec)**: Single function evaluation contains the simplest but most commonly seen format, where the user supplies a single JSON function document, with one and only one function call being invoked.

**Multiple Function (200 AST/50 Exec)**: Multiple function category contains a user question that only invokes one function call out of 2 to 4 JSON function documentations. The model needs to be capable of selecting the best function to invoke according to user-provided context.

**Parallel Function (200 AST/50 Exec)**: Parallel function is defined as invoking multiple function calls in parallel with one user query. The model needs to digest how many function calls need to be made and the question to model can be a single sentence or multiple sentence.

**Parallel Multiple Function (200 AST/40 Exec)**: Parallel Multiple function is the combination of parallel function and multiple function. In other words, the model is provided with multiple function documentation, and each of the corresponding function calls will be invoked zero or more times.

Each category has both AST and its corresponding executable evaluations. In the executable evaluation data, we manually write Python functions drawing inspiration from free REST API endpoints (e.g. get weather) and functions (e.g. linear regression) that compute directly. The executable category is designed to understand whether the function call generation is able to be stably utilized in applications utilizing function calls in the real world.

#### Non-Python Evaluation

While the previous categories consist of the majority of our evaluations, we include other specific categories, namely Chatting Capability, Function Relevance Detection, REST API, SQL, Java, and JavaScript, to evaluate model performance on diverse scenarios and support of multiple programming languages, and are resilient to irrelevant questions and function documentations.

**Chatting Capability (200)**: In Chatting Capability, we design scenarios where no functions are passed in, and the users ask generic questions - this is similar to using the model as a general-purpose chatbot. We evaluate if the model is able to output chat messages and recognize that it does not need to invoke any functions. Note the difference with “Relevance” where the model is expected to also evaluate if any of the function inputs are relevant or not. We include this category for internal model evaluation and exclude the statistics from the live leaderboard. We currently are working on a better evaluation of chat ability and ensuring the chat is relevant and coherent with users' requests and open to suggestions and feedback from the community.

**Function Relevance Detection (240)**: In function relevance detection, we design scenarios where none of the provided functions are relevant and supposed to be invoked. We expect the model's output to be a non-function-call response. This scenario provides insight into whether a model will hallucinate on its functions and parameters to generate function code despite lacking the function information or instructions from the users to do so.

**REST API (70)**: A majority of the real-world API calls are from REST API calls. Python mainly makes REST API calls through `requests.get()`, `requests.post()`, `requests.delete()`, etc that are included in the Python requests library. `GET` requests are the most common ones used in the real world. As a result, we include real-world `GET` requests to test the model's capabilities to generate executable REST API calls through complex function documentation, using `requests.get()` along with the API's hardcoded URL and description of the purpose of the function and its parameters. Our evaluation includes two variations. The first type requires passing the parameters inside the URL, called path parameters, for example, the `{Year}` and `{CountryCode}` in `GET` `/api/v3/PublicHolidays/{Year}/{CountryCode}`. The second type requires the model to put parameters as key/value pairs into the params and/or headers of `requests.get(.)`. For example, `params={'lang': 'fr'}` in the function call. The model is not given which type of REST API call it is going to make but needs to make a decision on how it's going to be invoked.

For REST API, we use an executable evaluation to check for the executable outputs' effective execution, response type, and response JSON key consistencies. On the AST, we chose not to perform AST evaluation on REST mainly because of the immense number of possible answers; the enumeration of all possible answers is exhaustive for complicated defined APIs.

**SQL (100)**: SQL evaluation data includes our customized `sql.execute` functions that contain sql_keyword, table_name, columns, and conditions. Those four parameters provide the necessary information to construct a simple SQL query like `SELECT column_A from table_B where column_C == D` Through this, we want to see if through function calling, SQL query can be reliably constructed and utilized rather than training a SQL-specific model. In our evaluation dataset, we restricted the scenarios and supported simple keywords, including `SELECT`, `INSERT INTO`, `UPDATE`, `DELETE`, and `CREATE`. We included 100 examples for SQL AST evaluation. Note that SQL AST evaluation will not be shown in our leaderboard calculations. We use SQL evaluation to test the generalization ability of function calling for programming languages that are not included in the training set for Gorilla OpenFunctions-v2. We opted to exclude SQL performance from the AST evaluation in the BFCL due to the multiplicity of methods to construct SQL function calls achieving identical outcomes. We're currently working on a better evaluation of SQL and are open to suggestions and feedback from the community. Therefore, SQL has been omitted from the current leaderboard to pave the way for a more comprehensive evaluation in subsequent iterations.

**Java (100) and Javascript (50)**: Despite function calling formats being the same across most programming languages, each programming language has language-specific types. For example, Java has the `HashMap` type. The goal of this test category is to understand how well the function calling model can be extended to not just Python type but all the language-specific typings. We included 100 examples for Java AST evaluation and 70 examples for Javascript AST evaluation.

The categories outlined above provide insight into the performance of different models across popular API call scenarios, offering valuable perspectives on the potential of function-calling models.

## BFCL V2 Live:

Our second release uses real world data in order to better measure LLM function calling performance in real world uses cases. To this end, there is a greater focus on the multiple function scenario, as well as relevance/irrelevance detection. The data in BFCL V2 Live is comprised of **simple (258)**, **multiple (1037)**, **parallel (16)**, and **parallel multiple (24)** categories, similar to those described in BFCL V1. In addition to these, we have the **Relevance** category, which can be broken down into the following two subcategories.

#### Relevance Evaluation

**Irrelevance Detection (875)**: The scenario where none of the function choices provided are relevant to the user query and none should be invoked. We expect the model to not output a function call; the model can either output a message explaining why the function provided are not relevant or simply output a non-function call response (e.g., an empty list).

**Relevance Detection (41)**: The opposite of irrelevance detection. The scenario where at least one of the function choices provided are relevant to the user query and should be invoked, but the way the user prompt or the function doc is stated means that there could be infinitely many correct function calls and impossible to use a pre-defined possible answer set to evaluate. We expect the model to output some function call (one or multiple) that is relevant to the user query; we don't check for the correctness of the function call in this category (eg, correct parameter value).

## BFCL V3:

This release introduces scenarios that require multi-step function calling, where multiple internal function calls can be used to address a single user request, as well as multi-turn function calls, which involve multiple exchanges or function calls between user and assistant. Within our multi-step and multi-turn data are the following categories:

**Base Multi-Turn (200)**: This category covers the foundational yet sufficiently diverse basic multi-turn interactions. In this category, we provide complete information to call each function (either through current turn question, execution result from previous turn, or initial state configuration)

**Augmented Multi-Turn (800)**: This category introduce additional complexity, such as ambiguous prompts or situations where the model must process multiple pieces of information across turns (similar to Multihop QA), requiring models to handle more nuanced decision-making, disambiguation, and conditional logic across multiple turns.
The augmented multiturn data is comprised of the followin subcategories:

- **Missing Parameters (200)**: This dataset challenges the model to identify required missing information that cannot be retrieved elsewhere in the system. In this scenario, we expect the LLM to ask for a follow-up to clarify the misinformation. This is distinct from certain entries in the Core Multi-Turn dataset where the question has implicit intent that can be answered by referencing the backend system.

- **Missing Functions (200)**: This scenario denotes when we expect the model to recognize that no action should be taken given the lack of functions provided. If the LLM raises that concern, we then supply it with the hold-out functions that can successfully perform user intended tasks. Note that the Core dataset and the Missing Function dataset essentially contains the same sequence of actions except for the latter we hold-out a subset of functions on execution path to further challenge the model's inference ability.

- **Long-Context (200)**: This dataset challenges the model's resilience in long context scenarios on function calling. We inject random objects (e.g. hundreds of files in one directory or thousands of booking records) to mimic real world API output, which tend to be overtly informative. Here, we aim to test the model's ability to grasp the core information from an overwhelmingly large context.

- **Composite (200)**: Composite Category seeks to combine all three scenarios above to create an exceptionally hard challenge that, despite being rare, is important to handle when using autonomous agents at scale. Through this category, we want to convince the audience that a good model performance in this category offers a strong signal that LLMs can function as autonomous agents at scale despite rare and extremely difficult scenarios.

### Evaluation

This dataset serves as the question + function documentation pairs for Berkeley Function-Calling Leaderboard (BFCL) evaluation. The source code for the evaluation process can be found [here](https://github.com/ShishirPatil/gorilla/tree/main/berkeley-function-call-leaderboard) with detailed instructions on how to use this dataset to compare LLM tool use capabilities across different models and categories.

More details on evaluation metrics, i.e. rules for the Abstract Syntax Tree (AST) and executable evaluation can be found in the [release blog](https://gorilla.cs.berkeley.edu/blogs/8_berkeley_function_calling_leaderboard.html#metrics).

### Contributing

All the models, and data used to train the models are released under Apache 2.0.
Gorilla is an open source effort from UC Berkeley and we welcome contributors.
Please email us your comments, criticisms, and questions.
More information about the project can be found at https://gorilla.cs.berkeley.edu/

### BibTex

```bibtex
@misc{berkeley-function-calling-leaderboard,
  title={Berkeley Function Calling Leaderboard},
  author={Fanjia Yan and Huanzhi Mao and Charlie Cheng-Jie Ji and Tianjun Zhang and Shishir G. Patil and Ion Stoica and Joseph E. Gonzalez},
  howpublished={\url{https://gorilla.cs.berkeley.edu/blogs/8_berkeley_function_calling_leaderboard.html}},
  year={2024},
}
```
