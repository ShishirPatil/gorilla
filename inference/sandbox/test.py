from sandbox import Sandbox

# create an instance of our langauge level sandbox
s = Sandbox()

# code output - would be from LLM. Currently used the language translation example from colab notebook
code = """
print("Hello world")

from transformers import pipeline

def process_data(text, translation):
    response = translation(text)[0]['translation_text']
    return response

text = 'I feel very good today.'

# Load the translation model
translation = pipeline('translation_en_to_zh', model='Helsinki-NLP/opus-mt-en-zh')

# Process the data
response = process_data(text, translation)
print(response)
"""

# execute the code by the LLM
s.execute(code)