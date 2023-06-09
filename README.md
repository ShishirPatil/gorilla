# Gorilla: Large Language Model Connected with Massive APIs [[Project Website](https://shishirpatil.github.io/gorilla/)]


<img src="https://github.com/ShishirPatil/gorilla/blob/gh-pages/assets/img/logo.png" width=50% height=50%>

**🟢 Gorilla is Apache 2.0** With Gorilla being fine-tuned on MPT, and Falcon, you can use Gorilla commercially with no obligations! :golf:  

**:rocket: Try Gorilla in 60s** [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1DEBPsccVLF_aUnmD0FwPeHFrtdC0QIUP?usp=sharing)

**:newspaper_roll: Checkout our paper!** [![arXiv](https://img.shields.io/badge/arXiv-2305.15334-<COLOR>.svg?style=flat-square)](https://arxiv.org/abs/2305.15334)

**:wave: Join our Discord!** [![Discord](https://img.shields.io/discord/1111172801899012102?label=Discord&logo=discord&logoColor=green&style=flat-square)](https://discord.gg/SwTyuTAxX3)


`Gorilla` enables LLMs to use tools by invoking APIs. Given a natural language query, Gorilla comes up with the semantically- and syntactically- correct API to invoke. With Gorilla, we are the first to demonstrate how to use LLMs to invoke 1,600+ (and growing) API calls accurately while reducing hallucination. We also release APIBench, the largest collection of APIs, curated and easy to be trained on! Join us, as we try to expand the largest API store and teach LLMs how to write them! Hop on our Discord, or open a PR, or email us if you would like to have your API incorporated as well.

## News
- 🟢 [06/06] Released Commercially usable, Apache 2.0 licensed Gorilla models
- :rocket: [05/30] Provided the [CLI interface](inference/README.md) to chat with Gorilla!
- :rocket: [05/28] Released Torch Hub and TensorFlow Hub Models!
- :rocket: [05/27] Released the first Gorilla model! [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1DEBPsccVLF_aUnmD0FwPeHFrtdC0QIUP?usp=sharing) and [:hugs:](https://huggingface.co/gorilla-llm/gorilla-7b-hf-delta-v0)!
- :fire: [05/27] We released the APIZoo contribution guide for community API contributions!
- :fire: [05/25] We release the APIBench dataset and the evaluation code of Gorilla!

## Get Started 

Inference: Run Gorilla locally [`inference/README.md`](inference/README.md)

Evaluation: We have included prompts and responces for the APIBench with and without retrievers along with the Abstract Syntax Tree (AST) matching evaluation script at [evaluation](https://github.com/ShishirPatil/gorilla/tree/main/eval).

## Repository Organization

Our repository organization is shown below. 

  - The `data` folder contains all the evaluation APIs `(APIBench)` and the community contributed APIs.
  - The `eval` folder contains all our evaluation code as well as the Gorilla outputs.
  - The `inference` folder contains all the inference code for running Gorilla locally.
  - <span style="color:hr">[Coming Soon!]</span>  The `train` folder contains all the training code associated with Gorilla finetuning.


For our dataset collections, all the 1640 API documentation is in `data/api`. We also include the `APIBench` dataset created by self-instruct in `data/apibench`. For evaluation, we convert this into a LLM-friendly chat format, and the questions are in `eval/eval-data/questions`, and the corresponding responces are in `eval/eval-data/responses`.  We have also included the evaluation scripts are in `eval/eval-scripts`. This would be entirely sufficient to train Gorilla yourself, and reproduce our results. Please see [evaluation](https://github.com/ShishirPatil/gorilla/tree/main/eval) for the details on how to use our evaluation pipeline.

Additionally, we have released all the model weights. `gorilla-7b-hf-v0` lets you invoke over 925 Hugging Face APIs. Similarly, `gorilla-7b-tf-v0` and `gorilla-7b-th-v0` have 626 (exhaustive) Tensorflow v2, and 94 (exhaustive) Torch Hub APIs. `gorilla-mpt-7b-hf-v0` and `gorilla-falcon-7b-hf-v0` are Apache 2.0 licensed models (commercially usable) fine-tuned on MPT-7B and Falcon-7B respectively. We will release a model with all three combined with generic chat capability and community contributed APIs as soon as we can scale our serving infrastructure. You can run Gorilla locally from instructions in the `inference/` sub-directory, or we also provide a hosted Gorilla chat completion API (see Colab)! If you have any suggestions, or if you run into any issues please feel free to reach out to us either through Discord or email or raise a Github issue.

```
gorilla
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
├── train (Coming Soon!)

```

## Contributing Your API
We aim to build an open-source, one-stop-shop for all APIs, LLMs can interact with! Any suggestions and contributions are welcome! Please see the details on [how to contribute](https://github.com/ShishirPatil/gorilla/tree/main/data/README.md). THIS WILL ALWAYS REMAIN OPEN SOURCE.


## FAQ(s)

1. I would like to use Gorilla commercially. Is there going to be a Apache 2.0 licensed version?

Yes! We now have models that you can use commercially without any obligations.


2. Can we use Gorilla with Langchain, Toolformer, AutoGPT etc?

Absolutely! You've highlighted a great aspect of our tools. Gorilla is  an  end-to-end model, specifically tailored to serve correct API calls without requiring any additional coding. It's designed to work as part of a wider ecosystem and can be flexibly integrated with other tools.

Langchain, is a versatile developer tool. Its "agents" can efficiently swap in any LLM, Gorilla included, making it a highly adaptable solution for various needs.

AutoGPT, on the other hand, concentrates on the art of prompting GPT series models. It's worth noting that Gorilla, as a fully fine-tuned model, consistently shows remarkable accuracy, and lowers hallucination, outperforming GPT-4 in making specific API calls.

Now, when it comes to ToolFormer, Toolformer zeroes in on a select set of tools, providing specialized functionalities. Gorilla, in contrast, has the capacity to manage thousands of API calls, offering a broader coverage over a more extensive range of tools.

The beauty of these tools truly shines when they collaborate, complementing each other's strengths and capabilities to create an even more powerful and comprehensive solution. This is where your contribution can make a difference. We enthusiastically welcome any inputs to further refine and enhance these tools. 

3. How to train your own Gorilla models? 

We will release the training code as soon as we can get GPUs to test and finalize the pipeline. Given the demand for our hosted end-points, we have dedicated all of our GPUs to serve the models. If you would like to help with resources get in touch!


## Project Roadmap

In the immediate future, we plan to release the following:

- [X] Dataset and Eval Code
- [X] Opening up the APIZoo for contributions from community
- [X] Hosted Gorilla LLM chat for HF model APIs [May 27, 2023]
- [X] Release weights for HF model APIs [May 27, 2023]
- [X] Run Gorilla LLM locally [May 28, 2023]
- [X] Release weights for all APIs from APIBench [May 28, 2023]
- [X] Release a commercially usable, Apache 2.0 licensed Gorilla model [Jun 5, 2023] 
- [ ] Train a model with first batch of community contributed APIs from APIZoo
- [ ] Release training code
- [ ] Train SOTA Gorilla LLM with expanded APIBench and APIZoo :rocket:

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
