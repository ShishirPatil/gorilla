# Berkeley Function Leaderboard

💡 Read more in our [Gorilla OpenFunctions Leaderboard](https://gorilla.cs.berkeley.edu/blogs/7_open_functions_v2.html)

## Introduction
We present Berkeley Function Leaderboard, the **first comprehensive and executable function calling evaluation for LLMs function calling**. Different from prior function calling evaluations (e.g. Anyscale function calling blog), we consider function callings of various forms, different function calling scenarios, and the executability of function calls. We also release our model Gorilla-Openfunctions-v2, the best open-source models so far to handle multiple languages of function calls, parallel function calls and multiple function calls. We also provide a specific debugging feature that when the provided function is not suitable for your task, the model will output an “Error Message”. 

Read more about the technical details and interesting insights in our blog post!

## Prepare Evaluation Dataset

To download the evaluation dataset from huggingface, from the current directory `./openfunctions/berkeley-function-call-leaderboard`, run the following command:

```bash
    cd berkeley-function-call-leaderboard
    huggingface-cli download gorilla-llm/Berkeley-Function-Calling-Leaderboard --local-dir ./data --repo-type dataset
```

This will download our dataset to `data` repository. 

## Execution Evaluation Data Post-processing 
Input your API keys into `function_credential_config.json`, so that the original placeholder values in questions, params, and answers will be cleaned. 

To run the executable test categories, there are 3 API keys to fill out:

1. RAPID-API Key: https://rapidapi.com/hub

    * Yahoo Finance: https://rapidapi.com/sparior/api/yahoo-finance15
    * Real Time Amazon Data : https://rapidapi.com/letscrape-6bRBa3QguO5/api/real-time-amazon-data
    * Urban Dictionary: https://rapidapi.com/community/api/urban-dictionary
    * Covid 19: https://rapidapi.com/api-sports/api/covid-193
    * Time zone by Location: https://rapidapi.com/BertoldVdb/api/timezone-by-location

    All the Rapid APIs we use have free tier usage. As a result, you need to subscribe to those API providers in order to have the executable test enviornment setup but it will be free of charge!

2. Exchange Rate API:https://www.exchangerate-api.com
3. OMDB API: http://www.omdbapi.com/apikey.aspx

The `apply_function_credential_config.py` inputs an input file, optionally an outputs file. If the output file is not given as an argument, it will overwrites your original file with the claned data.

```bash
    python apply_function_credential_config.py --input_file ./data/gorilla_openfunctions_v1_test_rest.json
```

Then, use `eval_data_compilation.py` to compile all files by using

```bash
    python eval_data_compilation.py
```
## Berkeley Function Leaderboard Statistics

To generate leaderboard statistics, there are two steps:

1. Inference the evaluation data and obtain the results from specific models 

```bash
    python openfunctions_evaluation.py --model MODEL_NAME --test_category TEST_CATEGORY --temperature 0.3
```
For TEST_CATEGORY, we have `executable_simple`, `executable_parallel_function`, `executable_multiple_function`, `executable_parallel_multiple_function`, `simple`, `relevance`, `parallel_function`, `multiple_function`, `parallel_multiple_function`, `java`, `javascript`, `rest`, `sql`, `chatable`.

If you want to run all evaluation at the same time, you can use `all` as the test category.

Running proprietary model like GPTs, Claude, Mistral-X will requires an API-Key which can be supplied in `openfunctions_evaluation.py`.

If decided to run OSS model, openfunctions evaluation uses vllm and therefore requires GPU for hosting and inferencing.

1. Check the accuracy of the evaluation result by our AST and Executable checks

```bash
    python openfunctions_checker.py --model MODEL_NAME --test_category {TEST_CATEGORY,all,ast,executable}
```

If you want to run the "all" or "executable" category, make sure to register your REST API keys in `function_credential_config.json`. This is because Gorilla Openfunctions Leaderboard want to test model's generated output on real world API! 

If you don't want to supply any API key, that's alright! Set `test_category` to `ast`. There, we are only doing the ast tree parsing and perform an exact match to derive the accuracy.

The output of this is in the format of 
```
Testing type: XXX, success rate: XXX
```

## Models Available
Below is a list of model we support to run our leaderboard evaluation against. If supported function calling, we will follow its function calling format provided by official documentations. Else, we will construct system message to prompt the model to generate function calls in the right format.
|Model | Function Calling |
|---|---|
|gorilla-openfunctions-v0 | Not supported|
|gorilla-openfunctions-v2 | Supported|
|gpt-*| Supported|
|glaiveai|  Supported| 
|Nexusflow-Raven-v2| Supported|
|FireFunction-v1 | Supported|
|mistral-large-latest | Supported|
|claude-*| Not supported|
|mistral-*| Not supported|
|deepseek-7b| Not supported|



## Contributing

All the leaderboard statistics, and data used to train the models is released under Apache 2.0.
Gorilla is an open source effort from UC Berkeley and we welcome contributors. 
Please email us your comments, criticism, and questions. More information about the project can be found at [https://gorilla.cs.berkeley.edu/](https://gorilla.cs.berkeley.edu/)

