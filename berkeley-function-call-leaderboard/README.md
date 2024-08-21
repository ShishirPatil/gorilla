# Berkeley Function Calling Leaderboard (BFCL)

💡 Read more in our [Gorilla OpenFunctions Leaderboard Blog](https://gorilla.cs.berkeley.edu/blogs/8_berkeley_function_calling_leaderboard.html)

🦍 Berkeley Function Calling Leaderboard live [Berkeley Function Calling Leaderboard](https://gorilla.cs.berkeley.edu/leaderboard.html#leaderboard)

🦍 Berkeley Function Calling Leaderboard on Hugginface [Berkeley Function Calling Leaderboard Huggingface](https://huggingface.co/spaces/gorilla-llm/berkeley-function-calling-leaderboard)

## Introduction
We introduce the Berkeley Function Leaderboard (BFCL), the **first comprehensive and executable function call evaluation dedicated to assessing Large Language Models' (LLMs) ability to invoke functions**. Unlike previous function call evaluations, BFCL accounts for various forms of function calls, diverse function calling scenarios, and their executability. Additionally, we release Gorilla-Openfunctions-v2, the most advanced open-source model to date capable of handling multiple languages, parallel function calls, and multiple function calls simultaneously. A unique debugging feature of this model is its ability to output an "Error Message" when the provided function does not suit your task.

Read more about the technical details and interesting insights in our [blog post](https://gorilla.cs.berkeley.edu/blogs/8_berkeley_function_calling_leaderboard.html)!

![image](./architecture_diagram.png)
### Install Dependencies

```bash
conda create -n BFCL python=3.10
conda activate BFCL
pip install -r requirements.txt # Inside gorilla/berkeley-function-call-leaderboard
```

**Note**: If you have GPU(s) and want to run our evaluation data against self-hosted OSS models, you can choose to use `vllm` or `sglang` for inference. This only works on Linux or Windows, but not on MacOS.

To use `vllm`, you need to install the `vllm` package. 
```bash
pip install vllm==0.5.4
```

To use `sglang`, you need to install the `sglang` package, and the `flashinfer` package
```bash
pip install sglang==0.2.13
```
Depends on the CUDA version, you can find the specific `flashinfer` installation command [here](https://docs.flashinfer.ai/installation.html).



## Execution Evaluation Data Post-processing (Can be Skipped: Necesary for Executable Test Categories)
Add your keys into `function_credential_config.json`, so that the original placeholder values in questions, params, and answers will be reset.

To run the executable test categories, there are 4 API keys to include:

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

The `apply_function_credential_config.py` will automatically search for dataset files in the default `./data/` directory and replace the placeholder values with the actual API keys.

```bash
python apply_function_credential_config.py
```


## Evaluating different models on the BFCL

Make sure the model API keys are included in your environment variables. Running proprietary models like GPTs, Claude, Mistral-X will require them.

```bash
export OPENAI_API_KEY=sk-XXXXXX
export MISTRAL_API_KEY=XXXXXX
export FIRE_WORKS_API_KEY=XXXXXX
export ANTHROPIC_API_KEY=XXXXXX
export COHERE_API_KEY=XXXXXX
export NVIDIA_API_KEY=nvapi-XXXXXX
export YI_API_KEY=XXXXXX
```

If decided to run OSS model, the generation script uses vllm and therefore requires GPU for hosting and inferencing. If you have questions or concerns about evaluating OSS models, please reach out to us in our [discord channel](https://discord.gg/grXXvj9Whz).

### Generating LLM Responses

Use the following command for LLM inference of the evaluation dataset with specific models. 

```bash
python openfunctions_evaluation.py --model MODEL_NAME --test-category TEST_CATEGORY --num-threads 1 --backend {vllm,sglang}
```
You can optionally specify the number of threads to use for *parallel inference* by setting the `--num-threads` flag to speed up inference for **hosted models**, not applicable for OSS models. The default is 1, which means no parallel inference.

If you want to self-host the OSS models, you can choose between `vllm` and `sglang` as the backend and set the `--backend` flag. The default is `sglang`.

For available options for `MODEL_NAME` and `TEST_CATEGORY`, please refer to the [Models Available](#models-available) and [Available Test Category](#available-test-category) section below.

If no `MODEL_NAME` is provided, the model `gorilla-openfunctions-v2` will be used by default. If no `TEST_CATEGORY` is provided, all test categories will be run by default.

### Models Available
Below is *a table of models we support* to run our leaderboard evaluation against. If the models support function calling (FC), we will follow its function calling format provided by official documentation. Otherwise, we use a consistent system message to prompt the model to generate function calls in the right format.
|Model | Type |
|---|---|
|gorilla-openfunctions-v2 | Function Calling|
|claude-3-{opus-20240229,sonnet-20240229,haiku-20240307}-FC | Function Calling |
|claude-3-{opus-20240229,sonnet-20240229,haiku-20240307} | Prompt |
|claude-3-5-sonnet-20240620-FC | Function Calling |
|claude-3-5-sonnet-20240620 | Prompt |
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
|gpt-4o-2024-08-06-FC | Function Calling|
|gpt-4o-2024-08-06 | Prompt|
|gpt-4o-2024-05-13-FC | Function Calling|
|gpt-4o-2024-05-13| Prompt|
|gpt-4o-mini-2024-07-18-FC | Function Calling|
|gpt-4o-mini-2024-07-18 | Prompt|
|google/gemma-7b-it 💻| Prompt|
|meetkai/functionary-medium-v3.1-FC| Function Calling|
|meetkai/functionary-small-{v3.1,v3.2}-FC| Function Calling|
|meta-llama/Meta-Llama-3-{8B,70B}-Instruct | Prompt|
|open-mixtral-{8x7b,8x22b} | Prompt|
|open-mixtral-8x22b-FC-{Any,Auto} | Function Calling|
|open-mistral-nemo-2407 | Prompt|
|open-mistral-nemo-2407-FC-{Any,Auto} | Function Calling|
|mistral-large-2407-FC-{Any,Auto} | Function Calling|
|mistral-large-2407 | Prompt|
|mistral-medium-2312 | Prompt|
|mistral-small-2402-FC-{Any,Auto} | Function Calling|
|mistral-small-2402 | Prompt|
|mistral-tiny-2312 | Prompt|
|Nexusflow-Raven-v2 | Function Calling|
|NousResearch/Hermes-2-Pro-Llama-3-{8B,70B} 💻| Function Calling|
|NousResearch/Hermes-2-Pro-Mistral-7B 💻| Function Calling|
|NousResearch/Hermes-2-Theta-Llama-3-{8B,70B} 💻| Function Calling|
|snowflake/arctic | Prompt|
|Salesforce/xLAM-1b-fc-r 💻| Function Calling|
|Salesforce/xLAM-7b-fc-r 💻| Function Calling|
|nvidia/nemotron-4-340b-instruct| Prompt|
|THUDM/glm-4-9b-chat 💻| Function Calling|
|ibm-granite/granite-20b-functioncalling 💻| Function Calling|
|yi-large-fc | Function Calling|

Here {MODEL} 💻 means the model needs to be hosted locally and called by vllm, {MODEL} means the models that are called API calls. For models with a trailing `-FC`, it means that the model supports function-calling feature. You can check out the table summarizing feature supports among different models [here](https://gorilla.cs.berkeley.edu/blogs/8_berkeley_function_calling_leaderboard.html#prompt).


For model names with {.}, it means that the model has multiple versions. For example, we provide evaluation on three versions of GPT-4: `gpt-4-0125-preview`, `gpt-4-1106-preview`, and `gpt-4-0613`.

For Mistral large and small models, we provide evaluation on both of their `Any` and `Auto` settings. More information about this can be found [here](https://docs.mistral.ai/guides/function-calling/).


For `Gemini-1.0-pro`, you need to fill in `model_handler/gemini_handler.py` with your GCP project ID that has access to Vertex AI endpoint.
For `Databrick-DBRX-instruct`, you need to create a Databrick Azure workspace and setup an endpoint for inference. 


### Available Test Category
In the following two sections, the optional `--test-category` parameter can be used to specify the category of tests to run. You can specify multiple categories separated by spaces. Available options include:

* Available test groups:
  * `all`: All test categories.
    * This is the default option if no test category is provided.
  * `live`: All user-contributed live test categories.
  * `non_live`: All not-user-contributed test categories (the opposite of `live`).
  * `ast`: Abstract Syntax Tree tests.
  * `executable`: Executable code evaluation tests.
  * `python`: Tests specific to Python code.
  * `non_python`: Tests for code in languages other than Python, such as Java and JavaScript.
  * `python_ast`: Python Abstract Syntax Tree tests.
* Available individual test categories:
  * `simple`: Simple function calls.
  * `parallel`: Multiple function calls in parallel.
  * `multiple`: Multiple function calls in sequence.
  * `parallel_multiple`: Multiple function calls in parallel and in sequence.
  * `java`: Java function calls.
  * `javascript`: JavaScript function calls.
  * `exec_simple`: Executable function calls.
  * `exec_parallel`: Executable multiple function calls in parallel.
  * `exec_multiple`: Executable multiple function calls in parallel.
  * `exec_parallel_multiple`: Executable multiple function calls in parallel and in sequence.
  * `rest`: REST API function calls.
  * `irrelevance`: Function calls with irrelevant function documentation.
  * `live_simple`: User-contributed simple function calls.
  * `live_multiple`: User-contributed multiple function calls in sequence.
  * `live_parallel`: User-contributed multiple function calls in parallel.
  * `live_parallel_multiple`: User-contributed multiple function calls in parallel and in sequence.
  * `live_irrelevance`: User-contributed function calls with irrelevant function documentation.
  * `live_relevance`: User-contributed function calls with relevant function documentation.
* If no test category is provided, the script will run all available test categories. (same as `all`)

> If you want to run the `all`, `non_live`, `executable` or `python` category, make sure to register your REST API keys in `function_credential_config.json`. This is because Gorilla Openfunctions Leaderboard wants to test model's generated output on real world API!

> If you do not wish to provide API keys for REST API testing, set `test-category` to any non-executable category.

> By setting the `--api-sanity-check` flag, or `-c` for short, if the test categories include any executable categories (eg, the test name contains `exec`), the evaluation process will perform the REST API sanity check first to ensure that all the API endpoints involved during the execution evaluation process are working properly. If any of them are not behaving as expected, we will flag those in the console and continue execution.


## Evaluating the LLM generations

### Running the Checker

Navigate to the `gorilla/berkeley-function-call-leaderboard/eval_checker` directory and run the `eval_runner.py` script with the desired parameters. The basic syntax is as follows:

```bash
python eval_runner.py --model MODEL_NAME --test-category TEST_CATEGORY
```

For available options for `MODEL_NAME` and `TEST_CATEGORY`, please refer to the [Models Available](#models-available) and [Available Test Category](#available-test-category) section.

If no `MODEL_NAME` is provided, all available model results will be evaluated by default. If no `TEST_CATEGORY` is provided, all test categories will be run by default.

### Example Usage

If you want to run all tests for the `gorilla-openfunctions-v2` model, you can use the following command:

```bash
python eval_runner.py --model gorilla-openfunctions-v2
```

If you want to evaluate all offline tests (do not require RapidAPI keys) for OpenAI GPT-3.5, you can use the following command:

```bash
python eval_runner.py --model gpt-3.5-turbo-0125 --test-category ast
```

If you want to run the `rest` tests for a few Claude models, you can use the following command:

```bash
python eval_runner.py --model claude-3-5-sonnet-20240620 claude-3-opus-20240229 claude-3-sonnet-20240229 --test-category rest
```

If you want to run `live_simple` and `javascript` tests for a few models and `gorilla-openfunctions-v2`, you can use the following command:

```bash
python eval_runner.py --model gorilla-openfunctions-v2 claude-3-5-sonnet-20240620 gpt-4-0125-preview gemini-1.5-pro-preview-0514 --test-category live_simple javascript
```

### Model-Specific Optimization

Some companies have proposed some optimization strategies in their models' handler, which we (BFCL) think is unfair to other models, as those optimizations are not generalizable to all models. Therefore, we have disabled those optimizations during the evaluation process by default. You can enable those optimizations by setting the `USE_{COMPANY}_OPTIMIZATION` flag to `True` in the `model_handler/constants.py` file.


## Changelog

* [August 19, 2024] [#580](https://github.com/ShishirPatil/gorilla/pull/580): Introduce BFCL V2 Live dataset, featuring user-contributed live prompts and function docs. To read more about the composition and construction of this dataset, please refer to our [blog](https://gorilla.cs.berkeley.edu/blogs/12_bfcl_v2_live.html). All CLI commands have been updated to support the new dataset.
* [August 8, 2024] [#574](https://github.com/ShishirPatil/gorilla/pull/574): Set temperature to 0.001 for all models for consistency and reproducibility.
* [August 7, 2024] [#571](https://github.com/ShishirPatil/gorilla/pull/571): Support parallel inference for hosted models. User can specify the number of threads to use for parallel inference by setting the `--num-threads` flag. The default is 1, which means no parallel inference.
* [August 6, 2024] [#569](https://github.com/ShishirPatil/gorilla/pull/569), [#570](https://github.com/ShishirPatil/gorilla/pull/570), [#573](https://github.com/ShishirPatil/gorilla/pull/573): Add the following new models to the leaderboard:
  * `open-mistral-nemo-2407`
  * `open-mistral-nemo-2407-FC-Any`
  * `open-mistral-nemo-2407-FC-Auto`
  * `open-mixtral-8x22b`
  * `open-mixtral-8x22b-FC-Any`
  * `open-mixtral-8x22b-FC-Auto`
  * `open-mixtral-8x7b`
  * `gpt-4o-mini-2024-07-18`
  * `gpt-4o-mini-2024-07-18-FC`
  * `gpt-4o-2024-08-06`
  * `gpt-4o-2024-08-06-FC`
  * `meetkai/functionary-medium-v3.1-FC`
  * `meetkai/functionary-small-v3.1-FC`
  * `meetkai/functionary-small-v3.2-FC`
* [August 5, 2024] [#568](https://github.com/ShishirPatil/gorilla/pull/568): Rephrase the question prompt for the `executable_parallel_function` category to remove potentially misleading information implying multi-turn function calls.
* [August 4, 2024] [#557](https://github.com/ShishirPatil/gorilla/pull/557): Bug fix in the possible answers.
  * simple: 7 affected
  * multiple function: 3 affected
  * parallel function: 5 affected
  * parallel multiple function: 6 affected
  * executable parallel function: 1 affected
  * javascript: 3 affected
* [July 26, 2024] [#549](https://github.com/ShishirPatil/gorilla/pull/549): Fix js_type_converter.py to properly handle JavaScript array value inside dictionary.
* [July 25, 2024] [#532](https://github.com/ShishirPatil/gorilla/pull/532), [#543](https://github.com/ShishirPatil/gorilla/pull/543), [#556](https://github.com/ShishirPatil/gorilla/pull/556), [#542](https://github.com/ShishirPatil/gorilla/pull/542): Add the following new models to the leaderboard:
    - `Salesforce/xLAM-7b-fc-r`
    - `Salesforce/xLAM-1b-fc-r`
    - `yi-large-fc`
    - `NousResearch/Hermes-2-Pro-Llama-3-8B`
    - `NousResearch/Hermes-2-Pro-Llama-3-70B`
    - `NousResearch/Hermes-2-Theta-Llama-3-8B`
    - `NousResearch/Hermes-2-Theta-Llama-3-70B`
* [July 22, 2024] [#540](https://github.com/ShishirPatil/gorilla/pull/540): Chore: Improve handling of vLLM's cleanup phase error by combining all selected test categories into one single task to submit to the vLLM server.
* [July 21, 2024] [#538](https://github.com/ShishirPatil/gorilla/pull/538), [#545](https://github.com/ShishirPatil/gorilla/pull/545): Fix `language_specific_pre_processing` and `convert_to_tool` function to properly handle pre-processing for prompts and function docs in Java and JavaScript test categories. All entries in these categories are affected.
* [July 20, 2024] [#537](https://github.com/ShishirPatil/gorilla/pull/537): Update generation script for locally-hosted OSS model to use single-node multi-GPU inference method (tensor parallel). Ray is not used anymore.
* [July 16, 2024] [#525](https://github.com/ShishirPatil/gorilla/pull/525), [#536](https://github.com/ShishirPatil/gorilla/pull/536): Add new model `ibm-granite/granite-20b-functioncalling` to the leaderboard.
* [July 10, 2024] [#522](https://github.com/ShishirPatil/gorilla/pull/522): Bug fix in the evaluation dataset for Executable Parallel Multiple category. This includes updates to both prompts and function docs. 2 entries are affected.
* [July 8, 2024] [#516](https://github.com/ShishirPatil/gorilla/pull/516): Fix double-casting issue in `model_handler` for Java and JavaScript test categories.
* [July 7, 2024] [#504](https://github.com/ShishirPatil/gorilla/pull/504), [#505](https://github.com/ShishirPatil/gorilla/pull/505), [#506](https://github.com/ShishirPatil/gorilla/pull/506), [#508](https://github.com/ShishirPatil/gorilla/pull/508), [#510](https://github.com/ShishirPatil/gorilla/pull/510), [#512](https://github.com/ShishirPatil/gorilla/pull/512), [#517](https://github.com/ShishirPatil/gorilla/pull/517): Make BFCL user-friendly and easy to extend.
* [July 6, 2024] [#423](https://github.com/ShishirPatil/gorilla/pull/423) and [#503](https://github.com/ShishirPatil/gorilla/pull/503): Bug fix in possible answers for the AST evaluation dataset (parallel category: 14 affected; parallel_multiple category: 25 affected).
* [July 5, 2024] [#496](https://github.com/ShishirPatil/gorilla/pull/496): Updates to API status checks. Checking the health of executable APIs is now off by default. Further, even when triggered, un-healthy APIs will not terminate the evaluation process. Users can enable this feature by setting the `--api-sanity-check` flag or `-c` for short. The previous `--skip-api-sanity-check` or `-s` flag is now deprecated.
* [July 3, 2024] [#489](https://github.com/ShishirPatil/gorilla/pull/489): Add new model `nvidia/nemotron-4-340b-instruct` to the leaderboard.
* [July 2, 2024] [#474](https://github.com/ShishirPatil/gorilla/pull/474): Add new model `THUDM/glm-4-9b-chat` to the leaderboard.
* [June 18, 2024] [#470](https://github.com/ShishirPatil/gorilla/pull/470): Add new model `firefunction-v2-FC` to the leaderboard.
* [June 15, 2024] [#437](https://github.com/ShishirPatil/gorilla/pull/437): Fix prompting issues for `Nexusflow-Raven-v2 (FC)`.
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
* [Mar 5, 2024] [#237](https://github.com/ShishirPatil/gorilla/pull/237) and [238](https://github.com/ShishirPatil/gorilla/pull/238): leaderboard update resulting from [#223](https://github.com/ShishirPatil/gorilla/pull/223); 3 new models: `mistral-large-2402`, `gemini-1.0-pro`, and `google/gemma-7b-it`.
* [Feb 29, 2024] [#223](https://github.com/ShishirPatil/gorilla/pull/223): modifications to REST evaluation. 


## Contributing

We welcome additions to the Function Calling Leaderboard! To add a new model, here are a few things you need to do:

1. Take a look at the `model_handler/handler.py`. This is the base handler object which all handlers are inherited from. Also, free feel to take a look at the existing model handers; very likely you can re-use some of the existing code if the new model outputs in a similar format.
2. Create your handler and define the following functions 
    1. `__init__`: on initialization, you need to create a `self.client` object if you have an existing endpoint(e.g. `self.client = OpenAI()`) or follow `model_handler/oss_handler.py` for starting a vLLM serving.
    2. `inference`: inference function takes in prompt, functions, as well as optional programming language parameters. It will make call to the endpoint, compile result in the desired format, as well as logging the token number and latency
    3. `decode_ast`: decode_ast will convert the response from raw output in the format of `[{func1:{param1:val1,...}},{func2:{param2:val2,...}}]` This format will be used to check for exact matching the parameters.
    4. `decode_execute`: deocde_execute will convert the response from raw output in the format of `"[func1(param1=val1),func2(param2=val2)]"`
3. Modify `model_handler/handler_map.py`. This mapping contains the key as the exact model name and value as the handler object of the specific model.
4. Modify `eval_checker/eval_runner_helper.py`:
    - Update the `MODEL_METADATA_MAPPING` with the model display name, URL, license and company information. The key should be the same as the one in `model_handler/handler_map.py`.
    - If your model is price-based, you should update the `INPUT_PRICE_PER_MILLION_TOKEN` and `OUTPUT_PRICE_PER_MILLION_TOKEN`. - If your model doesn't have a cost, you should add it to the `NO_COST_MODELS` list.
    - If your model is open-source and is hosted locally, the `OSS_LATENCY` list needs to be updated with the latency for the whole batch of data generation. This information will affect the cost calculation.
5. Raise a [Pull Request](https://github.com/ShishirPatil/gorilla/pulls) with your new Model Handler. We will run the model handler if an endpoint is established. If self-hosting is required and the model size is large, we might not be able to accommodate model hosting therefore an OpenAI compatible endpoint for evaluation is desired. 
6. Feel Free to join [Gorilla Discord](https://discord.gg/grXXvj9Whz) `#leaderboard` and reach out to us for any questions or concerns about adding new models. We are happy to help you!


All the leaderboard statistics, and data used to train the models are released under Apache 2.0.
Gorilla is an open source effort from UC Berkeley and we welcome contributors. 
Please email us your comments, criticisms, and questions. More information about the project can be found at [https://gorilla.cs.berkeley.edu/](https://gorilla.cs.berkeley.edu/)

