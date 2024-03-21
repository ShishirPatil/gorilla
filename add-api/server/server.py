import json
import base64
import os
import time
import requests
import urllib.parse
from json import dumps
from flask import Flask, request, jsonify, redirect, session, Response
from dotenv import load_dotenv
from urllib.parse import urlencode
from flask import Flask, jsonify
from flask_cors import CORS

from html_extraction import scrape, process_results
from customTypes import ConvertResult, ConvertedURL

# Load .env variables
load_dotenv()
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")

MAIN_REPO = "ShishirPatil/gorilla"
GITHUB_CALLBACK_URL = "http://localhost:8080/github/callback"
FRONTEND_URL = "http://localhost:3000/add-api/build"
SERVER_BASEURL = "http://localhost:8080"

app = Flask(__name__)
app.secret_key = os.urandom(24)
CORS(app, origins=[FRONTEND_URL], supports_credentials=True)

#########################
### Route Definitions ###
#########################

@app.route('/convert', methods=['POST'])
def convert_json():
    try:
        option_2_json = request.get_json()
        api_urls = option_2_json.get('api_urls')
        username = option_2_json.get("user_name")
        session["user_name"] = username
        scrape_results: dict = scrape(api_urls) 

        conversion_results = process_results(scrape_results, option_2_json)
        conversion_json_str = json.dumps(conversion_results, sort_keys=False, indent=2)
        
        return Response(conversion_json_str, status=200, mimetype='application/json')
    except Exception as e:
        print(e)
        return Response(json.dumps({"error": str(e)}), status=500, mimetype='application/json')


@app.route('/store-option1-content', methods=['POST'])
def store_option1_content():
    res = request.get_json()
    data = res.get('data')
    username = res.get("user_name")

    if not data or not username:
        raise BadRequest("Missing data or username in the request body.")

    # Store data in session to be used in the next routes
    session['urlResults'] = data
    session['user_name'] = username 

    return jsonify({"message": "Content stored successfully"}), 200


@app.route('/login/github', methods=['GET'])
def github_login():
    params = {
        'client_id': GITHUB_CLIENT_ID,
        'redirect_uri': GITHUB_CALLBACK_URL,
        'scope': 'repo',
        'state': os.urandom(16).hex(),  # Generate a secure random state
        'allow_signup': 'true'
    }
    query_params = urllib.parse.urlencode(params)
    return redirect(f"https://github.com/login/oauth/authorize?{query_params}")


@app.route('/github/callback')
def github_callback():
    code = request.args.get('code')
    access_token = exchange_code_for_token(code)

    if access_token:
        session['access_token'] = access_token
        return redirect(f'{SERVER_BASEURL}/raise-pr')
    else:
        # Provide feedback in case of error
        return jsonify(access_token), 400  


@app.route('/raise-pr', methods=['GET'])
def submit_pr():
    access_token = session.get('access_token')
    content: ConvertResult = session.get('urlResults')
    user_name = session.get("user_name")
    successfulResults = getSuccessfulResults(content)
    
    file_path = f"data/apizoo/{user_name}.json"
    new_branch_name = create_unique_branch_name(user_name)

    try:
        fork_repo_info = fork_repository(MAIN_REPO, access_token)
        fork_repo_name = fork_repo_info['full_name']
        create_branch(fork_repo_name, new_branch_name, access_token)

        commit_message = f"Add new file for {user_name}"
        file_content = dumps(list(successfulResults), indent=2) + '\n'
        create_file_in_repo(fork_repo_name, file_path, commit_message, file_content, new_branch_name, access_token)

        # TODO: write code to get the base_branch
        base_branch = "main"
        compare_url = generate_github_compare_url(MAIN_REPO, fork_repo_name, base_branch, new_branch_name)
        # Redirect the user to the compare URL
        return redirect(compare_url)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


#################################
## Github API HELPER FUNCTIONS ##
#################################

def generate_github_compare_url(main_repo, forked_repo, target_branch, new_branch_name):
    base_repo_user, repo_name = main_repo.split('/')
    forked_repo_user = forked_repo.split('/')[0]
    return f"https://github.com/{base_repo_user}/{repo_name}/compare/{target_branch}...{forked_repo_user}:{new_branch_name}?expand=1"


def exchange_code_for_token(code):
    """
    Exchange the authorization code for an access token from GitHub.

    :param code: The authorization code received from GitHub.
    :return: The access token as a string if the exchange is successful, None otherwise.
    """
    token_url = "https://github.com/login/oauth/access_token"
    headers = {'Accept': 'application/json'}
    payload = {
        'client_id': GITHUB_CLIENT_ID,
        'client_secret': GITHUB_CLIENT_SECRET,
        'code': code,
        'redirect_uri': GITHUB_CALLBACK_URL
    }
    try:
        # Make the POST request to exchange the code for an access token
        response = requests.post(token_url, headers=headers, data=payload)
        response_json = response.json()

        # Check if the response contains the access token
        if 'access_token' in response_json:
            return response_json['access_token']
        else:
            print("GitHub token exchange failed:", response_json)
            return None
    except requests.RequestException as e:
        print(f"Request failed: {e}")
        return None


def create_unique_branch_name(user_name):
    """Generate a unique branch name to avoid conflicts."""
    timestamp = int(time.time())
    return f"{user_name}-branch-{timestamp}"


def fork_repository(repo, access_token):
    """
    Fork a repository on GitHub using the access token
    """
    url = f"https://api.github.com/repos/{repo}/forks"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github.v3+json",
    }
    response = requests.post(url, headers=headers)
    if response.status_code == 202:
        return response.json()
    else:
        # Attempt to extract the GitHub error message from the response
        try:
            error_details = response.json()
            error_message = error_details.get('message', 'No error message provided.')
        except ValueError:
            # In case the response body does not contain valid JSON
            error_message = 'No error message provided.'

        # Include the status code and error message in the exception
        raise Exception(f"Failed to fork repository. Status code: {response.status_code}. Error: {error_message}")


def get_latest_commit_sha(repo, branch="main"):
    """
    Get the latest commit SHA of a branch in a repository using the access token stored in the session.
    """
    access_token = session.get('access_token')
    if not access_token:
        raise Exception("Access token is not available in the session.")

    url = f"https://api.github.com/repos/{repo}/git/ref/heads/{branch}"
    headers = {
        "Authorization": f"token {access_token}",
        "Accept": "application/vnd.github.v3+json",
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()["object"]["sha"]
    else:
        raise Exception("Failed to get latest commit SHA.")


def create_branch(repo, branch_name, access_token):
    """
    Create a new branch in a repository using the access token stored in the session.
    """
    latest_sha = get_latest_commit_sha(repo, "main")
    url = f"https://api.github.com/repos/{repo}/git/refs"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github.v3+json",
    }
    data = {
        "ref": f"refs/heads/{branch_name}",
        "sha": latest_sha,
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 201:
        return response.json()
    else:
        raise Exception("Failed to create branch.")


def create_file_in_repo(repo, file_path, commit_message, content, branch, access_token):
    url = f"https://api.github.com/repos/{repo}/contents/{file_path}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github.v3+json",
    }
    data = {
        "message": commit_message,
        "content": base64.b64encode(content.encode('utf-8')).decode('utf-8'),  # Content must be base64 encoded
        "branch": branch,
    }

    response = requests.put(url, headers=headers, json=data)

    if response.status_code in [200, 201]:  # 201 for Created, 200 for Updated
        return response.json()  # Return the JSON response if successful
    else:
        raise Exception(f"Failed to create file: {response.status_code} {response.json()}")


def submit_pull_request(main_repo, title, body, head, base, access_token):
    """Submit a pull request to the main repository."""
    url = f"https://api.github.com/repos/{main_repo}/pulls"
    headers = {
        "Authorization": f"token {access_token}",
        "Accept": "application/vnd.github.v3+json",
    }
    data = {
        "title": title,
        "body": body,
        "head": head,
        "base": base,
    }
    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 201:  # 201 Created
        print("Pull request submitted successfully.")
        return response.json()  # Returns the created pull request information
    else:
        raise Exception(f"Failed to create pull request: {response.status_code} {response.json()}")


###########################
## Misc Helper Functions ##
###########################

def getSuccessfulResults(urlResults: ConvertResult): 
    successfulResults = []
    for result in urlResults.values():
        if result["status"] == "success":
            successfulResults.append(result["data"])
        
    return successfulResults

if __name__ == "__main__":
    # TODO: remove debug=True for production.
    app.run(debug=True, host="localhost", port=8080)
