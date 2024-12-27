# Gorilla: Large Language Model Connected with Massive APIs

<div align="center">
  <img src="https://github.com/ShishirPatil/gorilla/blob/gh-pages/assets/img/logo.png" width="50%" height="50%">
</div>

<div align="center">
  
[![Arxiv](https://img.shields.io/badge/Gorilla_Paper-2305.15334-<COLOR>.svg?style=flat-square)](https://arxiv.org/abs/2305.15334) [![Discord](https://img.shields.io/discord/1111172801899012102?label=Discord&logo=discord&logoColor=green&style=flat-square)](https://discord.gg/grXXvj9Whz) [![Gorilla Blog](https://img.shields.io/badge/Blog-gorilla.cs.berkeley.edu-blue?style=flat-square)](https://gorilla.cs.berkeley.edu/blog.html) [![Hugging Face](https://img.shields.io/badge/🤗-gorilla--llm-yellow.svg?style=flat-square)](https://huggingface.co/gorilla-llm)

</div>

## Latest Updates

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


## About

**Gorilla enables LLMs to use tools by invoking APIs. Given a natural language query, Gorilla comes up with the semantically- and syntactically- correct API to invoke.** 

With Gorilla, we are the first to demonstrate how to use LLMs to invoke 1,600+ (and growing) API calls accurately while reducing hallucination. This repository contains [inference code](/gorilla/inference) for running Gorilla finetuned models, [evaluation code](/gorilla/eval) for reproducing results from our paper, and [APIBench](/data) - the largest collection of APIs, curated and easy to be trained on!

Since our initial release, we've served ~500k requests and witnessed incredible adoption by developers worldwide. The project has expanded to include tools, evaluations, leaderboard, end-to-end finetuning recipes, infrastructure components, and the Gorilla API Store:

| Project | Type | Description (click to expand) |
|---------|------|---------------------------|
| [Gorilla OpenFunctions-V2](openfunctions/) | 🤖 Model | <details><summary>Drop-in alternative for function calling, supporting multiple complex data types and parallel execution</summary>• Multiple & parallel function execution with OpenAI-compatible endpoints<br>• Support for Python, Java, JavaScript, and REST APIs<br>• Complex data type handling including lists, tuples, dicts<br>• State-of-the-art performance for open-source models</details> |
| [Berkeley Function Calling Leaderboard (BFCL)](berkeley-function-call-leaderboard/) | 📊 Evaluation<br>🏆 Leaderboard<br>🔧 Function Calling Infra<br>📚 Dataset | <details><summary>Comprehensive evaluation of function-calling capabilities</summary>• Real-time model comparisons with cost and latency metrics<br>• Interactive API explorer for testing and validation<br>• Standardized evaluation suite for function calling<br>• Community-driven benchmarking platform</details> |
| [Agent Arena](agent-arena/) | 📊 Evaluation<br>🏆 Leaderboard | <details><summary>Compare LLM agents across models, tools, and frameworks</summary>• Head-to-head agent comparisons with ELO rating system<br>• Framework compatibility testing (LangChain, AutoGPT)<br>• Community-driven evaluation platform<br>• Real-world task performance metrics</details> |
| [Gorilla Execution Engine (GoEx)](goex/) | 🔧 Infra | <details><summary>Runtime for executing LLM-generated actions with safety guarantees</summary>• Safe execution of LLM actions with rollback capabilities<br>• Multi-service authentication (Gmail, Slack, GitHub)<br>• Sandboxed execution environment<br>• Real-time monitoring and logging</details> |
| [Retrieval-Augmented Fine-tuning (RAFT)](raft/) | 📝 Fine-tuning<br>🤖 Model | <details><summary>Fine-tuning LLMs for robust domain-specific retrieval</summary>• Automated dataset generation from documents<br>• Domain-specific question-answer pair creation<br>• Support for multiple document types (PDF, JSON, TXT)<br>• Customizable retrieval augmentation</details> |
| [Gorilla CLI](https://github.com/gorilla-llm/gorilla-cli) | 🤖 Model<br>🔧 Local CLI Infra | <details><summary>LLMs for your command-line interface</summary>• Native CLI integration with local execution<br>• Multiple API support and command suggestions<br>• Easy installation and usage<br>• Secure local processing</details> |
| [Gorilla API Zoo](apizoo/) | 📚 Dataset | <details><summary>A community-maintained repository of up-to-date API documentation</summary>• 1,600+ curated APIs with version tracking<br>• Community contribution platform<br>• Training data generation capabilities<br>• Multiple framework support</details> |

## Getting Started

### Quick Start
Try Gorilla in your browser:
- 🚀 [Gorilla Demo](https://colab.research.google.com/drive/1DEBPsccVLF_aUnmD0FwPeHFrtdC0QIUP?usp=sharing): Try the base Gorilla model
- 🎯 [OpenFunctions Demo](https://gorilla.cs.berkeley.edu/leaderboard.html#api-explorer): Experiment with function calling
- 🌐 [Gradio Web UI](https://huggingface.co/spaces/gorilla-llm/gorilla-demo/): Interactive web interface
- 📊 [Berkeley Function Calling Leaderboard](https://gorilla.cs.berkeley.edu/leaderboard): Compare function calling capabilities

### Installation Options

1. **Gorilla CLI** - Fastest way to get started
```bash
pip install gorilla-cli
gorilla generate 100 random characters into a file called test.txt
```
[Learn more about Gorilla CLI →](https://github.com/gorilla-llm/gorilla-cli)

2. **Run Gorilla Locally**
```bash
git clone https://github.com/ShishirPatil/gorilla.git
cd gorilla/inference
```
[Detailed local setup instructions →](/gorilla/inference/README.md)

3. **Use OpenFunctions**
```python
import openai

openai.api_key = "EMPTY"
openai.api_base = "http://luigi.millennium.berkeley.edu:8000/v1"

# Define your functions
functions = [{
    "name": "get_current_weather",
    "description": "Get weather in a location",
    "parameters": {
        "type": "object",
        "properties": {
            "location": {"type": "string"},
            "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
        },
        "required": ["location"]
    }
}]

# Make API call
completion = openai.ChatCompletion.create(
    model="gorilla-openfunctions-v2",
    messages=[{"role": "user", "content": "What's the weather in San Francisco?"}],
    functions=functions
)
```
[OpenFunctions documentation →](/openfunctions/README.md)

<details>
<summary>🔧 Other Quick Starts</summary>

- 📊 **Evaluation & Benchmarking**
  - [Berkeley Function Calling Leaderboard](/berkeley-function-call-leaderboard/README.md): Compare function calling capabilities
  - [Agent Arena](/agent-arena/README.md): Evaluate agent workflows
  - [Gorilla Paper Evaluation Scripts](/gorilla/eval/README.md): Run your own evaluations

- 🛠️ **Development Tools**
  - [GoEx](/goex/README.md): Safe execution of LLM-generated actions
  - [RAFT](/raft/README.md): Fine-tune models for domain-specific tasks
  - [API Store](/data/README.md): Contribute and use APIs

</details>


## Frequently Asked Questions
Visit our [FAQ](docs/FAQ.md) for answers to common questions.

## Project Roadmap
View our [Roadmap](docs/ROADMAP.md) for upcoming features and milestones.

## License

Gorilla is Apache 2.0 licensed, making it suitable for both academic and commercial use.

## Contact

- 💬 Join our [Discord Community](https://discord.gg/grXXvj9Whz)
- 🐦 Follow us on [X](https://x.com/shishirpatil_)

## Citation

```text
@article{patil2023gorilla,
  title={Gorilla: Large Language Model Connected with Massive APIs},
  author={Shishir G. Patil and Tianjun Zhang and Xin Wang and Joseph E. Gonzalez},
  year={2023},
  journal={arXiv preprint arXiv:2305.15334},
} 
```
