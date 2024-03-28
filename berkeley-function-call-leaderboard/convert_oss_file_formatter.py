import os
import json

# value represents the starting index of the file, the values are sorted, so rest gets rows 0 to 69 inclusive
# FILENAME_MAPPING = {
#     "rest": (0, 69),
#     "executable_multiple_function": (70, 119),
#     "executable_parallel_multiple_function": (120, 159),
#     "executable_parallel_function": (160, 209),
#     "javascript": (210, 259),
#     "multiple_function": (260, 459),
#     "sql": (460, 559),
#     "java": (560, 659),
#     "parallel_function": (660, 859),
#     "simple": (860, 1259),
#     "executable_simple": (1260, 1359),
#     "parallel_multiple_function": (1360, 1559),
#     "chatable": (1560, 1759),
#     "relevance": (1760, 1999),
# }
FILENAME_MAPPING = {
    "multiple_function": (0, 199),
    "executable_multiple_function": (200, 249),
    "parallel_multiple_function": (250, 449),
    "executable_parallel_function": (450, 499),
    "relevance": (500, 739),
    "rest": (740, 809),
    "executable_parallel_multiple_function": (810, 849),
    "executable_simple": (850, 949),
    "simple": (950, 1349),
    "chatable": (1350, 1549),
    "javascript": (1550, 1599),
    "sql": (1600, 1699),
    "java": (1700, 1799),
    "parallel_function": (1800, 1999),
}

# Split a given file into multiple files based on the filename mapping. Each file starts with "gorilla_openfunctions_v1_test_" and ends with the filename mapping key and "_result.json"
DIRS = [
    # "./result/meetkai_functionary-small-v2.2",
    "./result/google_gemma-7b-it",
     "./result/glaiveai_glaive-function-calling-v1",
     "./result/deepseek-ai_deepseek-coder-6.7b-instruct",
    #  ""
]

for DIR in DIRS:
    input_oss_file = os.path.join(DIR, "result.json")
    data = []
    with open(input_oss_file, "r") as f:
        file = f.readlines()
        for line in file:
            data.append(json.loads(line))

    for key, value in FILENAME_MAPPING.items():
        start, end = value
        output_file = os.path.join(DIR, f"gorilla_openfunctions_v1_test_{key}_result.json")
        with open(output_file, "w") as f:
            original_idx = 0
            for i in range(start, end + 1):
                new_json = {
                    "id": original_idx,
                    "result": data[i]["text"],
                }
                f.write(json.dumps(new_json) + "\n")
                original_idx += 1