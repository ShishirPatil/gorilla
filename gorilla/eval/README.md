# Gorilla

<img src="https://github.com/ShishirPatil/gorilla/blob/gh-pages/assets/img/logo.png" width=50% height=50%>

## Get Started

### Getting GPT-3.5-turbo, GPT-4 and Claude Responses (0-Shot)

To get LLM responses for the API calls, use the following command:

```bash
python get_llm_responses.py --model gpt-3.5-turbo --api_key $API_KEY --output_file gpt-3.5-turbo_torchhub_0_shot.jsonl --question_data eval-data/questions/torchhub/questions_torchhub_0_shot.jsonl --api_name torchhub
```

### Getting Responses with Retrievers (`bm25` or `gpt`)

```bash
python get_llm_responses_retriever.py --retriever bm25 --model gpt-3.5-turbo --api_key $API_KEY --output_file gpt-3.5-turbo_torchhub_0_shot.jsonl --question_data eval-data/questions/torchhub/questions_torchhub_0_shot.jsonl --api_name torchhub --api_dataset ../../data/api/torchhub_api.jsonl
```

### Evaluate the Response with AST tree matching

After the responses of the LLM is generated, we can start to evaluate the generated responses with respect to our dataset:

```bash 
cd eval-scripts
python ast_eval_th.py --api_dataset ../../../data/api/torchhub_api.jsonl --apibench ../../../data/apibench/torchhub_eval.json --llm_responses ../eval-data/responses/torchhub/response_torchhub_Gorilla_FT_0_shot.jsonl
```

### Checking APIBench Eval Data Drift

APIBench eval questions are represented in both `data/apibench/*_eval.json` and `gorilla/eval/eval-data/questions`.
To compare the duplicated question text and make drift visible before running benchmarks:

```bash
python gorilla/eval/check_apibench_eval_data.py
```

Use `--strict` when wiring the check into CI so any missing, extra, or mismatched question text exits non-zero:

```bash
python gorilla/eval/check_apibench_eval_data.py --strict
```

