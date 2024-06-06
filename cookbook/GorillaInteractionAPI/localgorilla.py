"""
"""
import re
import json
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

def get_prompt(user_query: str, functions: list = None) -> str:
    """
    Generates a conversation prompt based on the user's query and a list of functions.

    Parameters:
    - user_query (str): The user's query.
    - functions (list): A list of functions to include in the prompt.

    Returns:
    - str: The formatted conversation prompt.
    """
    if functions is None:
        functions = []

    if len(functions) == 0:
        return f"USER: <<question>> {user_query}\nASSISTANT: "

    functions_string = json.dumps(functions)
    return f"USER: <<question>> {user_query} <<function>> {functions_string}\nASSISTANT: "

def parse_function_call(generated_text : str) -> dict:
    """
    Parse function calls from the given generated text from Gorilla.

    Args:
        generated_text (str): The text containing function calls to be parsed.

    Returns:
        dict: A dictionary representing the parsed function call.
              The dictionary has two keys:
              - 'api_name': The name of the API or function.
              - 'parameters': A dictionary containing the function parameters and their values.

    Example:
        If the generated_text is "add(a=1, b=2)", the returned dictionary would be:
        {'api_name': 'add', 'parameters': {'a': '1', 'b': '2'}}
    """
    # Define a regex pattern to match function calls
    pattern = re.compile(r'(\w+)\(([^)]+)\)')

    # Find all matches in the generated text
    matches = pattern.findall(generated_text)

    # Process each match and create a dictionary for each function call
    result = {}
    for match in matches:
        api_name = match[0]
        arguments = match[1].split(', ')
        parameters = {arg.split('=')[0]: arg.split('=')[1].strip("'") for arg in arguments}

        result["api_name"] = api_name
        result["parameters"] = parameters

    return result

def initialize_llm() -> object:
    """
    Initializes Gorilla Large Language Model (LLM) for text generation.

    Returns:
        object: A text generation pipeline object configured with a pretrained language model.

    Notes:
        This function sets up the following components:
        - Device setup: Determines the device (CPU or GPU) based on availability.
        - Model and tokenizer setup: Loads a pretrained language model and its tokenizer.
        - Model configuration: Adjusts model parameters, such as data type and memory usage.
        - Moves the model to the selected device.
        - Pipeline setup: Creates a text generation pipeline with specified parameters.
    """
    # Device setup
    device: str = "cuda:0" if torch.cuda.is_available() else "cpu"
    torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

    # Model and tokenizer setup
    model_id : str = "gorilla-llm/gorilla-openfunctions-v0"
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(model_id, 
                                                 torch_dtype=torch_dtype, 
                                                 low_cpu_mem_usage=True)

    # Move model to device
    model.to(device)

    # Pipeline setup
    pipe = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        max_new_tokens=128,
        batch_size=16,
        torch_dtype=torch_dtype,
        device=device,
    )

    return pipe

def functioncall_act() -> dict:
    """
    Perform an action using a the Gorilla Large Language Model (LLM) to 
    generate a function call based on a user query.

    Returns:
        dict: A dictionary representing the parsed function call.
              The dictionary has two keys:
              - 'api_name': The name of the API or function.
              - 'parameters': A dictionary containing the function parameters and their values.
                             Parameters are extracted from the generated function call.

    Raises:
        RuntimeError: If there is an issue initializing the Language Model.
        ValueError: If there is an issue parsing the generated function call.
    """

    try:
        # Initialize Language Model
        pipe = initialize_llm()

        # Example usage
        query: str = "I need to react with three words, word wow, word test, word acting"

        # Schema for function call
        functions = [
            {
                "name": "React",
                "api_name": "functioncall_react",
                "description": "Find three words from the sentence",
                "parameters":  [
                    {"name": "word1", "description": "A word"},
                    {"name": "word2", "description": "A word"},
                    {"name": "word3", "description": "A word"}
                ]
            }
        ]

        # Generate prompt and obtain model output
        prompt = get_prompt(query, functions=functions)
        output = pipe(prompt)
        function_call = output[0]["generated_text"].split("ASSISTANT:")[1].strip()

        print(f"Generated function_call: {function_call}")

        # Parse the generated function call
        # You could add your own methods here for preprocessing, data sanitizing, etc.
        function_calls = parse_function_call(function_call)
        return function_calls

    except RuntimeError as e:
        print(f"Error initializing the Language Model: {e}")
        raise e
    except ValueError as e:
        print(f"Error parsing the generated function call: {e}")
        raise e
