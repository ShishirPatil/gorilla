#!/bin/bash
# BFCL Single-Turn Category Runner for prism-coder-7b-FC
# Runs all single-turn categories sequentially, reporting progress and timing

set -e
cd /Users/admin/gorilla-bfcl/berkeley-function-call-leaderboard
source venv/bin/activate

MODEL="prism-coder-7b-FC"

# All single-turn categories (non-live + live)
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
)

echo "=== BFCL Generation Runner ==="
echo "Model: $MODEL"
echo "Categories: ${#CATEGORIES[@]}"
echo "Started: $(date)"
echo ""

for cat in "${CATEGORIES[@]}"; do
    echo "--- [$cat] Starting at $(date) ---"
    START=$SECONDS
    
    # Run with timeout of 30 min per category
    timeout 1800 bfcl generate --model "$MODEL" --test-category "$cat" --skip-server-setup 2>&1 || {
        echo "--- [$cat] FAILED or TIMED OUT (${ELAPSED}s) ---"
        continue
    }
    
    ELAPSED=$((SECONDS - START))
    echo "--- [$cat] Completed in ${ELAPSED}s ---"
    echo ""
done

echo ""
echo "=== Generation Complete at $(date) ==="
echo ""

# Now run evaluation on all categories at once
echo "=== Running Evaluation ==="
bfcl evaluate --model "$MODEL" --test-category "${CATEGORIES[@]}" 2>&1
echo ""
echo "=== All Done at $(date) ==="
