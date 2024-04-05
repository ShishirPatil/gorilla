import json

data = []
"""
    Compile evaluation data into a single file
"""

test_files = [
    "executable_parallel_function",
    "parallel_multiple_function",
    "executable_simple",
    "rest",
    "sql",
    "parallel_function",
    "chatable",
    "java",
    "javascript",
    "executable_multiple_function",
    "simple",
    "relevance",
    "executable_parallel_multiple_function",
    "multiple_function",
]

for test_name in test_files:
    with open(f"./data/gorilla_openfunctions_v1_test_{test_name}.json", "r") as file:
        for line in file:
            item = json.loads(line)
            item["question_type"] = test_name
            data.append(item)

with open("./eval_data_total.json", "w") as file:
    for item in data:
        file.write(json.dumps(item))
        file.write("\n")

print("Data successfully compiled into eval_data_total.json 🦍")
