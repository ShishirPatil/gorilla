#!/bin/bash

# This script evaluates and checks the performance of the model glaiveai.

# Define variables for ease of use and readability
MODEL_PATH="glaiveai/glaive-function-calling-v1"
MODEL_ID="glaiveai"
QUESTION_FILE="eval_data_total.json"
ANSWER_DIR="./result/glaiveai"
ANSWER_FILE="${ANSWER_DIR}/result.json"
TEST_CATEGORY="executable"
NUM_GPUS=4

# Ensure the answer directory exists
mkdir -p "$ANSWER_DIR"

# Step 1: Evaluate the model
echo "Starting model evaluation data generation..."
python openfunctions_evaluation_vllm.py --model-path "$MODEL_PATH" --model-id "$MODEL_ID" --question-file "$QUESTION_FILE" --answer-file "$ANSWER_FILE" --num-gpus "$NUM_GPUS"
echo "Model evaluation data generation completed."

# Step 2: Check the model's output
echo "Starting evaluation checker for calculating Berkeley Function-Calling Leaderboard Statistics..."
python openfunctions_checker.py --model "$MODEL_ID" --test_category "$TEST_CATEGORY" --file_name "$ANSWER_FILE"
echo "Output check completed."

echo "Script execution completed."
