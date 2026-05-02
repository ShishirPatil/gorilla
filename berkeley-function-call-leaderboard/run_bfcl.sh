#!/bin/bash
# BFCL Single-Turn and Multi-Turn Category Runner for prism-coder-7b-FC
# Runs all categories sequentially, reporting progress and timing

set -e
cd /Users/admin/gorilla-bfcl/berkeley-function-call-leaderboard
source venv/bin/activate

MODEL="prism-coder-7b-FC"
export PRISM_ENABLE_THINKING="1"

CATEGORIES=(
    "simple_python"
    "simple_java"
    "simple_javascript"
    "parallel"
    "multiple"
    "parallel_multiple"
    "irrelevance"
    "live_simple"
    "live_multiple"
    "live_parallel"
    "live_parallel_multiple"
    "live_irrelevance"
    "live_relevance"
    "multi_turn_base"
    "multi_turn_miss_func"
    "multi_turn_miss_param"
    "multi_turn_long_context"
    "memory_kv"
    "memory_vector"
    "memory_rec_sum"
    "web_search_base"
    "web_search_no_snippet"
)

echo "=== BFCL Generation Runner ==="
echo "Model: $MODEL"
echo "Categories: ${#CATEGORIES[@]}"
echo "Started: $(date)"
echo ""

for cat in "${CATEGORIES[@]}"; do
    echo "--- [$cat] Starting at $(date) ---"
    START=$SECONDS
    
    # Run bfcl generate
    bfcl generate --model "$MODEL" --test-category "$cat" --skip-server-setup 2>&1 || {
        echo "--- [$cat] FAILED (${ELAPSED}s) ---"
        continue
    }
    
    ELAPSED=$((SECONDS - START))
    echo "--- [$cat] Completed in ${ELAPSED}s ---"
    echo ""
done

echo ""
echo "=== Generation Complete at $(date) ==="
echo ""

# Join categories with commas for the CLI
CAT_LIST=$(IFS=,; echo "${CATEGORIES[*]}")

echo "=== Running Evaluation ==="
bfcl evaluate --model "$MODEL" --test-category "$CAT_LIST" 2>&1
echo ""
echo "=== All Done at $(date) ==="
