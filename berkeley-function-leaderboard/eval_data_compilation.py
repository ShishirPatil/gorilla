import os
import json
data = []
"""
    Compile evaluation data into a single file
"""
for filename in os.listdir("./data"):
    if "gorilla" in filename:
        with open(f"./data/{filename}", "r") as file:
            for line in file:
                item = json.loads(line)
                name = filename.replace("gorilla_openfunctions_v1_test_","").replace(".json","")
                item["question_type"] = name
                data.append(item)
with open("./eval_data_total.json", "a+") as file:
    for item in data:
        file.write(json.dumps(item))
        file.write("\n")