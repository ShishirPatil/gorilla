# Gorilla: Large Language Model Connected with Massive APIs

<div align="center">
  <img src="https://github.com/ShishirPatil/gorilla/blob/gh-pages/assets/img/logo.png" width="50%" height="50%">
</div>

<div align="center">
  
[![Arxiv](https://img.shields.io/badge/Gorilla_Paper-2305.15334-<COLOR>.svg?style=flat-square)](https://arxiv.org/abs/2305.15334) [![Discord](https://img.shields.io/discord/1111172801899012102?label=Discord&logo=discord&logoColor=green&style=flat-square)](https://discord.gg/grXXvj9Whz) [![Gorilla Blog](https://img.shields.io/badge/Blog-gorilla.cs.berkeley.edu-blue?style=flat-square)](https://gorilla.cs.berkeley.edu/blog.html) [![Hugging Face](https://img.shields.io/badge/🤗-gorilla--llm-yellow.svg?style=flat-square)](https://huggingface.co/gorilla-llm)

</div>

## About

**Gorilla enables LLMs to use tools by invoking APIs. Given a natural language query, Gorilla comes up with the semantically- and syntactically- correct API to invoke.** 

With Gorilla, we are the first to demonstrate how to use LLMs to invoke 1,600+ (and growing) API calls accurately while reducing hallucination. We also release APIBench, the largest collection of APIs, curated and easy to be trained on! 

Since our initial release, we've served ~500k requests and witnessed incredible adoption by developers worldwide. The project has expanded to include tools, evaluations, leaderboard, end-to-end finetuning recipes, infrastructure components, and the Gorilla API Store:

| Project | Type | Description |
|---------|------|-------------|
| [Gorilla OpenFunctions-V2](openfunctions/) | 🤖 Model | Drop-in alternative for function calling, supporting multiple complex data types and parallel execution |
| [Berkeley Function Calling Leaderboard (BFCL)](berkeley-function-call-leaderboard/) | 📊 Evaluation<br>🏆 Leaderboard<br>🔧 Function Calling Infra<br>📚 Dataset | Comprehensive evaluation of function-calling capabilities |
| [Agent Arena](agent-arena/) | 📊 Evaluation<br>🏆 Leaderboard | Compare LLM agents across models, tools, and frameworks |
| [Gorilla Execution Engine (GoEx)](goex/) | 🔧 Human-in-the-loop Infra | Runtime for executing LLM-generated actions with safety guarantees |
| [Retrieval-Augmented Fine-tuning (RAFT)](raft/) | 📝 Fine-tuning<br>🤖 Model | Fine-tuning LLMs for robust domain-specific retrieval |
| [Gorilla CLI](https://github.com/gorilla-llm/gorilla-cli) | 🤖 Model<br>🔧 Local CLI Infra | LLMs for your command-line interface |
| [Gorilla API Store](apizoo/) | 📚 Dataset | A community-maintained repository of up-to-date API documentation enabling API discovery, model training, and retrieval-based inference |

## Getting Started

### Quick Start
Try Gorilla in 60 seconds: [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1DEBPsccVLF_aUnmD0FwPeHFrtdC0QIUP?usp=sharing)

### Installation Options

1. **CLI Tool**: Get started with command-line interactions
   ```bash
   pip install gorilla-cli
   ```

2. **Local Development**: Clone and run Gorilla locally
   ```bash
   git clone https://github.com/ShishirPatil/gorilla.git
   cd gorilla
   ```

### Explore Key Features

- 🔍 [Evaluate Models](gorilla/eval/): Run and compare different LLM models
- 🛠️ [Contribute APIs](data/): Add your APIs to the Gorilla ecosystem
- 🤖 [Try OpenFunctions](openfunctions/): Experiment with function calling capabilities
- 🔒 [Use GoEx](goex/): Execute LLM actions safely

## Latest Updates

- ⏰: [04/01] Introducing cost and latency metrics into [Berkeley function calling leaderboard](https://gorilla.cs.berkeley.edu/leaderboard)!
- :rocket: [03/15] RAFT: Adapting Language Model to Domain Specific RAG is live! [[MSFT-Meta blog](https://techcommunity.microsoft.com/t5/ai-ai-platform-blog/bg-p/AIPlatformBlog)] [[Berkeley Blog](https://gorilla.cs.berkeley.edu/blogs/9_raft.html)]
- :trophy: [02/26] [Berkeley Function Calling Leaderboard](https://gorilla.cs.berkeley.edu/leaderboard) is live!
- :dart: [02/25] [OpenFunctions v2](https://gorilla.cs.berkeley.edu/blogs/7_open_functions_v2.html) sets new SoTA for open-source LLMs!

<details>
<summary>Older Updates</summary>

- :fire: [11/16] Excited to release [Gorilla OpenFunctions](https://gorilla.cs.berkeley.edu/blogs/4_open_functions.html)
- 💻 [06/29] Released [gorilla-cli](https://github.com/gorilla-llm/gorilla-cli), LLMs for your CLI!
- 🟢 [06/06] Released Commercially usable, Apache 2.0 licensed Gorilla models
- :rocket: [05/30] Provided the [CLI interface](inference/README.md) to chat with Gorilla!
- :rocket: [05/28] Released Torch Hub and TensorFlow Hub Models!
- :rocket: [05/27] Released the first Gorilla model! [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1DEBPsccVLF_aUnmD0FwPeHFrtdC0QIUP?usp=sharing) or [:hugs:](https://huggingface.co/gorilla-llm/gorilla-7b-hf-delta-v0)!
- :fire: [05/27] We released the APIZoo contribution guide for community API contributions!
- :fire: [05/25] We release the APIBench dataset and the evaluation code of Gorilla!

</details>

## Contact & Community

- 💬 Join our [Discord Community](https://discord.gg/grXXvj9Whz)
- 📧 Email us at [contact@gorilla.cs.berkeley.edu](mailto:contact@gorilla.cs.berkeley.edu)
- 🐦 Follow us on [Twitter](https://twitter.com/gorilla_llm)

### Example Questions?
- "How do I deploy a container to Kubernetes?"
- "Can you help me configure an AWS S3 bucket?"
- "What's the command to create a new GitHub repository?"

## License

Gorilla is Apache 2.0 licensed, making it suitable for both academic and commercial use.

## Citation

```text
@article{patil2023gorilla,
  title={Gorilla: Large Language Model Connected with Massive APIs},
  author={Shishir G. Patil and Tianjun Zhang and Xin Wang and Joseph E. Gonzalez},
  year={2023},
  journal={arXiv preprint arXiv:2305.15334},
} 
```
