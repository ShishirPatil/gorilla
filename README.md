# Gorilla: Large Language Model Connected with Massive APIs

<div align="center">
  <img src="https://github.com/ShishirPatil/gorilla/blob/gh-pages/assets/img/logo.png" width="50%" height="50%">
</div>

<div align="center">
  
[![Arxiv](https://img.shields.io/badge/Gorilla_Paper-2305.15334-<COLOR>.svg?style=flat-square)](https://arxiv.org/abs/2305.15334) [![Discord](https://img.shields.io/discord/1111172801899012102?label=Discord&logo=discord&logoColor=green&style=flat-square)](https://discord.gg/grXXvj9Whz) [![Gorilla Website](https://img.shields.io/badge/Website-gorilla.cs.berkeley.edu-blue?style=flat-square)](https://gorilla.cs.berkeley.edu/) [![Gorilla Blog](https://img.shields.io/badge/Blog-gorilla.cs.berkeley.edu/blog.html-blue?style=flat-square)](https://gorilla.cs.berkeley.edu/blog.html) [![Hugging Face](https://img.shields.io/badge/🤗-gorilla--llm-yellow.svg?style=flat-square)](https://huggingface.co/gorilla-llm)

</div>

## Latest Updates
> 📢 Check out our detailed [Berkeley Function Calling Leaderboard changelog](/berkeley-function-call-leaderboard/CHANGELOG.md) (Last updated: ![Last Updated](https://img.shields.io/github/last-commit/ShishirPatil/gorilla?path=berkeley-function-call-leaderboard/CHANGELOG.md)) for the latest dataset / model updates to the Berkeley Function Calling Leaderboard!


- 🤖 [07/17/2025] Announcing BFCL V4 Agentic! As function-calling forms the bedrock of Agentic systems, BFCL V4 Agentic benchmark focuses on tool-calling in real-world agentic settings, featuring web search with multi-hop reasoning and error recovery, agent memory management, and format sensitivity evaluation. [[Web-search Blog](https://gorilla.cs.berkeley.edu/blogs/15_bfcl_v4_web_search.html)] [[Memory Blog](https://gorilla.cs.berkeley.edu/blogs/16_bfcl_v4_memory.html)] [[Format Sensitivity Blog](https://gorilla.cs.berkeley.edu/blogs/17_bfcl_v4_prompt_variation.html)] [[PR](https://github.com/ShishirPatil/gorilla/pull/1019)] [[Tweet](https://x.com/shishirpatil_/status/1946020561626546176)]

- 🎯 [10/04/2024] Introducing the Agent Arena by Gorilla X LMSYS Chatbot Arena! Compare different agents in tasks like search, finance, RAG, and beyond. Explore which models and tools work best for specific tasks through our novel ranking system and community-driven prompt hub. [[Blog](https://gorilla.cs.berkeley.edu/blogs/14_agent_arena.html)] [[Arena](http://agent-arena.com)] [[Leaderboard](http://agent-arena.com/leaderboard)] [[Dataset](https://github.com/ShishirPatil/gorilla/tree/main/agent-arena#evaluation-directory)] [[Tweet](https://x.com/shishirpatil_/status/1841876885757977044)]

- 📣 [09/21/2024] Announcing BFCL V3 - Evaluating multi-turn and multi-step function calling capabilities! New state-based evaluation system tests models on handling complex workflows, sequential functions, and service states. [[Blog](https://gorilla.cs.berkeley.edu/blogs/13_bfcl_v3_multi_turn.html)] [[Leaderboard](https://gorilla.cs.berkeley.edu/leaderboard.html)] [[Code](https://github.com/ShishirPatil/gorilla/tree/main/berkeley-function-call-leaderboard)] [[Tweet](https://x.com/shishirpatil_/status/1837205152132153803)]

- 🚀 [08/20/2024] Released BFCL V2 • Live! The Berkeley Function-Calling Leaderboard now features enterprise-contributed data and real-world scenarios. [[Blog](https://gorilla.cs.berkeley.edu/blogs/12_bfcl_v2_live.html)] [[Live Leaderboard](https://gorilla.cs.berkeley.edu/leaderboard_live.html)] [[V2 Categories Leaderboard](https://gorilla.cs.berkeley.edu/leaderboard.html)] [[Tweet](https://x.com/shishirpatil_/status/1825577931697233999)]

- ⚡️ [04/12/2024] Excited to release GoEx - a runtime for LLM-generated actions like code, API calls, and more. Featuring "post-facto validation" for assessing LLM actions after execution, "undo" and "damage confinement" abstractions to manage unintended actions & risks. This paves the way for fully autonomous LLM agents, enhancing interaction between apps & services with human-out-of-loop. [[Blog](https://gorilla.cs.berkeley.edu/blogs/10_gorilla_exec_engine.html)] [[Code](https://github.com/ShishirPatil/gorilla/tree/main/goex)] [[Paper](https://arxiv.org/abs/2404.06921)] [[Tweet](https://x.com/shishirpatil_/status/1778485140257452375)]

- ⏰ [04/01/2024] Introducing cost and latency metrics into [Berkeley function calling leaderboard](https://gorilla.cs.berkeley.edu/leaderboard)!
- :rocket: [03/15/2024] RAFT: Adapting Language Model to Domain Specific RAG is live! [[MSFT-Meta blog](https://techcommunity.microsoft.com/t5/ai-ai-platform-blog/bg-p/AIPlatformBlog)] [[Berkeley Blog](https://gorilla.cs.berkeley.edu/blogs/9_raft.html)]
- :trophy: [02/26/2024] [Berkeley Function Calling Leaderboard](https://gorilla.cs.berkeley.edu/leaderboard) is live!
- :dart: [02/25/2024] [OpenFunctions v2](https://gorilla.cs.berkeley.edu/blogs/7_open_functions_v2.html) sets new SoTA for open-source LLMs!
- :fire: [11/16/2023] Excited to release [Gorilla OpenFunctions](https://gorilla.cs.berkeley.edu/blogs/4_open_functions.html)
- 💻 [06/29/2023] Released [gorilla-cli](https://github.com/gorilla-llm/gorilla-cli), LLMs for your CLI!
- 🟢 [06/06/2023] Released Commercially usable, Apache 2.0 licensed Gorilla models
- :rocket: [05/30/2023] Provided the [CLI interface](inference/README.md) to chat with Gorilla!
- :rocket: [05/28/2023] Released Torch Hub and TensorFlow Hub Models!
- :rocket: [05/27/2023] Released the first Gorilla model! [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1y78Zj7xHysX0xMpr9S468HYs12Mj6X1F?usp=sharing) or [:hugs:](https://huggingface.co/gorilla-llm/gorilla-7b-hf-delta-v0)!
- :fire: [05/27/2023] We released the APIZoo contribution guide for community API contributions!
- :fire: [05/25/2023] We release the APIBench dataset and the evaluation code of Gorilla!


## About

**Gorilla enables LLMs to use tools by invoking APIs. Given a natural language query, Gorilla comes up with the semantically- and syntactically- correct API to invoke.** 

With Gorilla, we are the first to demonstrate how to use LLMs to invoke 1,600+ (and growing) API calls accurately while reducing hallucination. This repository contains [inference code](/gorilla/inference) for running Gorilla finetuned models, [evaluation code](/gorilla/eval) for reproducing results from our paper, and [APIBench](/data) - the largest collection of APIs, curated and easy to be trained on!

Since our initial release, we've served ~500k requests and witnessed incredible adoption by developers worldwide. The project has expanded to include tools, evaluations, leaderboard, end-to-end finetuning recipes, infrastructure components, and the Gorilla API Store:

| Project | Type | Description (click to expand) |
|---------|------|---------------------------|
| [Gorilla Paper](https://arxiv.org/abs/2305.15334) | 🤖 Model<br>📝 Fine-tuning<br>📚 Dataset<br>📊 Evaluation<br>🔧 Infra | <details><summary>Large Language Model Connected with Massive APIs</summary>• Novel finetuning approach for API invocation<br>• Evaluation on 1,600+ APIs (APIBench)<br>• Retrieval-augmented training for test-time adaptation |
| [Gorilla OpenFunctions-V2](openfunctions/) | 🤖 Model | <details><summary>Drop-in alternative for function calling, supporting multiple complex data types and parallel execution</summary>• Multiple & parallel function execution with OpenAI-compatible endpoints<br>• Native support for Python, Java, JavaScript, and REST APIs with expanded data types<br>• Function relevance detection to reduce hallucinations<br>• Enhanced RESTful API formatting capabilities<br>• State-of-the-art performance among open-source models</details> |
| [Berkeley Function Calling Leaderboard (BFCL)](berkeley-function-call-leaderboard/) | 📊 Evaluation<br>🏆 Leaderboard<br>🔧 Function Calling Infra<br>📚 Dataset | <details><summary>Comprehensive evaluation of function-calling capabilities</summary>• V1: Expert-curated dataset for evaluating single-turn function calling<br>• V2: Enterprise-contributed data for real-world scenarios<br>• V3: Multi-turn & multi-step function calling evaluation<br>• Cost and latency metrics for all models<br>• Interactive API explorer for testing<br>• Community-driven benchmarking platform</details> |
| [Agent Arena](agent-arena/) | 📊 Evaluation<br>🏆 Leaderboard | <details><summary>Compare LLM agents across models, tools, and frameworks</summary>• Head-to-head agent comparisons with ELO rating system<br>• Framework compatibility testing (LangChain, AutoGPT)<br>• Community-driven evaluation platform<br>• Real-world task performance metrics</details> |
| [Gorilla Execution Engine (GoEx)](goex/) | 🔧 Infra | <details><summary>Runtime for executing LLM-generated actions with safety guarantees</summary>• Post-facto validation for verifying LLM actions after execution<br>• Undo capabilities and damage confinement for risk mitigation<br>• OAuth2 and API key authentication for multiple services<br>• Support for RESTful APIs, databases, and filesystem operations<br>• Docker-based sandboxed execution environment</details> |
| [Retrieval-Augmented Fine-tuning (RAFT)](raft/) | 📝 Fine-tuning<br>🤖 Model | <details><summary>Fine-tuning LLMs for robust domain-specific retrieval</summary>• Novel fine-tuning recipe for domain-specific RAG<br>• Chain-of-thought answers with direct document quotes<br>• Training with oracle and distractor documents<br>• Improved performance on PubMed, HotpotQA, and Gorilla benchmarks<br>• Efficient adaptation of smaller models for domain QA</details> |
| [Gorilla CLI](https://github.com/gorilla-llm/gorilla-cli) | 🤖 Model<br>🔧 Local CLI Infra | <details><summary>LLMs for your command-line interface</summary>• User-friendly CLI tool supporting ~1500 APIs (Kubernetes, AWS, GCP, etc.)<br>• Natural language command generation with multi-LLM fusion<br>• Privacy-focused with explicit execution approval<br>• Command history and interactive selection interface</details> |
| [Gorilla API Zoo](apizoo/) | 📚 Dataset | <details><summary>A community-maintained repository of up-to-date API documentation</summary>• Centralized, searchable index of APIs across domains<br>• Structured documentation format with arguments, versioning, and examples<br>• Community-driven updates to keep pace with API changes<br>• Rich data source for model training and fine-tuning<br>• Enables retrieval-augmented training and inference<br>• Reduces hallucination through up-to-date documentation</details> |

## Getting Started

### Quick Start
Try Gorilla in your browser:
- 🚀 [Gorilla Colab Demo](https://colab.research.google.com/drive/1y78Zj7xHysX0xMpr9S468HYs12Mj6X1F?usp=sharing): Try the base Gorilla model
- 🌐 [Gorilla Gradio Demo](https://huggingface.co/spaces/gorilla-llm/gorilla-demo/): Interactive web interface
- 🔥 [OpenFunctions Colab Demo](https://colab.research.google.com/drive/1Td3_R5vPael9PnKYHcl-PxmZkZzA9TCo?usp=sharing): Try the latest OpenFunctions model
- 🎯 [OpenFunctions Website Demo](https://gorilla.cs.berkeley.edu/leaderboard.html#api-explorer): Experiment with function calling
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

### 🔧 Other Quick Starts

- 📊 **Evaluation & Benchmarking**
  - [Berkeley Function Calling Leaderboard](/berkeley-function-call-leaderboard/README.md): Compare function calling capabilities
  - [Agent Arena](/agent-arena/README.md): Evaluate agent workflows
  - [Gorilla Paper Evaluation Scripts](/gorilla/eval/README.md): Run your own evaluations

- 🛠️ **Development Tools**
  - [GoEx](/goex/README.md): Safe execution of LLM-generated actions
  - [RAFT](/raft/README.md): Fine-tune models for domain-specific tasks
  - [API Store](/data/README.md): Contribute and use APIs


## Frequently Asked Questions
1. I would like to use Gorilla commercially. Is there going to be an Apache 2.0 licensed version?

Yes! We now have models that you can use commercially without any obligations.


2. Can we use Gorilla with other tools like Langchain etc?

Absolutely! You've highlighted a great aspect of our tools. Gorilla is  an  end-to-end model, specifically tailored to serve correct API calls (tools) without requiring any additional coding. It's designed to work as part of a wider ecosystem and can be flexibly integrated within agentic frameworks and other tools.

Langchain, is a versatile developer tool. Its "agents" can efficiently swap in any LLM, Gorilla included, making it a highly adaptable solution for various needs.

The beauty of these tools truly shines when they collaborate, complementing each other's strengths and capabilities to create an even more powerful and comprehensive solution. This is where your contribution can make a difference. We enthusiastically welcome any inputs to further refine and enhance these tools. 

Check out our blog on [How to Use Gorilla: A Step-by-Step Walkthrough](https://gorilla.cs.berkeley.edu/blogs/5_how_to_gorilla.html) to see all the different ways you can integrate Gorilla in your projects.

## Project Roadmap
In the immediate future, we plan to release the following:

- [ ] Multimodal function-calling leaderboard
- [ ] Agentic function-calling leaderboard
- [ ] New batch of user contributed live function calling evals. 
- [ ] BFCL metrics to evaluate contamination
- [ ] Openfunctions-v3 model to support more languages and multi-turn capability
- [x] Agent Arena to compare LLM agents across models, tools, and frameworks [10/04/2024]
- [x] Multi-turn and multi-step function calling evaluation [09/21/2024]
- [x] User contributed Live Function Calling Leaderboard [08/20/2024]
- [x] BFCL systems metrics including cost and latency [04/01/2024]
- [x] Gorilla Execution Engine (GoEx) - Runtime for executing LLM-generated actions with safety guarantees [04/12/2024]
- [x] Berkeley Function Calling leaderboard (BFCL) for evaluating tool-calling/function-calling models [02/26/2024]
- [x] Openfunctions-v2 with more languages (Java, JS, Python), relevance detection [02/26/2024]
- [x] API Zoo Index for easy access to all APIs [02/16/2024]
- [x] Openfunctions-v1, Apache 2.0, with parallel and multiple function calling [11/16/2023]
- [x] Openfunctions-v0, Apache 2.0 function calling model [11/16/2023]
- [X] Release a commercially usable, Apache 2.0 licensed Gorilla model [06/05/2023] 
- [X] Release weights for all APIs from APIBench [05/28/2023]
- [X] Run Gorilla LLM locally [05/28/2023]
- [X] Release weights for HF model APIs [05/27/2023]
- [X] Hosted Gorilla LLM chat for HF model APIs [05/27/2023]
- [X] Opening up the APIZoo for contributions from community
- [X] Dataset and Eval Code

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
