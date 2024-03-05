# Sequential evaluation data generation of all models on $test_category

#!/bin/bash


conda activate BFCL

# Define an array of supported model names
models=(
    "gorilla-openfunctions-v2"
    "gpt-3.5-turbo-0125"
    "gpt-4-0613"
    "gpt-4-1106-preview"
    "gpt-4-0125-preview"
    "Nexusflow-Raven-v2"
    "mistral-large-latest"
    "claude-2.1"
    "claude-instant-1.2"
    "mistral-medium"
    "mistral-small"
    "mistral-tiny"
    "fireworks-ai"
)

# Define the test category
test_category="executable"

# Run each test in the background, directing output to individual files
for model in "${models[@]}"
do
    python openfunctions_checker.py --model "$model" --test_category "$test_category"
done

echo "All tests completed."