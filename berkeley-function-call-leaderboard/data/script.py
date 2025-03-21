import json

# Load the reference BFCL_v3_rest.json
with open("/Users/catherinewu/projects/gorilla/berkeley-function-call-leaderboard/data/BFCL_v3_rest.json", "r", encoding="utf-8") as f:
    bfcl_data = [json.loads(line) for line in f.readlines()]

# Load the rest-eval-response_v5.jsonl
with open("/Users/catherinewu/projects/gorilla/berkeley-function-call-leaderboard/data/possible_answer/o.json", "r", encoding="utf-8") as f:
    response_lines = f.readlines()

# Convert each line into the new format
converted = []
for i, line in enumerate(response_lines):
    converted.append({
        "id": bfcl_data[i]["id"],
        "ground_truth": line.strip()
    })

# Save the result
output_path = "/Users/catherinewu/projects/gorilla/berkeley-function-call-leaderboard/data/possible_answer/BFCL_v3_rest.json"
with open(output_path, "w", encoding="utf-8") as f:
    for item in converted:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")

output_path