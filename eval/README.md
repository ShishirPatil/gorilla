# Gorilla

![](https://github.com/ShishirPatil/gorilla/blob/gh-pages/assets/img/gorilla_method.png)

## Get Started

### Getting GPT-3.5-turbo, GPT-4 and Claude Responses

If you want to get LLM response for the API call, use the following command to get the responses:

```bash
python get_llm_responses.py --model gpt-3.5-turbo --api_key $API_KEY --output_file gpt-3.5-turbo_torchhub_0_shot.jsonl --question_data ../data/questions/questions_0_shot_torchhub.jsonl --api_name torchhub
```

### Evaluate the Response with AST tree matching

After the responses of the LLM is generated, we can start to evaluate the generated responses with respect to our dataset:

```bash 
cd eval-scripts
python ast_eval_th.py --api_dataset ../../data/api/torchhub_api.jsonl --apibench ../../data/apibench/torchhub_eval.json --llm_responses ../eval-data/responses/torchhub/response_torchhub_Gorilla_FT_0_shot.jsonl
```

## Citation

If you use Gorilla in your work, please cite us with:
```text
@article{patil2023gorilla,
  title={Gorilla: Large Language Model Connected with Massive APIs},
  author={Shishir G. Patil and Tianjun Zhang and Xin Wang and Joseph E. Gonzalez},
  year={2023},
  journal={arXiv preprint arXiv:2305.15334},
}
```
