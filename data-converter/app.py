import json
import os
import time
import requests 

from json import dumps
from flask import Flask, request, render_template, jsonify
from openai import OpenAI
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from github import Github, GithubException

load_dotenv()

# Load .env variables
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
FORKED_REPO = os.getenv("FORKED_REPO")  # Adjust to your forked repository
MAIN_REPO = os.getenv("MAIN_REPO")  # Adjust to the main repository

app = Flask(__name__)
client = OpenAI(api_key=OPENAI_API_KEY)
g = Github(GITHUB_TOKEN)


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/convert', methods=['POST'])
def convert_json():
    option_2_json = request.get_json()
    api_documentation = get_api_documentation(option_2_json)
    option_1_format = convert_to_option1(api_documentation, option_2_json)
    option_1_json = process_model_output(option_1_format, option_2_json)
    
    return jsonify(option_1_json)


@app.route('/pullrequest', methods=['POST'])
def submit_pr():
    content = request.get_json()
    user_name = content.get('user_name')
    if not user_name:
        return jsonify({"message": "User name is required."}), 400

    file_path = f"data/apizoo/{user_name}.json"
    new_branch_name = create_unique_branch_name(user_name)
    
    try:
        fork_repo = g.get_repo(FORKED_REPO)
        main_repo = g.get_repo(MAIN_REPO)

        base_branch = main_repo.default_branch
        create_branch(fork_repo, new_branch_name, main_repo, base_branch)

        commit_message = f"Add new file for {user_name}"
        file_content = dumps(content, indent=2) + '\n'
        create_file_in_repo(fork_repo, file_path, commit_message, file_content, new_branch_name)

        pr_title = f"Add {user_name}'s file"
        pr_head = f"{FORKED_REPO.split('/')[0]}:{new_branch_name}"
        submit_pull_request(main_repo, pr_title, "Please pull this in!", pr_head, base_branch)

        return jsonify({"message": "Pull request submitted successfully."}), 200

    except GithubException as e:
        return jsonify({"message": "Error submitting pull request.", "details": str(e)}), 500


######################
## HELPER FUNCTIONS ##
######################

def create_unique_branch_name(user_name):
    """Generate a unique branch name to avoid conflicts."""
    timestamp = int(time.time())
    return f"{user_name}-branch-{timestamp}"

def create_branch(target_repo, new_branch, base_repo, base_branch):
    """Create a new branch in the repository."""
    latest_commit_sha = base_repo.get_branch(branch=base_branch).commit.sha
    target_repo.create_git_ref(ref=f"refs/heads/{new_branch}", sha=latest_commit_sha)

def create_file_in_repo(repo, file_path, commit_message, content, branch):
    """Create a new file in the specified repository and branch."""
    repo.create_file(path=file_path, message=commit_message, content=content, branch=branch)

def submit_pull_request(main_repo, title, body, head, base):
    """Submit a pull request to the main repository."""
    main_repo.create_pull(title=title, body=body, head=head, base=base)


def process_model_output(option_1_format: str, option_2_json: dict) -> dict:
    try:
        # Directly load the option_1_format string into a Python dictionary
        option_1_dict = json.loads(option_1_format)
    except json.JSONDecodeError as e:
        # Handle the case where the string cannot be converted to JSON
        return {"error": "Failed to parse the Option 1 format into JSON: " + str(e)}, 400

    # Assuming option_1_dict is a list of dictionaries based on your original code
    if isinstance(option_1_dict, list) and option_1_dict:
        option_1_dict[0]["user_name"] = option_2_json.get("user_name", "")
        option_1_dict[0]["api_name"] = option_2_json.get("api_name", "")
    elif isinstance(option_1_dict, dict):
        # If option_1_dict is a dictionary, directly update/add "user_name"
        option_1_dict["user_name"] = option_2_json.get("user_name", "")
    
    return option_1_dict

def get_api_documentation(data: dict):
    assert 'api_url' in data
    api_url = data['api_url']
    response = requests.get(api_url)
    html_content = response.text

    # Parse the HTML
    soup = BeautifulSoup(html_content, 'lxml')

    # Attempt to find the <main> tag first
    main_content = soup.find('main')

    # If <main> tag not found, look for divs with common main content class names
    if not main_content:
        common_class_names = ['main-content', 'api-documentation', 'content', 'primary-content']
        for class_name in common_class_names:
            main_content = soup.find('div', class_=class_name)
            if main_content:
                break

    if not main_content:
        main_content = soup # Fallback to the whole non of the divs above were found

    texts = []
    for tag in main_content.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'code', 'section']):
        text = tag.get_text(separator=' ', strip=True)
        texts.append(text)

    # Join all pieces of texts into a single string
    clean_text = '\n'.join(texts)

    return clean_text


def convert_to_option1(api_documentation: str, data: dict):
    prompt = get_prompt(data, api_documentation)
    result = convert_with_model(prompt)
    return result


def convert_with_model(prompt: str) -> str:
    completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model="gpt-3.5-turbo",
    )
    converted_data: str = completion.choices[0].message.content
    return converted_data



def get_prompt(data, api_documentation):
    return f"""Read the following API documentation about {data["api_name"]} api and fill out the relvenant information in the option 1 JSON format:

Here is what the Option 1 format should look like:

Option 1 API JSON Format:
Fill out a JSON using the following JSON list format:

| Field          | Type  | Description/Options                                                            |
|----------------|-------|---------------------------------------------------------------|
| `api_call`     | String| One line of code that starts with the function call, followed by a full list of argument names and values |
| `api_version`  | String| Version of the API                                                             | 
| `api_arguments`| JSON  | JSON of all the restricted keywords in the arguments list                      | 
| `functionality`| String| Short description of the function (maximum 20 words)                           | 


Example Submission:

[ 
  {{
    "api_call": "torch.hub.load(repo_or_dir=['snakers4/silero-models'], model=['silero_stt'], *args, source, trust_repo, force_reload, verbose, skip_validation, **kwargs)", 
    "api_version": 2.0, 
    "api_arguments": {{
      "repo_or_dir": "snakers4/silero-models", 
      "model": "silero_stt", 
      "language": ["en", "de", "es"]
    }},
    "functionality": "Speech to Text",
  }},
]


Here is the HTML of the api documentation, parse it and find the relevent information to fill out a Option 1 Json.

{api_documentation}

_______
Give me just the Option 1 format JSON. Don't say anything else. Just the option 1 JSON.
"""


if __name__ == '__main__':
    app.run(debug=True)
