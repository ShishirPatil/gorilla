import os
import pickle
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


def list_channels():
    # channel is a string start with @
    # Load Slack credentials
    credentials_path = './credentials/slack/token.pickle'
    if os.path.exists(credentials_path):
        with open(credentials_path, 'rb') as token_file:
            slack_token = pickle.load(token_file)
    else:
        raise FileNotFoundError("Slack token file not found.")
    client = WebClient(token=slack_token)

    try:
        # Call the conversations.list method using the WebClient
        result = client.conversations_list()
        print(result["channels"])

    except SlackApiError as e:
        # Print the error
        print(f"Error sending message: {e.response['error']}")
        raise
    
