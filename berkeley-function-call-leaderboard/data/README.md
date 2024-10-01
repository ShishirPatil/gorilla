---
license: apache-2.0
language:
- en
---
# Berkeley Function Calling Leaderboard 

<!-- Provide a quick summary of the dataset. -->

The Berkeley function calling leaderboard is a live leaderboard to evaluate the ability of different LLMs to call functions (also referred to as tools). 
We built this dataset from our learnings to be representative of most users' function calling use-cases, for example, in agents, as a part of enterprise workflows, etc. 
To this end, our evaluation dataset spans diverse categories, and across multiple languages. 

Checkout the Leaderboard at [gorilla.cs.berkeley.edu/leaderboard.html](https://gorilla.cs.berkeley.edu/leaderboard.html) 
and our release blogs:

[BFCL V1](https://gorilla.cs.berkeley.edu/blogs/8_berkeley_function_calling_leaderboard.html): Our initial BFCL release

[BFCL V2](https://gorilla.cs.berkeley.edu/blogs/12_bfcl_v2_live.html): Our second release, employing enterprise and OSS-contributed live data

[BFCL V3](https://gorilla.cs.berkeley.edu/blogs/13_bfcl_v3_multi_turn.html#composition): Introduces multi-turn and multi-step function calling scenarios

***Latest Version Release Date***: 09/22/2024

***Original Release Date***: 02/26/2024

Details of the change log can be found at the end of this README.

## Prepare Evaluation Dataset
To download and prepare the BFCL dataset, please follow the instructions detailed in [`Prepare Evaluation Dataset` section](https://github.com/ShishirPatil/gorilla/tree/main/berkeley-function-call-leaderboard#prepare-evaluation-dataset) and [`Execution Evaluation Data Post-processing` section](https://github.com/ShishirPatil/gorilla/tree/main/berkeley-function-call-leaderboard#execution-evaluation-data-post-processing) of https://github.com/ShishirPatil/gorilla/tree/main/berkeley-function-call-leaderboard README.

The BFCL dataset is organized in multiple JSON files, where each file representing a test category. The helper function loads a JSON file into a list of dictionaries, which is used in the BFCL evaluation procedure. 

**DO NOT** use the HuggingFace `load_dataset` method to load the dataset as our dataset is not compatible with the HuggingFace datasets package. We will try to fix this later to provide alternative ways to access the dataset.

## Dataset Composition

We break down our dataset into our 3 major releases. The composition of each release is as follows:

## BFCL V1:

![image/png](https://cdn-uploads.huggingface.co/production/uploads/63814d392dd1f3e7bf59862f/IE-HwJL1OUSi-Tc2fT-oo.png)

## BFCL V2 Live:

![image/png](https://gorilla.cs.berkeley.edu/assets/img/blog_post_12_composition.png)

## BFCL V3:

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

**Irrelevance detection (875)**: The scenario where none of the function choices provided are relevant to the user query and none should be invoked. We expect the model to not output a function call; the model can either output a message explaining why the function provided are not relevant or simply output a non-function call response (e.g., an empty list).

**Relevance detection (41)**: The opposite of irrelevance detection. The scenario where at least one of the function choices provided are relevant to the user query and should be invoked, but the way the user prompt or the function doc is stated means that there could be infinitely many correct function calls and impossible to use a pre-defined possible answer set to evaluate. We expect the model to output some function call (one or multiple) that is relevant to the user query; we don't check for the correctness of the function call in this category (eg, correct parameter value).

## BFCL V3:
This release introduces scenarios that require multi-step function calling, where multiple internal function calls can be used to address a single user request, as well as multi-turn function calls, which involve multiple exchanges or function calls between user and assistant. Within our multi-step and multi-turn data are the following categories:

**Base multiturn (200)**: This category covers the foundational yet sufficiently diverse basic multi-turn interactions. In this category, we provide complete information to call each function (either through current turn question, execution result from previous turn, or initial state configuration)

**Augmented multiturn (800)**: This category introduce additional complexity, such as ambiguous prompts or situations where the model must process multiple pieces of information across turns (similar to Multihop QA), requiring models to handle more nuanced decision-making, disambiguation, and conditional logic across multiple turns.
The augmented multiturn data is comprised of the followin subcategories:
- **Missing Parameters (200)**: This dataset challenges the model to identify required missing information that cannot be retrieved elsewhere in the system. In this scenario, we expect the LLM to ask for a follow-up to clarify the misinformation. This is distinct from certain entries in the Core Multi-Turn dataset where the question has implicit intent that can be answered by referencing the backend system.

- **Missing Functions (200)**: This scenario denotes when we expect the model to recognize that no action should be taken given the lack of functions provided. If the LLM raises that concern, we then supply it with the hold-out functions that can successfully perform user intended tasks. Note that the Core dataset and the Missing Function dataset essentially contains the same sequence of actions except for the latter we hold-out a subset of functions on execution path to further challenge the model's inference ability.

- **Long-Context Multi-Turn (200)**: This dataset challenges the model's resilience in long context scenarios on function calling. We inject random objects (e.g. hundreds of files in one directory or thousands of booking records) to mimic real world API output, which tend to be overtly informative. Here, we aim to test the model's ability to grasp the core information from an overwhelmingly large context.

- **Composite (200)**: Composite Category seeks to combine all three scenarios above to create an exceptionally hard challenge that, despite being rare, is important to handle when using autonomous agents at scale. Through this category, we want to convince the audience that a good model performance in this category offers a strong signal that LLMs can function as autonomous agents at scale despite rare and extremely difficult scenarios.


### Evaluation

This dataset serves as the question + function documentation pairs for Berkeley Function-Calling Leaderboard (BFCL) evaluation. The source code for the evaluation process can be found [here](https://github.com/ShishirPatil/gorilla/tree/main/berkeley-function-call-leaderboard) with detailed instructions on how to use this dataset to compare LLM tool use capabilities across different models and categories.

More details on evaluation metrics, i.e. rules for the Abstract Syntax Tree (AST) and executable evaluation can be found in the [release blog](https://gorilla.cs.berkeley.edu/blogs/8_berkeley_function_calling_leaderboard.html#metrics).


### Contributing

All the models, and data used to train the models are released under Apache 2.0.
Gorilla is an open source effort from UC Berkeley and we welcome contributors. 
Please email us your comments, criticisms, and questions. 
More information about the project can be found at https://gorilla.cs.berkeley.edu/

### Change Log
The Berkeley Function Calling Leaderboard is a continually evolving project. We are committed to regularly updating the dataset and leaderboard by introducing new models and expanding evaluation categories. Below is an overview of the modifications implemented in the most recent version:

* [June 7, 2024] [#407](https://github.com/ShishirPatil/gorilla/pull/407), [#462](https://github.com/ShishirPatil/gorilla/pull/462): Update the AST evaluation logic to allow the use of `int` values for Python parameters expecting `float` values. This is to accommodate the Python auto-conversion feature from `int` to `float`.
* [May 14, 2024] [#426](https://github.com/ShishirPatil/gorilla/pull/426):
    - Add the following new models to the leaderboard:
        + `gpt-4o-2024-05-13`
        + `gpt-4o-2024-05-13-FC`
        + `gemini-1.5-pro-preview-0514`
        + `gemini-1.5-flash-preview-0514`
    - Update price for the following models:
        + All Gemini Series
        + `Claude-2.1 (Prompt)` and `Claude-instant-1.2 (Prompt)`
        + `Mistral-large` and `Mistral-Small`
        + `GPT-3.5-Turbo-0125`
* [May 8, 2024] [#406](https://github.com/ShishirPatil/gorilla/pull/406) and [#421](https://github.com/ShishirPatil/gorilla/pull/421): Update the `gemini_handler.py` to better handle parallel function calls for Gemini models.
* [May 6, 2024] [#412](https://github.com/ShishirPatil/gorilla/pull/412): Bug fix in evaluation dataset for AST categories. This includes updates to both prompts and function docs.
* [May 2, 2024] [#405](https://github.com/ShishirPatil/gorilla/pull/405): Bug fix in the possible answers for the AST Simple evaluation dataset. Prompt and function docs are not affected.
* [April 28, 2024] [#397](https://github.com/ShishirPatil/gorilla/pull/397): Add new model `snowflake/arctic` to the leaderboard. Note that there are multiple ways to inference the model, and we choose to do it via Nvidia API catalog. 
* [April 27, 2024] [#390](https://github.com/ShishirPatil/gorilla/pull/390): Bug fix in cost and latency calculation for open-source models, which are now all calculated when serving the model with [vLLM](https://github.com/vllm-project/vllm) using 8 V100 GPUs for consistency. $$\text{Cost} = \text{Latency per 1000 function call} * (\text{8xV100 azure-pay-as-you-go-price per hour / 3600})$$
* [April 25, 2024] [#386](https://github.com/ShishirPatil/gorilla/pull/386): Add 5 new models to the leaderboard: `meta-llama/Meta-Llama-3-8B-Instruct`, `meta-llama/Meta-Llama-3-70B-Instruct`, `gemini-1.5-pro-preview-0409`, `command-r-plus`, `command-r-plus-FC`.
* [April 19, 2024] [#377](https://github.com/ShishirPatil/gorilla/pull/377): 
    - Bug fix for the evaluation dataset in the executable test categories. This includes updates to both prompts and function docs.
    - The `evaluation_result` field has been removed to accommodate the variability in API execution results across different evaluation runs. Instead, a human-verified `ground_truth` is now included for the executable test categories. During each evaluation run, `evaluation_result` is generated anew using the `ground_truth`, and then compared against the model output. 
    - A stricter metric has been adopted when using the `structural_match` (aka. type match) evaluation criteria ---- For `list` results, the lengths are compared; for `dict` results, the keys are matched. This is to account for the fast-changing nature of some of the real-time API results while ensuring the evaluation remains meaningful.
    - Added another evaluation criteria `real_time_match` for the executable category, which is a looser form of `exact_match` specifically for numerical execution results. The execution result must be within a certain percentage threshold (20%) from the expected result to accommodate the live updates of API responses. User can change this threshold value in `eval_checker_constant.py`.
* [April 18, 2024] [#375](https://github.com/ShishirPatil/gorilla/pull/375): A more comprehensive API sanity check is included; the APIs that are invoked during the non-REST executable evaluation process will also be checked for their availability before running the evaluation. Also, add support for the shortcut `-s` for the `--skip-api-sanity-check` flag, based on the community feedback.
* [April 16, 2024] [#366](https://github.com/ShishirPatil/gorilla/pull/366): Switch to use Anthropic's new Tool Use Beta `tools-2024-04-04` when generating Claude 3 FC series data. `gpt-4-turbo-2024-04-09` and `gpt-4-turbo-2024-04-09-FC` are also added to the leaderboard.
* [April 11, 2024] [#347](https://github.com/ShishirPatil/gorilla/pull/347): Add the 95th percentile latency to the leaderboard statistics. This metric is useful for understanding the latency distribution of the models, especially the worst-case scenario.
* [April 10, 2024] [#339](https://github.com/ShishirPatil/gorilla/pull/339): Introduce REST API sanity check for the executable test category. It ensures that all the API endpoints involved during the execution evaluation process are working properly. If any of them are not behaving as expected, the evaluation process will be stopped by default as the result will be inaccurate. Users can choose to bypass this check by setting the `--skip-api-sanity-check` flag.
* [April 9, 2024] [#338](https://github.com/ShishirPatil/gorilla/pull/338): Bug fix in the evaluation datasets (including both prompts and function docs). Bug fix for possible answers as well.
* [April 8, 2024] [#330](https://github.com/ShishirPatil/gorilla/pull/330): Fixed an oversight that was introduced in [#299](https://github.com/ShishirPatil/gorilla/pull/299). For function-calling (FC) models that cannot take `float` type in input, when the parameter type is a `float`, the evaluation procedure will convert that type to `number` in the model input and mention in the parameter description that `This is a float type value.`. An additional field `format: float` will also be included in the model input to make it clear about the type. Updated the model handler for Claude, Mistral, and OSS to better parse the model output.
* [April 3, 2024] [#309](https://github.com/ShishirPatil/gorilla/pull/309): Bug fix for evaluation dataset possible answers. Implement **string standardization** for the AST evaluation pipeline, i.e. removing white spaces and a subset of punctuations `,./-_*^` to make the AST evaluation more robust and accurate. Fixed AST evaluation issue for type `tuple`. Add 2 new models `meetkai/functionary-small-v2.4 (FC)`, `meetkai/functionary-medium-v2.4 (FC)` to the leaderboard.
* [April 1, 2024] [#299](https://github.com/ShishirPatil/gorilla/pull/299): Leaderboard update with new models (`Claude-3-Haiku`, `Databrick-DBRX-Instruct`), more advanced AST evaluation procedure, and updated evaluation datasets. Cost and latency statistics during evaluation are also measured. We also released the manual that our evaluation procedure is based on, available [here](https://gorilla.cs.berkeley.edu/blogs/8_berkeley_function_calling_leaderboard.html#metrics).
* [Mar 11, 2024] [#254](https://github.com/ShishirPatil/gorilla/pull/254): Leaderboard update with 3 new models: `Claude-3-Opus-20240229 (Prompt)`, `Claude-3-Sonnet-20240229 (Prompt)`, and `meetkai/functionary-medium-v2.2 (FC)`
* [Mar 5, 2024] [#237](https://github.com/ShishirPatil/gorilla/pull/237) and [238](https://github.com/ShishirPatil/gorilla/pull/238): leaderboard update resulting from [#223](https://github.com/ShishirPatil/gorilla/pull/223); 3 new models: `mistral-large-2402`, `gemini-1.0-pro`, and `gemma`.
* [Feb 29, 2024] [#223](https://github.com/ShishirPatil/gorilla/pull/223): Modifications to REST evaluation. 
* [Feb 27, 2024] [#215](https://github.com/ShishirPatil/gorilla/pull/215): BFCL first release.

### BibTex

```bibtex
@misc{berkeley-function-calling-leaderboard,
  title={Berkeley Function Calling Leaderboard},
  author={Fanjia Yan and Huanzhi Mao and Charlie Cheng-Jie Ji and Tianjun Zhang and Shishir G. Patil and Ion Stoica and Joseph E. Gonzalez},
  howpublished={\url{https://gorilla.cs.berkeley.edu/blogs/8_berkeley_function_calling_leaderboard.html}},
  year={2024},
}