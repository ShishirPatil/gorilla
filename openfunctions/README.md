# Gorilla OpenFunctions v2 

🎉 Gorilla OpenFunctions v2 is here!
💡 SoTA for open-source models (Apache 2.0). On-par with GPT-4. 

🚀 Try it out on the [leaderboard](https://gorilla.cs.berkeley.edu/leaderboard)   
📣 Read more in our [OpenFunctions v2 release blog](https://gorilla.cs.berkeley.edu/blogs/7_open_functions_v2.html)

## Introduction
Gorilla OpenFunctions extends Large Language Model(LLM) Chat Completion feature to formulate 
executable APIs call given natural language instructions and API context. With OpenFunctions v2 7B parameter model,
we now support:
1. Multiple functions - choose between functions 
2. Parallel functions - call the same function `N` time with different parameter values
3. Multiple & parallel - both of the above in a single chatcompletion call (one generation)
4. Relevance detection - when chatting, chat. When asked for function, returns a function
5. Python - supports `string, number, boolean, list, tuple, dict` parameter datatypes and `Any` for those not natively supported. 
6. JAVA - support for `byte, short, int, float, double, long, boolean, char, Array, ArrayList, Set, HashMap, Hashtable, Queue, Stack, and Any` datatypes.
7. JavaScript - support for `String, Number, Bigint, Boolean, dict (object), Array, Date, and Any` datatypes.
8. REST - native REST support


## Models Available
|Model | Functionality|
|---|---|
|gorilla-openfunctions-v2 | Multiple, parallel, multiple & parallel, relevance detection, Python + JAVA + JS + REST|
|gorilla-openfunctions-v1 | Parallel functions, and can choose between functions|
|gorilla-openfunctions-v0 | Given a function, and user intent, returns properly formatted json with the right arguments|


All of our models are hosted on our Huggingface UC Berkeley gorilla-llm org: [gorilla-openfunctions-v2](https://huggingface.co/gorilla-llm/gorilla-openfunctions-v2), [gorilla-openfunctions-v1](https://huggingface.co/gorilla-llm/gorilla-openfunctions-v1), and [gorilla-openfunctions-v0](https://huggingface.co/gorilla-llm/gorilla-openfunctions-v0) .

## Example Usage (Hosted)

1. OpenFunctions is compatible with OpenAI Functions

```bash
!pip install openai==0.28.1
```

2. Point to Gorilla hosted servers

```python
import openai

def get_gorilla_response(prompt="Call me an Uber ride type \"Plus\" in Berkeley at zipcode 94704 in 10 minutes", model="gorilla-openfunctions-v0", functions=[]):
  openai.api_key = "EMPTY"
  openai.api_base = "http://luigi.millennium.berkeley.edu:8000/v1"
  try:
    completion = openai.ChatCompletion.create(
      model="gorilla-openfunctions-v2",
      temperature=0.0,
      messages=[{"role": "user", "content": prompt}],
      functions=functions,
    )
    return completion.choices[0]
  except Exception as e:
    print(e, model, prompt)
```

3. Pass the user argument and set of functions, Gorilla OpenFunctions returns a fully formatted json

```python
query = "What's the weather like in the two cities of Boston and San Francisco?"
functions = [
    {
        "name": "get_current_weather",
        "description": "Get the current weather in a given location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The city and state, e.g. San Francisco, CA",
                },
                "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
            },
            "required": ["location"],
        },
    }
]
get_gorilla_response(query, functions=functions)
```

4. Expected output **NEW**

Gorilla returns a readily accessible string **AND** Open-AI compatible JSON. 

```python
{
  "index": 0,
  "message": {
    "role": "assistant",
    "content": "get_current_weather(location='Boston, MA'), get_current_weather(location='San Francisco, CA')",
    "function_call": [
      {
        "name": "get_current_weather",
        "arguments": {
          "location": "Boston, MA"
        }
      },
      {
        "name": "get_current_weather",
        "arguments": {
          "location": "San Francisco, CA"
        }
      }
    ]
  },
  "finish_reason": "stop"
}

```

We have retained the string functionality that our community loved from OpenFunctions v1 `get_current_weather(location='Boston, MA'), get_current_weather(location='San Francisco, CA')` above. And Notice the `function_call` key in the JSON to be OpenAI compatible.


This is possible in OpenFunctions v2, because we ensure that the output includes the name of the argument and not just the value. This enables us to parse the output into a JSON. In those scenarios where the output is not parsable into JSON, we will always return the function call string. 

### End to End Example

In the current directory, run the example code in `inference_hosted.py` to see how the model works.

```bash
python inference_hosted.py
```

Expected Output:

```bash
(.py3) shishir@dhcp-132-64:~/Work/Gorilla/openfunctions/$ python inference_hosted.py
--------------------
Function call strings(s): get_current_weather(location='Boston, MA'), get_current_weather(location='San Francisco, CA')
--------------------
OpenAI compatible `function_call`: [<OpenAIObject at 0x1139ba890> JSON: 
{
  "name": "get_current_weather",
  "arguments": 
  {
    "location": "Boston, MA"
  }
}, <OpenAIObject at 0x1139ba930> JSON: {
  "name": "get_current_weather",
  "arguments": 
  {
    "location": "San Francisco, CA"
  }
}]
```


## Running OpenFunctions Locally

If you want to Run OpenFunctions locally, here is the prompt format that we used: 

```python
def get_prompt(user_query: str, functions: list = []) -> str:
    """
    Generates a conversation prompt based on the user's query and a list of functions.

    Parameters:
    - user_query (str): The user's query.
    - functions (list): A list of functions to include in the prompt.

    Returns:
    - str: The formatted conversation prompt.
    """
    system = "You are an AI programming assistant, utilizing the Gorilla LLM model, developed by Gorilla LLM, and you only answer questions related to computer science. For politically sensitive questions, security and privacy issues, and other non-computer science questions, you will refuse to answer."
    if len(functions) == 0:
        return f"{system}\n### Instruction: <<question>> {user_query}\n### Response: "
    functions_string = json.dumps(functions)
    return f"{system}\n### Instruction: <<function>>{functions_string}\n<<question>>{user_query}\n### Response: "
```

And you can use the following code to format the response:

```python

from openfunctions_utils import strip_function_calls, parse_function_call

def format_response(response: str):
    """
    Formats the response from the OpenFunctions model.

    Parameters:
    - response (str): The response generated by the LLM.

    Returns:
    - str: The formatted response.
    - dict: The function call(s) extracted from the response.

    """
    function_call_dicts = None
    try:
        response = strip_function_calls(response)
        # Parallel function calls returned as a str, list[dict]
        if len(response) > 1: 
            function_call_dicts = []
            for function_call in response:
                function_call_dicts.append(parse_function_call(function_call))
            response = ", ".join(response)
        # Single function call returned as a str, dict
        else:
            function_call_dicts = parse_function_call(response[0])
            response = response[0]
    except Exception as e:
        # Just faithfully return the generated response str to the user
        pass
    return response, function_call_dicts
        
```

### End to End Example

First, follow the setup instructions as follows:
```bash
# Create a new Conda environment with Python 3.10
conda create -n openfunctions python=3.10
conda activate openfunctions
pip install -r requirements.txt
```

Then, run the example code in `inference_local.py` to see how the model works.

```bash
python inference_local.py
```
Expected Output (if you are using `query_1` and `functions_1`):
```
Loading checkpoint shards: 100%|███████████████████████████████████████████████████████████████████████| 2/2 [00:06<00:00,  3.15s/it]
...
...
--------------------
Function call strings 1(s): get_current_weather(location='Boston, MA'), get_current_weather(location='San Francisco, CA')
--------------------
OpenAI compatible `function_call`: [{'name': 'get_current_weather', 'arguments': {'location': 'Boston, MA'}}, {'name': 'get_current_weather', 'arguments': {'location': 'San Francisco, CA'}}]
--------------------
```

**Note:** Use the `get_prompt` and `format_response`  only if you are hosting it locally. If you are using the Berkeley hosted models through the Chat-completion API, we do this in the backend, so you don't have to do this. The model is supported in Hugging Face 🤗 Transformers and can be run up locally.


## Evaluation

The Berkeley Open Functions Leaderboard is a platform for evaluating the performance of models on function calling. The leaderboard is a collection of user-submitted prompts and the corresponding model responses. The leaderboard will be updated in real-time as new prompts are submitted. The leaderboard is available at [https://gorilla.cs.berkeley.edu/leaderboard](https://gorilla.cs.berkeley.edu/leaderboard).


## License

Gorilla OpenFunctions v2 is distributed under the Apache 2.0 license. This software incorporates elements from the Deepseek model. Consequently, the licensing of Gorilla OpenFunctions v2 adheres to the Apache 2.0 license, with additional terms as outlined in [Appendix A](https://github.com/deepseek-ai/DeepSeek-LLM/blob/6712a86bfb7dd25c73383c5ad2eb7a8db540258b/LICENSE-MODEL) of the Deepseek license.


## Contributing

Gorilla is an open source effort from UC Berkeley and we welcome contributors. 
Please email us your comments, criticism, and questions. More information about the project can be found at [https://gorilla.cs.berkeley.edu/](https://gorilla.cs.berkeley.edu/)

