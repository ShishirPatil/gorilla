# Berkeley Function Calling Leaderboard (BFCL)

## Introduction

We introduce the Berkeley Function Leaderboard (BFCL), the **first comprehensive and executable function call evaluation dedicated to assessing Large Language Models' (LLMs) ability to invoke functions**. Unlike previous function call evaluations, BFCL accounts for various forms of function calls, diverse function calling scenarios, and their executability.

💡 Read more in our Gorilla OpenFunctions Leaderboard Blogs:

- [BFCL v1 (original) Blog Post](https://gorilla.cs.berkeley.edu/blogs/8_berkeley_function_calling_leaderboard.html)
- [BFCL v2 (live dataset) Blog Post](https://gorilla.cs.berkeley.edu/blogs/12_bfcl_v2_live.html)
- [BFCL v3 (multi-turn) Blog Post](https://gorilla.cs.berkeley.edu/blogs/13_bfcl_v3_multi_turn.html)

🦍 See the Berkeley Function Calling Leaderboard live at [Berkeley Function Calling Leaderboard](https://gorilla.cs.berkeley.edu/leaderboard.html#leaderboard)

![image](./architecture_diagram.png)

## Install Dependencies

```bash
# Create a new Conda environment with Python 3.10
conda create -n BFCL python=3.10

# Activate the new environment
conda activate BFCL

# Clone the Gorilla repository
git clone https://github.com/ShishirPatil/gorilla.git

# Change directory to the berkeley-function-call-leaderboard
cd gorilla/berkeley-function-call-leaderboard

# Install the package in editable mode
pip install -e .
```

### Installing Extra Dependencies for Self-Hosted Open Source Models

To do LLM generation on self-hosted open source models, you need to run the following command to install the extra dependencies.

```bash
pip install -e .[oss_eval]
```

Note that this requires GPU supported by vLLM and it can only be installed on Linux and Windows (not Mac).

### Setting up Environment Variables

We use `.env` file to store the environment variables. We have provided a sample `.env.example` file in the `gorilla/berkeley-function-call-leaderboard` directory. You should make a copy of this file, rename it to `.env` and fill in the necessary values.

```bash
cp .env.example .env
```

### API Keys for Execution Evaluation Data Post-processing (Can be Skipped: Necessary for Executable Test Categories)

Add your keys into the `.env` file, so that the original placeholder values in questions, params, and answers will be reset.

To run the executable test categories, there are 4 API keys to include:

1. RAPID-API Key: https://rapidapi.com/hub

   - Yahoo Finance: https://rapidapi.com/sparior/api/yahoo-finance15
   - Real Time Amazon Data : https://rapidapi.com/letscrape-6bRBa3QguO5/api/real-time-amazon-data
   - Urban Dictionary: https://rapidapi.com/community/api/urban-dictionary
   - Covid 19: https://rapidapi.com/api-sports/api/covid-193
   - Time zone by Location: https://rapidapi.com/BertoldVdb/api/timezone-by-location

   All the Rapid APIs we use have free tier usage. You need to **subscribe** to those API providers in order to have the executable test environment setup but it will be _free of charge_!

2. Exchange Rate API:https://www.exchangerate-api.com
3. OMDB API: http://www.omdbapi.com/apikey.aspx
4. Geocode API: https://geocode.maps.co/

The evaluation script will automatically search for dataset files in the default `./data/` directory and replace the placeholder values with the actual API keys you provided in the `.env` file.

## Evaluating different models on the BFCL

Make sure the model API keys are included in your `.env` file. Running proprietary models like GPTs, Claude, Mistral-X will require them.

```bash
OPENAI_API_KEY=sk-XXXXXX
MISTRAL_API_KEY=
FIREWORKS_API_KEY=
ANTHROPIC_API_KEY=
NVIDIA_API_KEY=nvapi-XXXXXX
YI_API_KEY=

VERTEX_AI_PROJECT_ID=
VERTEX_AI_LOCATION=

COHERE_API_KEY=

DATABRICKS_API_KEY=
DATABRICKS_AZURE_ENDPOINT_URL=
```

If decided to run locally-hosted model, the generation script uses vLLM and therefore requires GPU for hosting and inferencing. If you have questions or concerns about evaluating OSS models, please reach out to us in our [discord channel](https://discord.gg/grXXvj9Whz).

### Generating LLM Responses

Use the following command for LLM inference of the evaluation dataset with specific models.

```bash
python openfunctions_evaluation.py --model MODEL_NAME --test-category TEST_CATEGORY --num-threads 1
```

You can optionally specify the number of threads to use for _parallel inference_ by setting the `--num-threads` flag to speed up inference for **hosted models**, not applicable for OSS models.

For available options for `MODEL_NAME` and `TEST_CATEGORY`, please refer to the [Models Available](#models-available) and [Available Test Category](#available-test-category) section below.

If no `MODEL_NAME` is provided, the model `gorilla-openfunctions-v2` will be used by default. If no `TEST_CATEGORY` is provided, all test categories will be run by default.

### Models Available

Below is _a table of models we support_ to run our leaderboard evaluation against. If the models support function calling (FC), we will follow its function calling format provided by official documentation. Otherwise, we use a consistent system message to prompt the model to generate function calls in the right format.

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
|gemini-1.0-pro-{001,002}-FC | Function Calling|
|gemini-1.0-pro-{001,002} | Prompt|
|gemini-1.5-pro-{001,002}-FC | Function Calling|
|gemini-1.5-pro-{001,002} | Prompt|
|gemini-1.5-flash-{001,002}-FC | Function Calling|
|gemini-1.5-flash-{001,002} | Prompt|
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
|meta-llama/Meta-Llama-3-{8B,70B}-Instruct 💻| Prompt|
|meta-llama/Llama-3.1-{8B,70B}-Instruct-FC 💻| Function Calling|
|meta-llama/Llama-3.1-{8B,70B}-Instruct 💻| Prompt|
|meta-llama/Llama-3.2-{1B,3B}-Instruct-FC 💻| Function Calling|
|meta-llama/Llama-3.2-{1B,3B}-Instruct 💻| Prompt|
|open-mixtral-{8x7b,8x22b} | Prompt|
|open-mixtral-8x22b-FC | Function Calling|
|open-mistral-nemo-2407 | Prompt|
|open-mistral-nemo-2407-FC | Function Calling|
|mistral-large-2407-FC | Function Calling|
|mistral-large-2407 | Prompt|
|mistral-medium-2312 | Prompt|
|mistral-small-2402-FC | Function Calling|
|mistral-small-2402 | Prompt|
|mistral-tiny-2312 | Prompt|
|Nexusflow-Raven-v2 | Function Calling|
|NousResearch/Hermes-2-Pro-Llama-3-{8B,70B} 💻| Function Calling|
|NousResearch/Hermes-2-Pro-Mistral-7B 💻| Function Calling|
|NousResearch/Hermes-2-Theta-Llama-3-{8B,70B} 💻| Function Calling|
|snowflake/arctic | Prompt|
|Salesforce/xLAM-1b-fc-r 💻| Function Calling|
|Salesforce/xLAM-7b-fc-r 💻| Function Calling|
|Salesforce/xLAM-7b-r 💻| Function Calling|
|Salesforce/xLAM-8x7b-r 💻| Function Calling|
|Salesforce/xLAM-8x22b-r 💻| Function Calling|
|microsoft/Phi-3.5-mini-instruct 💻| Prompt|
|microsoft/Phi-3-medium-{4k,128k}-instruct 💻| Prompt|
|microsoft/Phi-3-small-{8k,128k}-instruct 💻| Prompt|
|microsoft/Phi-3-mini-{4k,128k}-instruct 💻| Prompt|
|nvidia/nemotron-4-340b-instruct| Prompt|
|THUDM/glm-4-9b-chat 💻| Function Calling|
|ibm-granite/granite-20b-functioncalling 💻| Function Calling|
|yi-large-fc | Function Calling|
|MadeAgents/Hammer-7b 💻| Function Calling|
|Qwen/Qwen2.5-{1.5B,7B}-Instruct 💻| Prompt|
|Qwen/Qwen2-{1.5B,7B}-Instruct 💻| Prompt|
|Team-ACE/ToolACE-8B 💻| Function Calling|

Here {MODEL} 💻 means the model needs to be hosted locally and called by vllm, {MODEL} means the models that are called API calls. For models with a trailing `-FC`, it means that the model supports function-calling feature. You can check out the table summarizing feature supports among different models [here](https://gorilla.cs.berkeley.edu/blogs/8_berkeley_function_calling_leaderboard.html#prompt).

For model names with `{.}`, it means that the model has multiple versions. For example, we provide evaluation on three versions of GPT-4: `gpt-4-0125-preview`, `gpt-4-1106-preview`, and `gpt-4-0613`.

For `Gemini` models, you need to provide your `VERTEX_AI_PROJECT_ID` and ``VERTEX_AI_LOCATION`` in the `.env` file.
For `Databrick-DBRX-instruct`, you need to create a Databrick Azure workspace and setup an endpoint for inference (provide the `DATABRICKS_AZURE_ENDPOINT_URL` in the `.env` file).

### Available Test Category

In the following two sections, the optional `--test-category` parameter can be used to specify the category of tests to run. You can specify multiple categories separated by spaces. Available options include:

- Available test groups:
  - `all`: All test categories.
    - This is the default option if no test category is provided.
  - `multi_turn`: All multi-turn test categories.
  - `single_turn`: All single-turn test categories.
  - `live`: All user-contributed live test categories.
  - `non_live`: All not-user-contributed test categories (the opposite of `live`).
  - `ast`: Abstract Syntax Tree tests.
  - `executable`: Executable code evaluation tests.
  - `python`: Tests specific to Python code.
  - `non_python`: Tests for code in languages other than Python, such as Java and JavaScript.
  - `python_ast`: Python Abstract Syntax Tree tests.
- Available individual test categories:
  - `simple`: Simple function calls.
  - `parallel`: Multiple function calls in parallel.
  - `multiple`: Multiple function calls in sequence.
  - `parallel_multiple`: Multiple function calls in parallel and in sequence.
  - `java`: Java function calls.
  - `javascript`: JavaScript function calls.
  - `exec_simple`: Executable function calls.
  - `exec_parallel`: Executable multiple function calls in parallel.
  - `exec_multiple`: Executable multiple function calls in parallel.
  - `exec_parallel_multiple`: Executable multiple function calls in parallel and in sequence.
  - `rest`: REST API function calls.
  - `irrelevance`: Function calls with irrelevant function documentation.
  - `live_simple`: User-contributed simple function calls.
  - `live_multiple`: User-contributed multiple function calls in sequence.
  - `live_parallel`: User-contributed multiple function calls in parallel.
  - `live_parallel_multiple`: User-contributed multiple function calls in parallel and in sequence.
  - `live_irrelevance`: User-contributed function calls with irrelevant function documentation.
  - `live_relevance`: User-contributed function calls with relevant function documentation.
  - `multi_turn_base`: Base entries for multi-turn function calls.
  - `multi_turn_miss_func`: Multi-turn function calls with missing function.
  - `multi_turn_miss_param`: Multi-turn function calls with missing parameter.
  - `multi_turn_long_context`: Multi-turn function calls with long context.
  - `multi_turn_composite`: Multi-turn function calls with missing function, missing parameter, and long context.
- If no test category is provided, the script will run all available test categories. (same as `all`)

> If you want to run the `all`, `non_live`, `executable` or `python` category, make sure to register your REST API keys in the `.env` file. This is because Gorilla Openfunctions Leaderboard wants to test model's generated output on real world API!

> If you do not wish to provide API keys for REST API testing, set `test-category` to any non-executable category.

> By setting the `--api-sanity-check` flag, or `-c` for short, if the test categories include any executable categories (eg, the test name contains `exec`), the evaluation process will perform the REST API sanity check first to ensure that all the API endpoints involved during the execution evaluation process are working properly. If any of them are not behaving as expected, we will flag those in the console and continue execution.

## Evaluating the LLM generations

### Running the Checker

Navigate to the `gorilla/berkeley-function-call-leaderboard/bfcl/eval_checker` directory and run the `eval_runner.py` script with the desired parameters. The basic syntax is as follows:

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

Some companies have proposed some optimization strategies in their models' handler, which we (BFCL) think is unfair to other models, as those optimizations are not generalizable to all models. Therefore, we have disabled those optimizations during the evaluation process by default. You can enable those optimizations by setting the `USE_{COMPANY}_OPTIMIZATION` flag to `True` in the `.env` file.

## Contributing

We welcome additions to the Function Calling Leaderboard! To add a new model, please follow these steps:

1. **Review the Base Handler:**

   - Look at `bfcl/model_handler/base_handler.py`. This is the base handler object from which all handlers inherit.
   - Feel free to examine the existing model handlers; you can likely reuse some of the existing code if your new model outputs in a similar format.
     - If your model is OpenAI-compatible, the `OpenAI` handler might be helpful.
     - If your model is hosted locally, `bfcl/model_handler/oss_model/base_oss_handler.py` is a good starting point.

2. **Create Your Handler and Define the Following Functions:**

   1. `__init__`: Initialize the model object with the necessary parameters.
   2. **Define Necessary Methods:**
      - **For API Endpoint Models:**
        - Implement all the non-implemented methods under the `FC Methods` or `Prompting Methods` sections in the `base_handler.py` file, depending on whether your model is a Function Calling model or a Prompt model.
      - **For Locally Hosted Models:**
        - You only need to define the `_format_prompt` method.
        - All other methods under the `Prompting Methods` section in the `base_oss_handler.py` file have been implemented for you, but you can override them if necessary.
   3. `decode_ast`: Convert the raw model response to the format `[{func1:{param1:val1,...}},{func2:{param2:val2,...}}]`; i.e., a list of dictionaries, each representing a function call with the function name as the key and the parameters as the value. This is the format that the evaluation pipeline expects.
   4. `decode_execute`: Convert the raw model response to the format `["func1(param1=val1)", "func2(param2=val2)"]`; i.e., a list of strings, each representing an executable function call.

3. **Update the Handler Map and Model Metadata:**

   - Modify `bfcl/model_handler/handler_map.py`. This is a mapping of the model name to their handler class.
   - Modify `bfcl/val_checker/model_metadata.py`:
     - Update the `MODEL_METADATA_MAPPING` with the model's display name, URL, license, and company information. The key should match the one in `bfcl/model_handler/handler_map.py`.
     - If your model is price-based, update the `INPUT_PRICE_PER_MILLION_TOKEN` and `OUTPUT_PRICE_PER_MILLION_TOKEN`.
     - If your model doesn't have a cost, add it to the `NO_COST_MODELS` list.
     - If your model is open-source and hosted locally, update the `OSS_LATENCY` list with the latency for the entire batch of data generation. This information will affect the cost calculation.

4. **Submit a Pull Request:**

   - Raise a [Pull Request](https://github.com/ShishirPatil/gorilla/pulls) with your new Model Handler.
   - Note that any model on the leaderboard must be publicly accessible—either open-source or with an API endpoint available for inference. While you can require registration, login, or tokens, the general public should ultimately be able to access the endpoint.

5. **Join Our Community:**
   - Feel free to join the [Gorilla Discord](https://discord.gg/grXXvj9Whz) `#leaderboard` channel and reach out to us with any questions or concerns about adding new models. We are happy to help you!

All the leaderboard statistics, and data used to train the models are released under Apache 2.0.
Gorilla is an open source effort from UC Berkeley and we welcome contributors.
Please email us your comments, criticisms, and questions. More information about the project can be found at [https://gorilla.cs.berkeley.edu/](https://gorilla.cs.berkeley.edu/)
