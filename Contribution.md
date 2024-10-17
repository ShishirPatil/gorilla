# Contribution Guide for Gorilla API Store

Welcome to the **Gorilla API Store** contribution guide! We appreciate your interest in enhancing the capabilities of LLMs with API integration. This guide will help you contribute APIs to Gorilla and make sure your API is well-documented and functional within our ecosystem.

## Table of Contents

- [Introduction](#introduction)
- [Contribution Methods](#contribution-methods)
  - [Option 1: API JSON Contribution](#option-1-api-json-contribution-preferred)
  - [Option 2: URL JSON Contribution](#option-2-url-json-contribution)
- [Submission Process](#submission-process)
- [Contribution Format](#contribution-format)
  - [API JSON Format](#api-json-format)
  - [URL JSON Format](#url-json-format)
- [Example Submissions](#example-submissions)
  - [API JSON Example](#api-json-example)
  - [URL JSON Example](#url-json-example)
- [Best Practices](#best-practices)
- [Contact and Support](#contact-and-support)

---

## Introduction

The **Gorilla API Store** is designed to enhance the ability of large language models (LLMs) to interact with various APIs, improving their accuracy and reducing hallucinations in function calls. We aim to build an open-source, one-stop-shop for all APIs that LLMs can invoke effectively.

[Gorilla](https://gorilla.cs.berkeley.edu/) currently supports **1,600+ APIs** and counting. By contributing your APIs to this ecosystem, you'll help expand this store and enable more accurate and context-aware API calls by LLMs. We offer multiple ways to contribute, making it easy to get involved.

---

## Contribution Methods

You can contribute to the Gorilla API Store in two ways:

### Option 1: API JSON Contribution (Preferred)

This method allows for full control and customization over your API contribution. You will create a JSON file describing your API in detail, including function calls, arguments, and example code. This method is the preferred option because it ensures a higher level of accuracy in documenting your API.

### Option 2: URL JSON Contribution

If you're short on time or resources, you can simply provide a URL to your API documentation, and we will generate the API JSON for you using an LLM. Please note that this method may require additional verification to ensure the generated JSON is accurate.

---

## Submission Process

To submit your API, follow these steps:

1. **Prepare Your API JSON** or **API URL JSON** as described below.
2. **Fork** the Gorilla repository.
3. **Have any issue** then create a new issue in [Issue section](https://github.com/ShishirPatil/gorilla/issues) and get the issue assigned then start working on it.
4. **Create a Pull Request** with your API JSON file added under the appropriate directory (`data/apizoo`) and make PR in [Pull request section](https://github.com/ShishirPatil/gorilla/pulls) .
5. We'll review your submission, and once approved, your API will become part of the Gorilla API Store.

---

## Contribution Format

### API JSON Format

For **API JSON** contributions, follow this format:

| Field              | Type         | Description                                                         | Required |
| ------------------ | ------------ | ------------------------------------------------------------------- | -------- |
| `user_name`        | String       | Name of the contributor.                                            | ✅       |
| `api_name`         | String       | Name of the API (max 20 words).                                     | ✅       |
| `api_call`         | String       | A one-line function call with arguments and values.                 | ✅       |
| `api_version`      | String       | Version of the API.                                                 | ✅       |
| `api_arguments`    | JSON         | JSON object listing the function's arguments and valid options.     | ✅       |
| `functionality`    | String       | Short description of the function (max 20 words).                   | ✅       |
| `env_requirements` | List[String] | List of any required libraries or dependencies.                     | Optional |
| `example_code`     | String       | Example code showing how to use the API.                            | Optional |
| `meta_data`        | JSON         | Additional information such as descriptions or performance metrics. | Optional |
| `questions`        | List[String] | Questions that describe real-life scenarios for using this API.     | Optional |

---

### URL JSON Format

For **URL JSON** contributions, follow this format:

| Field       | Type         | Description                                                     | Required |
| ----------- | ------------ | --------------------------------------------------------------- | -------- |
| `user_name` | String       | Name of the contributor.                                        | ✅       |
| `api_name`  | String       | Name of the API (max 20 words).                                 | ✅       |
| `api_url`   | String       | URL to the API documentation.                                   | ✅       |
| `questions` | List[String] | Questions that describe real-life scenarios for using this API. | Optional |

---

## Example Submissions

### API JSON Example:

```json
[
  {
    "user_name": "example_username_api",
    "api_name": "Torch Hub Model snakers4-silero",
    "api_call": "torch.hub.load(repo_or_dir=['snakers4/silero-models'], model=['silero_stt'], *args, source, trust_repo, force_reload, verbose, skip_validation, **kwargs)",
    "api_version": "2.0",
    "api_arguments": {
      "repo_or_dir": "snakers4/silero-models",
      "model": "silero_stt",
      "language": ["en", "de", "es"]
    },
    "functionality": "Speech to Text",
    "env_requirements": ["torchaudio", "torch", "omegaconf", "soundfile"],
    "example_code": "import torch\nmodel = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)\nimgs = ['https://ultralytics.com/images/zidane.jpg']\nresults = model(imgs)",
    "meta_data": {
      "description": "Silero Speech-To-Text models provide enterprise-grade STT in a compact form factor.",
      "performance": { "dataset": "imagenet", "accuracy": "80.4%" }
    },
    "questions": [
      "I am a doctor and I want to dictate what my patient is saying and put it into a text doc in my computer.",
      "My math students need an API to write down what I am saying for reviewing."
    ]
  }
]
```

##

## URL JSON Example:

```json
[
  {
    "user_name": "example_username_url",
    "api_name": "Torch Hub ultralytics_yolov5",
    "api_url": "https://pytorch.org/hub/ultralytics_yolov5/",
    "questions": [
      "I am a doctor and I want to dictate what my patient is saying and put it into a text doc in my computer.",
      "My math students need an API to write down what I am saying for reviewing."
    ]
  }
]
```

# Best Practices

#### Clear Documentation

- Ensure that the URL points to clear and well-documented API information. This helps us generate accurate API JSON.

#### Accurate API Calls

- Double-check the API calls in the documentation to ensure they are syntactically and semantically correct.

#### Dependencies

- Make sure that the URL lists all necessary dependencies and environment requirements for the API to function properly.

#### Test Your API

- Whenever possible, provide working examples or sample code in your API documentation to demonstrate how the API functions.

## Contact and Support

For any questions or issues with your contribution, please reach out through one of the following:

- **Discord**: Join our [community](https://discord.com/invite/grXXvj9Whz) for real-time support.
- **Checkout our paper** : checkout our [papers](https://arxiv.org/abs/2305.15334) for more information
- Use [Gorilla in your CLI](https://github.com/gorilla-llm/gorilla-cli) with ` pip install gorilla-cli`
- **Email**: Contact us at support@gorilla-apistore.com.

**We look forward to your contributions!**
