# How to Add New Models

We welcome your contributions to the Leaderboard! This guide provides step-by-step instructions for adding a new model to the leaderboard.

- [How to Add New Models](#how-to-add-new-models)
  - [Repository Structure](#repository-structure)
  - [Where to Begin](#where-to-begin)
  - [Function Calling (FC) vs. Prompt Models](#function-calling-fc-vs-prompt-models)
  - [Creating Your Model Handler](#creating-your-model-handler)
  - [Updating the Handler Map and Model Metadata](#updating-the-handler-map-and-model-metadata)
  - [Submitting Your Pull Request](#submitting-your-pull-request)
  - [Join Our Community](#join-our-community)

## Repository Structure

The repository is organized as follows:

```plaintext
berkeley-function-call-leaderboard/
├── bfcl/
│   ├── eval_checker/             # Evaluation modules
│   │   ├── ast_eval/             # AST-based evaluation
│   │   ├── executable_eval/      # Evaluation by execution
│   │   ├── multi_turn_eval/      # Multi-turn evaluation
│   ├── model_handler/            # All model-specific handlers
│   │   ├── local_inference/            # Handlers for locally-hosted models
│   │   │   ├── base_oss_handler.py   # Base handler for OSS models
│   │   │   ├── llama_fc.py           # Example: LLaMA (FC mode)
│   │   │   ├── deepseek_coder.py     # Example: DeepSeek Coder
│   │   │   ├── ...
│   │   ├── api_inference/    # Handlers for API-based models
│   │   │   ├── openai.py             # Example: OpenAI models
│   │   │   ├── claude.py             # Example: Claude models
│   │   │   ├── ...
│   │   ├── parser/                # Parsing utilities for Java/JavaScript
│   │   ├── base_handler.py        # Base handler blueprint
│   │   ├── handler_map.py         # Maps model names to handler classes
├── data/                         # Datasets
├── result/                       # Model responses
├── score/                        # Evaluation results
├── utils/                        # Helper scripts
```

To add a new model, focus primarily on the `model_handler` directory. You do not need to modify the parsing utilities in `model_handler/parser` or any other directories.

## Where to Begin

- **Base Handler:** Start by reviewing `bfcl/model_handler/base_handler.py`. All model handlers inherit from this base class. The `inference_single_turn` and `inference_multi_turn` methods defined there are helpful for understanding the model response generation pipeline. The `base_handler.py` contains many useful details in the docstrings of each abstract method, so be sure to review them.
  - If your model is hosted locally, you should also look at `bfcl/model_handler/local_inference/base_oss_handler.py`.
- **Reference Handlers:** Checkout some of the existing model handlers (such as `openai.py`, `claude.py`, etc); you can likely reuse some of the existing code if your new model outputs in a similar format.
  - If your model is OpenAI-compatible, the `openai.py` handler will be helpful (and you might be able to just use it as is).
  - If your model is locally hosted, the `llama_fc.py` handler or the `deepseek_coder.py` handler can be good starting points.

## Function Calling (FC) vs. Prompt Models

We support models in two modes:

1. **Function Calling (FC) Mode:**  
   Models with native tool/function calling capabilities. For example, OpenAI GPT in FC mode uses the `tools` section as documented in the [OpenAI function calling guide](https://platform.openai.com/docs/guides/function-calling).

2. **Prompting Mode:**  
   Models without native function calling capabilities rely on traditional prompt-based interactions, and we supply the function definitions in the `system prompt` section as opposed to a dedicated `tools` section. Prompt mode also serve as an alternative approach for models that support FC mode but do not fully leverage its function calling ability (i.e., we only use its normal text generation capability).

For API-based models (such as OpenAI GPT), both FC and Prompting modes can be defined in the same handler. Methods related to FC mode end with `_FC`, while Prompting mode methods end with `_prompting`.

For locally-hosted models, we only implement prompting methods to maintain code readablity. If a locally-hosted model has both FC and Prompting modes, you will typically create two separate handlers (e.g., `llama_fc.py` for FC mode and `llama.py` for Prompting mode).

## Creating Your Model Handler

**For API-based Models:**

- Implement all the methods marked as "not implemented" under the `FC Methods` or `Prompting Methods` sections in `base_handler.py`, depending on which mode(s) your model supports.

**For Locally-Hosted Models:**

- Implement the `_format_prompt` method in your handler.
- Other methods from the `Prompting Methods` section in `base_oss_handler.py` are already implemented, but you may override them if necessary.

**Common Requirements for All Handlers:**  
Regardless of mode or model type, you should implement the following methods to convert raw model response (output of `_parse_query_response_xxx`) into standard formats expected by the evaluation pipeline:

1. **`decode_ast`**  
   Converts the raw model response into a structured list of dictionaries, with each dictionary representing a function call:

   ```python
   [{"func1": {"param1": "val1", "param2": "val2"}}, {"func2": {"param1": "val1"}}]
   ```

   This helps the evaluation pipeline understand the model’s intended function calls.

2. **`decode_execute`**  
   Converts the raw model response into a list of strings representing callable functions:

   ```python
   ["func1(param1=val1, param2=val2)", "func2(param1=val1)"]
   ```

## Updating the Handler Map and Model Metadata

1. **Update `model_handler/handler_map.py`:**  
   Add your new model’s handler class and associate it with the model’s name.

2. **Update `model_handler/model_metadata.py`:**  
   In `bfcl/eval_checker/model_metadata.py`, add entries in `MODEL_METADATA_MAPPING` to include:

   - Model display name (as shown in the leaderboard)
   - URL to the model’s documentation or homepage
   - License details
   - Company name

   If your model is API-based and has usage costs, update the following accordingly:

   - `INPUT_PRICE_PER_MILLION_TOKEN`
   - `OUTPUT_PRICE_PER_MILLION_TOKEN`

   If the model is API-based but free, add it to the `NO_COST_MODELS` list.

3. **Update `model_handler/constant.py`:**  
   If your model is a Function Calling model and it does not support `.` in the function name (such as GPT in FC mode), add the model name to the `UNDERSCORE_TO_DOT` list.

4. **Update `SUPPORTED_MODELS.md`:**  
   Add your model to the list of supported models. Include the model name and type (FC or Prompt) in the table.

## Submitting Your Pull Request

- Raise a [Pull Request](https://github.com/ShishirPatil/gorilla/pulls) with your new Model Handler and the necessary updates to the metadata.
- Ensure that the model you add is publicly accessible, either open-source or behind a publicly available API. While you may require authentication, billing, registration, or tokens, the general public should ultimately be able to access the endpoint.
  - If your model is not publicly accessible, we would still welcome your contribution, but we unfortunately cannot include it in the public-facing leaderboard.

## Join Our Community

- Have questions or need help? Join the [Gorilla Discord](https://discord.gg/grXXvj9Whz) and visit the `#leaderboard` channel.
- Feel free to reach out if you have any questions, concerns, or would like guidance while adding your new model. We’re happy to assist!

---

Thank you for contributing to the Berkeley Function Calling Leaderboard! We look forward to seeing your model added to the community.
