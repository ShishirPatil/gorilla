# Parallel evaluation data generation of all models on $test_category

#!/bin/bash
export OPENAI_API_KEY=
export MISTRAL_API_KEY=
export FIRE_WORKS_API_KEY=
export ANTHROPIC_API_KEY=

# Activate environment
conda activate BFCL

# Define an array of model names using API keys / endpoints
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
    "fireworks-ai"
)
test_category="all"

# Run each test in the background
for model in "${models[@]}"
do
    python openfunctions_evaluation.py --model "$model" --test_category "$test_category" &
done

# Wait for all background processes to finish
wait

echo "All tests completed."