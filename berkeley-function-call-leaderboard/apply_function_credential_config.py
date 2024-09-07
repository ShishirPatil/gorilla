import glob
import json
import argparse
import os
from bfcl.eval_checker import custom_exception

parser = argparse.ArgumentParser(description="Replace placeholders in the function credential config file.")
parser.add_argument("--input-path", help="Path to the function credential config file. Can be a file or a directory.")
parser.add_argument("--output-path", help="Path to the output file.")
args = parser.parse_args()

# Load the configuration with actual API keys
with open("function_credential_config.json") as f:
    function_credential_config = json.load(f)

PLACEHOLDERS = {
    "YOUR-GEOCODE-API-KEY": function_credential_config[3]["GEOCODE-API-KEY"],
    "YOUR-RAPID-API-KEY": function_credential_config[0]["RAPID-API-KEY"],
    "YOUR-OMDB-API-KEY": function_credential_config[2]["OMDB-API-KEY"],
    "YOUR-EXCHANGERATE-API-KEY": function_credential_config[1]["EXCHANGERATE-API-KEY"]
}


def replace_placeholders(data):
    """
    Recursively replace placeholders in a nested dictionary or list using string.replace.
    """
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                replace_placeholders(value)
            elif isinstance(value, str):
                for placeholder, actual_value in PLACEHOLDERS.items():
                    if placeholder in value:  # Check if placeholder is in the string
                        data[key] = value.replace(placeholder, actual_value)
    elif isinstance(data, list):
        for idx, item in enumerate(data):
            if isinstance(item, (dict, list)):
                replace_placeholders(item)
            elif isinstance(item, str):
                for placeholder, actual_value in PLACEHOLDERS.items():
                    if placeholder in item:  # Check if placeholder is in the string
                        data[idx] = item.replace(placeholder, actual_value)
    return data


def process_file(input_file_path, output_file_path):
    modified_data = []
    with open(input_file_path, "r") as f:
        lines = f.readlines()
        for line in lines:
            try:
                data = json.loads(line)  # Parse each line as a JSON object
                data = replace_placeholders(data)  # Replace placeholders
                modified_data.append(json.dumps(data))  # Convert back to string and store
            except json.JSONDecodeError:
                # Handle the case where a line is not a valid JSON object
                print("Invalid JSON line skipped.")
                continue
    
    # Write the modified data to the output file
    with open(output_file_path, "w") as f:
        for i, modified_line in enumerate(modified_data):
            f.write(modified_line)
            if i < len(modified_data) - 1:  # Check against the length of modified_data
                f.write("\n")        
    print(f"All placeholders have been replaced for {input_file_path} 🦍.")
    
    
def process_dir(input_dir, output_dir):
    # This function does not support nested directories
    # To support nested directories, refer to this commit:
    # https://github.com/ShishirPatil/gorilla/pull/508/commits/8b1e35590e5bce3bd52a7c6405775b1ce4a64945
    print(f"Input directory: {input_dir}")
    # Get a list of all entries in the folder
    entries = os.scandir(input_dir)

    json_files_pattern = os.path.join(input_dir, "*.json")
    for input_file_path in glob.glob(json_files_pattern):
        file_name = os.path.basename(input_file_path)
        output_file_path = os.path.join(output_dir, file_name)
        process_file(input_file_path, output_file_path)
        

if __name__ == "__main__":
    # Verify all values are provided
    for key, value in PLACEHOLDERS.items():
        if value == "":
            raise custom_exception.NoAPIKeyError()
    print("All API keys are present.")
    
    input_path = args.input_path
    if input_path is None:
        input_path = "./data/" 
    
    output_path = args.output_path
    if output_path is None:
        output_path = input_path
    
    if os.path.isdir(input_path):
        process_dir(input_path, output_path)
    else:
        process_file(input_path, output_path)