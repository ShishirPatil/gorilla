import json
import argparse


parser = argparse.ArgumentParser(description="Replace placeholders in the function credential config file.")
parser.add_argument("--input-file", help="Path to the function credential config file.", required=True)
parser.add_argument("--output-file", help="Path to the output file.", default="")
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

def main():
    # Verify all values are provided
    for key, value in PLACEHOLDERS.items():
        if value == "":
            print(f"Please provide a value for the placeholder {key}.")
            return
    print("All API keys are present.")
        
    modified_data = []
    with open(f"{args.input_file}", 'r') as f:
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

    if args.output_file == "":
        with open(f"{args.input_file}", 'w') as f:
            for modified_line in modified_data:
                f.write(modified_line + '\n')  # Write each modified JSON object back to the input file
        print(f"All placeholders have been replaced in {args.input_file} 🦍.")
    else:
        with open(f"{args.output_file}", 'w') as f:
            for modified_line in modified_data:
                f.write(modified_line + '\n')  # Write each modified JSON object overwrite the output file
        print(f"All placeholders have been replaced in {args.output_file} 🦍.")
                
if __name__ == "__main__":
    main()