# Berkeley Function Calling Leaderboard

💡 Read more in our [Gorilla OpenFunctions Leaderboard Blog](https://gorilla.cs.berkeley.edu/blogs/8_berkeley_function_calling_leaderboard.html)

🦍 Berkeley Function Calling Leaderboard live [Berkeley Function Calling Leaderboard](https://gorilla.cs.berkeley.edu/leaderboard.html#leaderboard)

🦍 Berkeley Function Calling Leaderboard on Hugginface [Berkeley Function Calling Leaderboard Huggingface](https://huggingface.co/spaces/gorilla-llm/berkeley-function-calling-leaderboard)

## Introduction
We present Berkeley Function Leaderboard, the **first comprehensive and executable function calling evaluation for LLMs function calling**. Different from prior function calling evaluations (e.g. Anyscale function calling blog), we consider function callings of various forms, different function calling scenarios, and the executability of function calls. We also release our model Gorilla-Openfunctions-v2, the best open-source models so far to handle multiple languages of function calls, parallel function calls and multiple function calls. We also provide a specific debugging feature that when the provided function is not suitable for your task, the model will output an “Error Message”. 

Read more about the technical details and interesting insights in our blog post!

![image](./architecture_diagram.png)
### Install Dependencies

Before generating the leaderboard statistics, you should install dependencies using the following command: 

```bash
conda create -n BFCL python=3.10
conda activate BFCL
pip install -r requirements.txt # Inside ./berkeley-function-call-leaderboard
pip install vllm # If you have vLLM supported GPU(s) and want to run our evaluation data against self-hosted OSS models.
```
If you plan to evaluate on OSS models, we are using vLLM for inference and refer to https://github.com/vllm-project/vllm for detail. We recommend to inference on at least V100s, A100s, and latest GPUs that are supported by vLLM. 

### Checker Setup (required for Java, JavaScript test categories)
We use `tree-sitter` to do the AST parsing for Java and JavaScript test categories. Thus, you need to install `tree-sitter`.

The git clones need to be under the `/berkeley-function-call-leaderboard/eval_checker` folder.

```bash
cd ./eval_checker
git clone https://github.com/tree-sitter/tree-sitter-java.git
git clone https://github.com/tree-sitter/tree-sitter-javascript.git
```

Now, move back to `/berkeley-function-call-leaderboard` by `cd ..`, and create two symbolic links to the `tree-sitter-java` and `tree-sitter-javascript` directories. This is required to run `openfunctions_evaluation.py`.

```
ln -s eval_checker/tree-sitter-java tree-sitter-java
ln -s eval_checker/tree-sitter-javascript tree-sitter-javascript
```

## Prepare Evaluation Dataset

To download the evaluation dataset from huggingface, from the current directory `./berkeley-function-call-leaderboard`, run the following command:

```bash
huggingface-cli download gorilla-llm/Berkeley-Function-Calling-Leaderboard --local-dir ./data --repo-type dataset
```


This will download our dataset to `data` repository. 

## Evaluation Dataset

The evaluation datasets are now stored in the `./data` folder. The possible answers are stored in the `./data/possible_answer` folder. 


## Execution Evaluation Data Post-processing 
Input your API keys into `function_credential_config.json`, so that the original placeholder values in questions, params, and answers will be cleaned. 

To run the executable test categories, there are 4 API keys to fill out:

1. RAPID-API Key: https://rapidapi.com/hub

    * Yahoo Finance: https://rapidapi.com/sparior/api/yahoo-finance15
    * Real Time Amazon Data : https://rapidapi.com/letscrape-6bRBa3QguO5/api/real-time-amazon-data
    * Urban Dictionary: https://rapidapi.com/community/api/urban-dictionary
    * Covid 19: https://rapidapi.com/api-sports/api/covid-193
    * Time zone by Location: https://rapidapi.com/BertoldVdb/api/timezone-by-location

    All the Rapid APIs we use have free tier usage. As a result, you need to subscribe to those API providers in order to have the executable test environment setup but it will be free of charge!

2. Exchange Rate API:https://www.exchangerate-api.com
3. OMDB API: http://www.omdbapi.com/apikey.aspx
4. Geocode API: https://geocode.maps.co/

The `apply_function_credential_config.py` inputs an input file, optionally an outputs file. If the output file is not given as an argument, it will overwrites your original file with the cleaned data.

```bash
python apply_function_credential_config.py --input-file ./data/gorilla_openfunctions_v1_test_rest.json
```

Then, use `eval_data_compilation.py` to compile all files by using

```bash
python eval_data_compilation.py
```
## Berkeley Function-Calling Leaderboard Statistics

To run Mistral Models function calling, you need to have `mistralai >= 0.1.3`.

Also provide your API keys in your environment variables.

```bash
export OPENAI_API_KEY=sk-XXXXXX
export MISTRAL_API_KEY=XXXXXX
export FIRE_WORKS_API_KEY=XXXXXX
export ANTHROPIC_API_KEY=XXXXXX
export COHERE_API_KEY=XXXXXX
export NVIDIA_API_KEY=nvapi-XXXXXX
```

To generate leaderboard statistics, there are two steps:

1. Inference the evaluation data and obtain the results from specific models 

```bash
python openfunctions_evaluation.py --model MODEL_NAME --test-category TEST_CATEGORY
```
For TEST_CATEGORY, we have `executable_simple`, `executable_parallel_function`, `executable_multiple_function`, `executable_parallel_multiple_function`, `simple`, `relevance`, `parallel_function`, `multiple_function`, `parallel_multiple_function`, `java`, `javascript`, `rest`, `sql`, `chatable`.

If you want to run all evaluations at the same time, you can use `all` as the test category.

Running proprietary models like GPTs, Claude, Mistral-X will require an API-Key which can be supplied in `openfunctions_evaluation.py`.

If decided to run OSS model, openfunction evaluation uses vllm and therefore requires GPU for hosting and inferencing. If you have questions or concerns about evaluating OSS models, please reach out to us in our [discord channel](https://discord.gg/grXXvj9Whz).




## Checking the Evaluation Results

### Running the Checker

Navigate to the `./berkeley-function-call-leaderboard/eval_checker` directory and run the `eval_runner.py` script with the desired parameters. The basic syntax is as follows:

```bash
python ./eval_runner.py --model MODEL_NAME --test-category {TEST_CATEGORY,all,ast,executable,python,non-python}
```

- `MODEL_NAME`: Optional. The name of the model you wish to evaluate. This parameter can accept multiple model names separated by spaces. Eg, `--model gorilla-openfunctions-v2 gpt-4-0125-preview`.
    - If no model name is provided, the script will run the checker on all models exist in the `./result` folder. This path can be changed by modifying the `INPUT_PATH` variable in the `eval_runner.py` script.
- `TEST_CATEGORY`: Optional. The category of tests to run. You can specify multiple categories separated by spaces. Available options include:
    - `all`: Run all test categories.
    - `ast`: Abstract Syntax Tree tests.
    - `executable`: Executable code evaluation tests.
    - `python`: Tests specific to Python code.
    - `non-python`: Tests for code in languages other than Python, such as Java and JavaScript.
    - Individual test categories:
        - `simple`: Simple function calls.
        - `parallel_function`: Multiple function calls in parallel.
        - `multiple_function`: Multiple function calls in sequence.
        - `parallel_multiple_function`: Multiple function calls in parallel and in sequence.
        - `executable_simple`: Executable function calls.
        - `executable_parallel_function`: Executable multiple function calls in parallel.
        - `executable_multiple_function`: Executable multiple function calls in sequence.
        - `executable_parallel_multiple_function`: Executable multiple function calls in parallel and in sequence.
        - `java`: Java function calls.
        - `javascript`: JavaScript function calls.
        - `rest`: REST API function calls.
        - `relevance`: Function calls with irrelevant function documentation.
    - If no test category is provided, the script will run all available test categories.
> If you want to run the `all` or `executable` or `python` category, make sure to register your REST API keys in `function_credential_config.json`. This is because Gorilla Openfunctions Leaderboard wants to test model's generated output on real world API! 

> If you do not wish to provide API keys for REST API testing, set `test-category` to `ast` or any non-executable category.

> By default, if the test categories include `executable`, the evaluation process will perform the REST API sanity check first to ensure that all the API endpoints involved during the execution evaluation process are working properly. If any of them are not behaving as expected, the evaluation process will be stopped by default as the result will be inaccurate. You can choose to bypass this check by setting the `--skip-api-sanity-check` flag, or `-s` for short.

### Example Usage

If you want to run all tests for the `gorilla-openfunctions-v2` model, you can use the following command:

```bash
python ./eval_runner.py --model gorilla-openfunctions-v2
```

If you want to runn `rest` tests for all GPT models, you can use the following command:

```bash
python ./eval_runner.py --model gpt-3.5-turbo-0125 gpt-4-0613 gpt-4-1106-preview gpt-4-0125-preview --test-category rest
```

If you want to run `rest` and `javascript` tests for all GPT models and `gorilla-openfunctions-v2`, you can use the following command:

```bash
python ./eval_runner.py --model gorilla-openfunctions-v2 gpt-3.5-turbo-0125 gpt-4-0613 gpt-4-1106-preview gpt-4-0125-preview --test-category rest javascript
```

### Model-Specific Optimization

Some companies have proposed some optimization strategies in their models' handler, which we (BFCL) think is unfair to other models, as those optimizations are not generalizable to all models. Therefore, we have disabled those optimizations during the evaluation process by default. You can enable those optimizations by setting the `USE_{COMPANY}_OPTIMIZATION` flag to `True` in the `model_handler/constants.py` file.


## Models Available
Below is *a table of models we support* to run our leaderboard evaluation against. If supported function calling (FC), we will follow its function calling format provided by official documentation. Otherwise, we will construct a system message to prompt the model to generate function calls in the right format.
|Model | Type |
|---|---|
|gorilla-openfunctions-v2 | Function Calling|
|claude-3-{opus-20240229,sonnet-20240229,haiku-20240307}-FC | Function Calling |
|claude-3-{opus-20240229,sonnet-20240229,haiku-20240307} | Prompt |
|claude-{2.1,instant-1.2}| Prompt|
|command-r-plus-FC | Function Calling|
|command-r-plus | Prompt|
|databrick-dbrx-instruct | Prompt|
|deepseek-ai/deepseek-coder-6.7b-instruct 💻| Prompt|
|firefunction-{v1,v2}-FC | Function Calling|
|gemini-1.0-pro | Function Calling|
|gemini-1.5-pro-preview-{0409,0514} | Function Calling|
|gemini-1.5-flash-preview-0514 | Function Calling|
|glaiveai/glaive-function-calling-v1 💻| Function Calling|
|gpt-3.5-turbo-0125-FC| Function Calling|
|gpt-3.5-turbo-0125| Prompt|
|gpt-4-{0613,1106-preview,0125-preview,turbo-2024-04-09}-FC| Function Calling|
|gpt-4-{0613,1106-preview,0125-preview,turbo-2024-04-09}| Prompt|
|gpt-4o-2024-05-13-FC | Function Calling|
|gpt-4o-2024-05-13| Prompt|
|google/gemma-7b-it 💻| Prompt|
|meetkai/functionary-{small,medium}-v2.4-FC| Function Calling|
|meetkai/functionary-small-v2.2-FC| Function Calling|
|meta-llama/Meta-Llama-3-{8B,70B}-Instruct | Prompt|
|mistral-large-2402-FC-{Any,Auto} | Function Calling|
|mistral-large-2402 | Prompt|
|mistral-medium-2312 | Prompt|
|mistral-small-2402-FC-{Any,Auto} | Function Calling|
|mistral-small-2402 | Prompt|
|mistral-tiny-2312 | Prompt|
|Nexusflow-Raven-v2 | Function Calling|
|NousResearch/Hermes-2-Pro-Mistral-7B 💻| Function Calling|
|snowflake/arctic | Prompt| 

Here {MODEL} 💻 means the model needs to be hosted locally and called by vllm, {MODEL} means the models that are called API calls. For models with a trailing `-FC`, it means that the model supports function-calling feature. You can check out the table summarizing feature supports among different models [here](https://gorilla.cs.berkeley.edu/blogs/8_berkeley_function_calling_leaderboard.html#prompt).


For model names with {.}, it means that the model has multiple versions. For example, we provide evaluation on three versions of GPT-4: `gpt-4-0125-preview`, `gpt-4-1106-preview`, and `gpt-4-0613`.

For Mistral large and small models, we provide evaluation on both of their `Any` and `Auto` settings. More information about this can be found [here](https://docs.mistral.ai/guides/function-calling/).


For inferencing `Gemini-1.0-pro`, you need to fill in `model_handler/gemini_handler.py` with your GCP project ID that has access to Vertex AI endpoint.
For inferencing `Databrick-DBRX-instruct`, you need to create a Databrick Azure workspace and setup an endpoint for inference. 


## Changelog

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
* [April 10, 2024] [#339](https://github.com/ShishirPatil/gorilla/pull/339): Introduce REST API sanity check for the REST executable test category. It ensures that all the API endpoints involved during the execution evaluation process are working properly. If any of them are not behaving as expected, the evaluation process will be stopped by default as the result will be inaccurate. Users can choose to bypass this check by setting the `--skip-api-sanity-check` flag or `-s` for short.
* [April 9, 2024] [#338](https://github.com/ShishirPatil/gorilla/pull/338): Bug fix in the evaluation datasets (including both prompts and function docs). Bug fix for possible answers as well.
* [April 8, 2024] [#330](https://github.com/ShishirPatil/gorilla/pull/330): Fixed an oversight that was introduced in [#299](https://github.com/ShishirPatil/gorilla/pull/299). For function-calling (FC) models that cannot take `float` type in input, when the parameter type is a `float`, the evaluation procedure will convert that type to `number` in the model input and mention in the parameter description that `This is a float type value.`. An additional field `format: float` will also be included in the model input to make it clear about the type. Updated the model handler for Claude, Mistral, and OSS to better parse the model output.
* [April 8, 2024] [#327](https://github.com/ShishirPatil/gorilla/pull/327): Add new model `NousResearch/Hermes-2-Pro-Mistral-7B` to the leaderboard.
* [April 3, 2024] [#309](https://github.com/ShishirPatil/gorilla/pull/309): Bug fix for evaluation dataset possible answers. Implement **string standardization** for the AST evaluation pipeline, i.e. removing white spaces and a subset of punctuations (`,./-_*^`) to make the AST evaluation more robust and accurate. Fixed AST evaluation issue for type `tuple`. Add 2 new models `meetkai/functionary-small-v2.4 (FC)`, `meetkai/functionary-medium-v2.4 (FC)` to the leaderboard.
* [April 1, 2024] [#299](https://github.com/ShishirPatil/gorilla/pull/299): Leaderboard update with new models (`Claude-3-Haiku`, `Databrick-DBRX-Instruct`), more advanced AST evaluation procedure, and updated evaluation datasets. Cost and latency statistics during evaluation are also measured. We also released the manual that our evaluation procedure is based on, available [here](https://gorilla.cs.berkeley.edu/blogs/8_berkeley_function_calling_leaderboard.html#metrics).
* [Mar 11, 2024] [#254](https://github.com/ShishirPatil/gorilla/pull/254): Leaderboard update with 3 new models: `Claude-3-Opus-20240229 (Prompt)`, `Claude-3-Sonnet-20240229 (Prompt)`, and `meetkai/functionary-medium-v2.2 (FC)`
* [Mar 5, 2024] [#237](https://github.com/ShishirPatil/gorilla/pull/237) and [238](https://github.com/ShishirPatil/gorilla/pull/238): leaderboard update resulting from [#223](https://github.com/ShishirPatil/gorilla/pull/223); 3 new models: `mistral-large-2402`, `gemini-1.0-pro`, and `gemma`.
* [Feb 29, 2024] [#223](https://github.com/ShishirPatil/gorilla/pull/223): modifications to REST evaluation. 


## Contributing

To add a new model to the Function Calling Leaderboard, here are a few things you need to do:

1. Take a look at the `model_handler/handler.py`. This is the base handler object where all handlers are inherited from 
2. Create your handler and define the following functions 
    1. `__init__`: on initialization, you need to create a `self.client` object if you have an existing endpoint(e.g. `self.client = OpenAI()`) or follow `model_handler/oss_handler.py` for starting a vLLM serving.
    2. `inference`: inference function takes in prompt, functions, as well as optional programming language parameters. It will make call to the endpoint, compile result in the desired format, as well as logging the token number and latency
    3. `decode_ast`: decode_ast will convert the response from raw output in the format of `[{func1:{param1:val1,...}},{func2:{param2:val2,...}}] This format will be used to check for exact matching the parameters.
    4. `decode_execute`: deocde_execute will convert the response from raw output in the format of `"[func1(param1=val1),func2(param2=val2)]"`
3. Modify `model_handler/handler_map.py`. This mapping contains the key as the exact model name and value as the handler object of the specific model. 
4. If your model is price-based, please update the pricing detail, i.e. price per million tokens under `eval_runner_helper.py`
5. Raise a [Pull Request](https://github.com/ShishirPatil/gorilla/pulls) with your new Model Handler. We will run the model handler if an endpoint is established. If self-hosting is required and the model size is large, we might not be able to accommodate model hosting therefore an OpenAI compatible endpoint for evaluation is desired. 
6. Feel Free to join [Gorilla Discord](https://discord.gg/grXXvj9Whz) `#leaderboard` and reach out to us for any questions or concerns about adding new models. We are happy to help you!


All the leaderboard statistics, and data used to train the models are released under Apache 2.0.
Gorilla is an open source effort from UC Berkeley and we welcome contributors. 
Please email us your comments, criticisms, and questions. More information about the project can be found at [https://gorilla.cs.berkeley.edu/](https://gorilla.cs.berkeley.edu/)

