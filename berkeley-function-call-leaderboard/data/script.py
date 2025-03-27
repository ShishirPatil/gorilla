import os
import json

# Paths
input_folder = "/Users/catherinewu/projects/gorilla/berkeley-function-call-leaderboard/data"
extracted_folder = os.path.join(input_folder, "possible_answer")

# List of files to process
target_files = [
    "BFCL_v3_exec_multiple.json",
    "BFCL_v3_exec_parallel_multiple.json",
    "BFCL_v3_exec_parallel.json",
    "BFCL_v3_exec_simple.json"
]

for filename in target_files:
    input_path = os.path.join(input_folder, filename)
    extracted_path = os.path.join(extracted_folder, filename)

    cleaned_data = []
    extracted_data = []

    # Read and parse each line as a separate JSON object
    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            cleaned_entry = {k: v for k, v in entry.items() if k not in {"ground_truth", "execution_result_type"}}
            extracted_entry = {
                "id": entry.get("id"),
                "ground_truth": entry.get("ground_truth"),
                "execution_result_type": entry.get("execution_result_type")
            }
            cleaned_data.append(cleaned_entry)
            extracted_data.append(extracted_entry)

    # Save cleaned data (compact JSON lines)
    with open(input_path, "w", encoding="utf-8") as f:
        for entry in cleaned_data:
            f.write(json.dumps(entry, separators=(",", ":")) + "\n")

    # Save extracted metadata (compact JSON lines)
    with open(extracted_path, "w", encoding="utf-8") as f:
        for entry in extracted_data:
            f.write(json.dumps(entry, separators=(",", ":")) + "\n")

print("✅ Done. JSONL files cleaned and metadata extracted.")