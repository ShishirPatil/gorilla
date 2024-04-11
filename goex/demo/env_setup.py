"""
Setup Script for getting .env populated using .env.example
"""
import os
from pathlib import Path

ROOT_FOLDER_PATH = os.path.dirname(Path(os.path.realpath(__file__)).parent)

def parse_env_example(file_path):
    """
    Parses the .env.example file and returns a dictionary of the variables and their default values.
    """
    variables = {}
    with open(file_path, 'r') as file:
        for line in file:
            if line.strip() and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                variables[key] = value
    return variables

def create_filled_env(file_path, variables):
    """
    Creates a new .env file based on the variables dictionary provided by the user.
    """
    with open(file_path, 'w') as file:
        for key, value in variables.items():
            file.write(f'{key}={value}\n')

def main():
    env_path = '.env'
    if os.path.exists(env_path):
        env_example_path = env_path
    else:
        env_example_path = '.env.example'
    
    variables = parse_env_example(env_example_path)

    print("Please fill out the following fields for the .env config [Leave empty for default]:")
    
    for key in variables.keys():
        user_input = input(f"{key} [{variables[key]}]: ").strip()
        if 'PATH' in key:
            user_input = os.path.abspath(user_input) if user_input else os.path.abspath(variables[key])
        variables[key] = user_input if user_input else variables[key]

    create_filled_env(env_path, variables)

    print(f"Your configuration has been saved to {env_path}.")

if __name__ == "__main__":
    main()
