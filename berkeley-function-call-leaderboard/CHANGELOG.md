# Changelog

All notable changes to this project will be documented in this file.

* [July 3, 2024] [#489](https://github.com/ShishirPatil/gorilla/pull/489): Add new model `nvidia/nemotron-4-340b-instruct` to the leaderboard.
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
* [Mar 5, 2024] [#237](https://github.com/ShishirPatil/gorilla/pull/237) and [238](https://github.com/ShishirPatil/gorilla/pull/238): leaderboard update resulting from [#223](https://github.com/ShishirPatil/gorilla/pull/223); 3 new models: `mistral-large-2402`, `gemini-1.0-pro`, and `gemma`.
* [Feb 29, 2024] [#223](https://github.com/ShishirPatil/gorilla/pull/223): modifications to REST evaluation. 
