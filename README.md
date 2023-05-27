# Gorilla: Large Language Model Connected with Massive APIs
By Shishir G. Patil, Tianjun Zhang, Xin Wang, and Joseph E. Gonzalez  ([Project Website](https://shishirpatil.github.io/gorilla/))

<img src="https://github.com/ShishirPatil/gorilla/blob/gh-pages/assets/img/logo.png" width=50% height=50%>

_See the paper!_ [https://arxiv.org/abs/2305.15334](https://arxiv.org/abs/2305.15334)

_Join our Discord!_ [https://discord.gg/3apqwwME](https://discord.gg/3apqwwME) 

`Gorilla` enables LLMs to use tools by invoking APIs. Given a natural language query, Gorilla comes up with the semantically- and syntactically- correct API to invoke. With Gorilla, we are the first to demonstrate how to use LLMs to invoke 1,600+ (and growing) API calls accurately while reducing hallucination. Join us, as we try to build the API store for LLMs! Hop on our Discord, or open a PR, or email us if you would like to have your API incorporated as well.

## News
- :fire: [05/25] We release the APIBench dataset and the evaluation code of Gorilla!

## Content
- [Repository Organization](##Repository-Organization)
- [Contributing Your API](##Contributing-Your-API)
- [Evaluation](https://github.com/ShishirPatil/gorilla/tree/main/eval)
- [FAQ(s)](##FAQ(s))
- [Project Roadmap](##PROJECT-ROADMAP)


## Get Started 

### Install Dependencies

Use the following command to install dependencies: 

```bash
conda create -n gorilla python=3.8
conda activate gorilla
pip install -r requirements.txt
```

We have included prompts and responces for the APIBench with and without retrievers along with the Abstract Syntax Tree (AST) matching evaluation script at [evaluation](https://github.com/ShishirPatil/gorilla/tree/main/eval).

## Repository Organization

Our repository organization is shown below. 

  - The `data` folder contains all the evaluation APIs `(APIBench)` and the community contributed APIs.
  - The `eval` folder contains all our evaluation code as well as the Gorilla outputs.
  - <span style="color:hr">[Coming Soon!]</span>  The `inference` folder contains all the inference code associated with running Gorilla locally.
  - <span style="color:hr">[Coming Soon!]</span>  The `train` folder contains all the training code associated with Gorilla finetuning.


For our dataset collections, all the 1640 API documentation is in `data/api`. We also include the `APIBench` dataset created by self-instruct in `data/apibench`. For evaluation, we convert this into a LLM-friendly chat format, and the questions are in `eval/eval-data/questions`, and the corresponding responces are in `eval/eval-data/responses`.  We have also included the evaluation scripts are in `eval/eval-scripts`. This would be entirely sufficient to train Gorilla yourself, and reproduce our results. Please see [evaluation](https://github.com/ShishirPatil/gorilla/tree/main/eval) for the details on how to use our evaluation pipeline.

Additionally, to make it more accessible, we will also release the model weights soon, and a hosted Gorilla chat completion API! Eitherways, if you run into any issues please feel free to reach out to us either through Discord or email or raise a Github issue.

```
gorilla
├── data
│   ├── api (TF/HF/TH APIs used in generating apibench)
│   │   ├── {api_name}_api.jsonl
│   ├── apibench (Evaluating LLM models) v-0.1
│   │   ├── {api_name}_train.jsonl, {api_name}_eval.jsonl
|   |── apizoo (Contributed by the community - evolving)
│   |   ├── username1.json
│   │   ├── username2.json
│   │   ├── username3.json
│   │   ├── ...
├── eval
│   ├── README.md
│   ├── get_llm_responses.py
│   ├── eval-scripts
│   │   ├── ast_eval_{api_name}.py
│   ├── eval-data
│   │   ├── questions
│   │   │   ├── API name
│   │   │   │   ├── questions_{api_name}_{eval_metric}.jsonl
│   │   ├── responses
│   │   │   ├── API name
│   │   │   │   ├── responses_{api_name}_Gorilla_FT_{eval_metric}.jsonl
│   │   │   │   ├── responses_{api_name}_Gorilla_RT_{eval_metric}.jsonl
├── inference (Coming Soon!)
├── train (Coming Soon!)

```

## Contributing Your API
We aim to build an open-source, one-stop-shop for all APIs, LLMs can interact with! Any suggestions and contributions are welcome! Please see the details on [how to contribute](https://github.com/ShishirPatil/gorilla/tree/main/data/README.md). THIS WILL ALWAYS REMAIN OPEN SOURCE.


## FAQ(s)

Can we use Gorilla with Langchain, Toolformer, AutoGPT etc?

Absolutely! You've highlighted a great aspect of our tools. Gorilla is  an  end-to-end model, specifically tailored to serve correct API calls without requiring any additional coding. It's designed to work as part of a wider ecosystem and can be flexibly integrated with other tools.

Langchain, is a versatile developer tool. Its "agents" can efficiently swap in any LLM, Gorilla included, making it a highly adaptable solution for various needs.

AutoGPT, on the other hand, concentrates on the art of prompting GPT series models. It's worth noting that Gorilla, as a fully fine-tuned model, consistently shows remarkable accuracy, and lowers hallucination, outperforming GPT-4 in making specific API calls.

Now, when it comes to ToolFormer, Toolformer zeroes in on a select set of tools, providing specialized functionalities. Gorilla, in contrast, has the capacity to manage thousands of API calls, offering a broader coverage over a more extensive range of tools.

The beauty of these tools truly shines when they collaborate, complementing each other's strengths and capabilities to create an even more powerful and comprehensive solution. This is where your contribution can make a difference. We enthusiastically welcome any inputs to further refine and enhance these tools. 


## Project Roadmap

- [X] Dataset and Eval Code
- [X] Opening up the API Zoo for contributions from community
- [] Hosted Gorilla LLM chat for HF model APIs [May 27, 2023]
- [] Release weights for HF model APIs [May 27, 2023]
- [] Run Gorilla LLM locally [May 27, 2023]
- [] Release weights for all APIs from APIBench [May 28, 2023]
- [] Train a model with first batch of community contributed APIs from API Zoo [May 30, 2023]
- [] Release training code [May 31, 2023]

Propose a new task you would like to work on :star_struck:

## Citation
```text
@article{patil2023gorilla,
  title={Gorilla: Large Language Model Connected with Massive APIs},
  author={Shishir G. Patil and Tianjun Zhang and Xin Wang and Joseph E. Gonzalez},
  year={2023},
  journal={arXiv preprint arXiv:2305.15334},
} 
```




