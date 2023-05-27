# Gorilla API Store 

<img src="https://github.com/ShishirPatil/gorilla/blob/gh-pages/assets/img/logo.png" width=50% height=50%>

Wants Gorilla to use your API? Wants to train your own Gorilla with the dataset? Learn about the entire workflow and how to contribute to Gorilla API App Store! Gorilla API App Store intends to enhance LLM's capability to use tools through API calls. We appreciate everyone's effort and contribution!

## How to Contribute?

Contribute to Gorilla API Store is very easy! 

1. **JSON Contribution**: It only takes two steps

- Step 1: Submit an API JSON file or a URL JSON file following our cirteria. 
- Step 2: Put up a Pull Request.

2. **Website Contribution**: We will provide a website and you only need to put in your API url. We will provide a draft API JSON file to you and you can either choose to **Submit** or **Edit & Submit**. 

## Repository Organization
 
Once we approve your merge, your data will be merged to a file under your username! Our repository organization is as follows: 

```
gorilla_api_store
├── dataset
│   │   ├── APIBench (Evaluating LLM models) v-0.1
│   │   │   ├── {api_name}_train.jsonl, {api_name}_eval.jsonl
│   │   ├── APIZoo (Contributed by our Community)
│   │   │   ├── username1.jsonl
│   │   │   ├── username2.jsonl
│   │   │   ├── username3.jsonl
│   │   │   ├── ...
```

## JSON Contribution

We make the contribution to Gorilla API Store as easy as possible. You could either submit following the API JSON format or URL JSON format. 

### API JSON

Community members can submit to Gorilla API Zoo using the following JSON format:

| Field      |  Type  | Description/Options     | Required |
| :---       | :----: |          :----         |   :---:   |
| user_name     | String       | Name of User   | ✅ |
| api_name      | String       | Name of API (maximum 20 words)   | ✅ |
| api_call | String | One line of code that starts with the function call, fullowed by a full list of argument names and values | ✅ |
| api_version | String | Version of API | ✅ |
| api_arguments | JSON | JSON of all the restricted keywords in the arguments list | ✅ |
| functionality | String | Short description of the function (maximum 20 words) | ✅ |
| env_requirements | List[String] | List of all the library dependencies | [Optional]:fire: |
| example_code | String | A string containing example code to use the API | [Optional]:fire: |
| meta_data | JSON | A JSON file of containing additional information about the API | [Optional]:fire: |
| Questions | List[String] | A question describing a real-life scenario that uses this API. Please donnot include specific API name. | [Optional]:fire: |

**Example Submission**:

```python
{
  "user_name": "tianjun_z",
  "api_name": "Torch Hub Model Load",
  "api_call": torch.hub.load(repo_or_dir=['snakers4/silero-models'], model=['silero_stt'], *args, source, trust_repo, force_reload, verbose, skip_validation, **kwargs), 
  "api_version": 2.0, 
  "api_arguments": {
    "repo_or_dir": "snakers4/silero-models", 
    "model": "silero_stt", 
    "language": ["en", "de", "es"]
  },
  "functionality": "Speech to Text",
  "env_requirements": ["torchaudio", "torch", "omegaconf", "soundfile"],
  "example_code": "import torch
                   model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
                   imgs = ['https://ultralytics.com/images/zidane.jpg']
                   results = model(imgs)",
  "meta_data": {
    "description": "Silero Speech-To-Text models provide enterprise grade STT in a compact form-factor for several commonly spoken languages. The models are robust to a variety of dialects, codecs, domains, noises, and lower sampling rates. They consume a normalized audio in the form of samples and output frames with token probabilities. A decoder utility is provided for simplicity.", 
    "performance": {"dataset": "imagenet", "accuracy": "80.4\%"}
  },
  "questions": [
    "I am a doctor and I want to dictate what my patient is saying and put it into a text doc in my computer.",
    "My students in math class is having trouble following up my content. He needs an API to write down what I am saying for reviewing.",
  ],
}
```

### URL JSON

We also provide you another much simpler approach for you to contribute! Provide a simple url to your API documentation, we'll process for you. For this, submit a JSON file containing the URL: 

| Field      |  Type  | Description/Options     | Required |
| :---       | :----: |          :----         |   :---:   |
| user_name     | String       | Name of User   | ✅ |
| api_name      | String       | Name of API (maximum 20 words)   | ✅ |
| api_url      | String       | URL to API documentation   | ✅ |
| Questions | List[String] | A question describing a real-life scenario that uses this API. Please donnot include specific API name. | [Optional]:fire: |

**Example Submission**:

```python
{
  "user_name": "tianjun_z",
  "api_name": "Torch Hub Model Load",
  "url": "https://pytorch.org/hub/ultralytics_yolov5/",
  "questions": [
    "I am a doctor and I want to dictate what my patient is saying and put it into a text doc in my computer.",
    "My students in math class is having trouble following up my content. He needs an API to write down what I am saying for reviewing.",
  ],
}
```

## Website Contribution

Visit our [website](), type in the API URL and we'll output an example submission for you! You can choose to submit or edit an then submit. Easy and quick!
