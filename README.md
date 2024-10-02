# Gorilla: Large Language Model Connected with Massive APIs [[Project Website](https://shishirpatil.github.io/gorilla/)]


<img src="https://github.com/ShishirPatil/gorilla/blob/gh-pages/assets/img/logo.png" width=50% height=50%>

**🚒  GoEx: A Runtime for executing LLM generated actions like code & API calls** GoEx presents “undo” and “damage confinement” abstractions for mitigating the risk of unintended actions taken in LLM-powered systems. [Release blog](https://gorilla.cs.berkeley.edu/blogs/10_gorilla_exec_engine.html) [Paper](https://arxiv.org/abs/2404.06921).

**🎉 Berkeley Function Calling Leaderboard** How do models stack up for function calling? :dart: Releasing the [Berkeley Function Calling Leaderboard](https://gorilla.cs.berkeley.edu/leaderboard). Read more in our [Release Blog](https://gorilla.cs.berkeley.edu/blogs/8_berkeley_function_calling_leaderboard.html). 

**:trophy: Gorilla OpenFunctions v2** Sets new SoTA for open-source LLMs :muscle: On-par with GPT-4 :raised_hands: Supports more languages :ok_hand: [Blog](https://gorilla.cs.berkeley.edu/blogs/7_open_functions_v2.html). 

**:fire: Gorilla OpenFunctions** is a drop-in alternative for function calling! [Release Blog](https://gorilla.cs.berkeley.edu/blogs/4_open_functions.html)

**🟢 Gorilla is Apache 2.0** With Gorilla being fine-tuned on MPT, and Falcon, you can use Gorilla commercially with no obligations! :golf:  

**:rocket: Try Gorilla in 60s** 
- [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1DEBPsccVLF_aUnmD0FwPeHFrtdC0QIUP?usp=sharing)
- [🚅 LiteLLM Playground](https://litellm.ai/playground)

:computer: Use [Gorilla in your CLI](https://github.com/gorilla-llm/gorilla-cli) with `pip install gorilla-cli`

**:fax: Checkout our [blogs](https://gorilla.cs.berkeley.edu/blog.html) for all things tools-use/function-calling!** 

**:newspaper_roll: Checkout our paper!** [![arXiv](https://img.shields.io/badge/arXiv-2305.15334-<COLOR>.svg?style=flat-square)](https://arxiv.org/abs/2305.15334)

**:wave: Join our Discord!** [![Discord](https://img.shields.io/discord/1111172801899012102?label=Discord&logo=discord&logoColor=green&style=flat-square)](https://discord.gg/grXXvj9Whz)


`Gorilla` enables LLMs to use tools by invoking APIs. Given a natural language query, Gorilla comes up with the semantically- and syntactically- correct API to invoke. With Gorilla, we are the first to demonstrate how to use LLMs to invoke 1,600+ (and growing) API calls accurately while reducing hallucination. We also release APIBench, the largest collection of APIs, curated and easy to be trained on! Join us, as we try to expand the largest API store and teach LLMs how to write them! Hop on our Discord, or open a PR, or email us if you would like to have your API incorporated as well.

## News
- ⏰: [04/01] Introducing cost and latency metrics into [Berkeley function calling leaderboard](https://gorilla.cs.berkeley.edu/leaderboard)!
- :rocket: [03/15] RAFT: Adapting Language Model to Domain Specific RAG is live! [[MSFT-Meta blog](https://techcommunity.microsoft.com/t5/ai-ai-platform-blog/bg-p/AIPlatformBlog)] [[Berkeley Blog](https://gorilla.cs.berkeley.edu/blogs/9_raft.html)]
- :trophy: [02/26] [Berkeley Function Calling Leaderboard](https://gorilla.cs.berkeley.edu/leaderboard) is live!
- :dart: [02/25] [OpenFunctions v2](https://gorilla.cs.berkeley.edu/blogs/7_open_functions_v2.html) sets new SoTA for open-source LLMs!
- :fire: [11/16] Excited to release [Gorilla OpenFunctions](https://gorilla.cs.berkeley.edu/blogs/4_open_functions.html)
- 💻 [06/29] Released [gorilla-cli](https://github.com/gorilla-llm/gorilla-cli), LLMs for your CLI!
- 🟢 [06/06] Released Commercially usable, Apache 2.0 licensed Gorilla models
- :rocket: [05/30] Provided the [CLI interface](inference/README.md) to chat with Gorilla!
- :rocket: [05/28] Released Torch Hub and TensorFlow Hub Models!
- :rocket: [05/27] Released the first Gorilla model! [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1DEBPsccVLF_aUnmD0FwPeHFrtdC0QIUP?usp=sharing) or [:hugs:](https://huggingface.co/gorilla-llm/gorilla-7b-hf-delta-v0)!
- :fire: [05/27] We released the APIZoo contribution guide for community API contributions!
- :fire: [05/25] We release the APIBench dataset and the evaluation code of Gorilla!

## Gorilla Gradio
**Try Gorilla LLM models in [HF Spaces](https://huggingface.co/spaces/gorilla-llm/gorilla-demo/) or [![Gradio Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1ktnVWPJOgqTC9hLW8lJPVZszuIddMy7y?usp=sharing)**
![gorilla_webUI_2](https://github.com/TanmayDoesAI/gorilla/assets/85993243/f30645bf-6798-4bd2-ac6e-6943840ae095)


## Get Started 

Inference: Run Gorilla locally [`inference/README.md`](inference/README.md)

Evaluation: We have included prompts and responses for the APIBench with and without retrievers along with the Abstract Syntax Tree (AST) matching evaluation script at [evaluation](https://github.com/ShishirPatil/gorilla/tree/main/eval).

## Repository Organization

Our repository organization is shown below. 

  - The `berkeley-function-call-leaderboard` folder contains scripts for evaluating function-calling ability of models.
  - The `data` folder contains all the evaluation APIs `(APIBench)` and the community contributed APIs.
  - The `eval` folder contains all our evaluation code as well as the Gorilla outputs.
  - The `inference` folder contains all the inference code for running Gorilla locally.
  - The `openfunctions` folder contains the inference code for the OpenFunctions model(s).

For our dataset collections, all the 1640 API documentation is in `data/api`. We also include the `APIBench` dataset created by self-instruct in `data/apibench`. For evaluation, we convert this into a LLM-friendly chat format, and the questions are in `eval/eval-data/questions`, and the corresponding responses are in `eval/eval-data/responses`.  We have also included the evaluation scripts are in `eval/eval-scripts`. This would be entirely sufficient to train Gorilla yourself, and reproduce our results. Please see [evaluation](https://github.com/ShishirPatil/gorilla/tree/main/eval) for the details on how to use our evaluation pipeline.

Additionally, we have released all the model weights. `gorilla-7b-hf-v0` lets you invoke over 925 Hugging Face APIs. Similarly, `gorilla-7b-tf-v0` and `gorilla-7b-th-v0` have 626 (exhaustive) Tensorflow v2, and 94 (exhaustive) Torch Hub APIs. `gorilla-mpt-7b-hf-v0` and `gorilla-falcon-7b-hf-v0` are Apache 2.0 licensed models (commercially usable) fine-tuned on MPT-7B and Falcon-7B respectively. We will release a model with all three combined with generic chat capability and community contributed APIs as soon as we can scale our serving infrastructure. You can run Gorilla locally from instructions in the `inference/` sub-directory, or we also provide a hosted Gorilla chat completion API (see Colab)! If you have any suggestions, or if you run into any issues please feel free to reach out to us either through Discord or email or raise a Github issue.

```
gorilla
|-- berkeley-function-call-leaderboard (data and scripts to eval model's function-calling ability)
├── data
│   ├── api (TF/HF/TH APIs used in generating apibench)
│   │   ├── {api_name}_api.jsonl
│   ├── apibench (Evaluating LLM models) v-1.0
│   │   ├── {api_name}_train.jsonl, {api_name}_eval.jsonl
|   |── apizoo (Contributed by the community - evolving)
│   |   ├── username1.json
│   │   ├── username2.json
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
├── inference
│   ├── README.md
│   ├── serve
│   │   ├── gorilla_cli.py
│   │   ├── conv_template.py
├── openfunctions
|   ├── openfunctions-v1 (data and scripts for openfunctions-v0 and v1)
|   ├── utils (parsing script for openfunctions-v2)
|   ├── inference_* (openfunctions-v2 hosted/local inference code)

```

## Contributing Your API
We aim to build an open-source, one-stop-shop for all APIs, LLMs can interact with! Any suggestions and contributions are welcome! Please see the details on [how to contribute](https://github.com/ShishirPatil/gorilla/tree/main/data/README.md). THIS WILL ALWAYS REMAIN OPEN SOURCE.


## FAQ(s)

1. I would like to use Gorilla commercially. Is there going to be a Apache 2.0 licensed version?

Yes! We now have models that you can use commercially without any obligations.


2. Can we use Gorilla with other tools like Langchain etc?

Absolutely! You've highlighted a great aspect of our tools. Gorilla is  an  end-to-end model, specifically tailored to serve correct API calls (tools) without requiring any additional coding. It's designed to work as part of a wider ecosystem and can be flexibly integrated within agentic frameworks and other tools.

Langchain, is a versatile developer tool. Its "agents" can efficiently swap in any LLM, Gorilla included, making it a highly adaptable solution for various needs.

The beauty of these tools truly shines when they collaborate, complementing each other's strengths and capabilities to create an even more powerful and comprehensive solution. This is where your contribution can make a difference. We enthusiastically welcome any inputs to further refine and enhance these tools. 

Check out our blog on [How to Use Gorilla: A Step-by-Step Walkthrough](https://gorilla.cs.berkeley.edu/blogs/5_how_to_gorilla.html) to see all the different ways you can integrate Gorilla in your projects.



## Project Roadmap

In the immediate future, we plan to release the following:

- [ ] BFCL metrics to evaluate contamination 
- [ ] BFCL systems metrics including cost and latency
- [ ] BFCL update with "live" data and user-votes
- [ ] Openfunctions-v3 model to support more languages and multi-turn capability 
- [x] Berkeley Function Calling leaderboard (BFCL) for evaluating tool-calling/function-calling models [Feb 26, 2024]
- [x] Openfunctions-v2 with more languages (Java, JS, Python), relevance detection [Feb 26, 2024]
- [x] API Zoo Index for easy access to all APIs [Feb 16, 2024]
- [x] Openfunctions-v1, Apache 2.0, with parallel and multiple function calling [Nov 16, 2023]
- [x] Openfunctions-v0, Apache 2.0 function calling model [Nov 16, 2023]
- [X] Release a commercially usable, Apache 2.0 licensed Gorilla model [Jun 5, 2023] 
- [X] Release weights for all APIs from APIBench [May 28, 2023]
- [X] Run Gorilla LLM locally [May 28, 2023]
- [X] Release weights for HF model APIs [May 27, 2023]
- [X] Hosted Gorilla LLM chat for HF model APIs [May 27, 2023]
- [X] Opening up the APIZoo for contributions from community
- [X] Dataset and Eval Code

Propose a new task you would like to work on :star_struck:

## Citation

If you use Gorilla or APIBench, please cite our paper:

```text
@article{patil2023gorilla,
  title={Gorilla: Large Language Model Connected with Massive APIs},
  author={Shishir G. Patil and Tianjun Zhang and Xin Wang and Joseph E. Gonzalez},
  year={2023},
  journal={arXiv preprint arXiv:2305.15334},
} 
```
