import os
import pickle
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


def slack_send_message(channel_id, text):
    # Load Slack credentials
    credentials_path = './credentials/slack/token.pickle'
    if os.path.exists(credentials_path):
        with open(credentials_path, 'rb') as token_file:
            slack_token = pickle.load(token_file)
    else:
        raise FileNotFoundError("Slack token file not found.")
    client = WebClient(token=slack_token)


    try:
        # Call the chat.postMessage method using the WebClient
        result = client.chat_postMessage(
            channel=channel_id, 
            text=text
        )
        print("Message sent successfully.", result)

    except SlackApiError as e:
        # Print the error
        print(f"Error sending message: {e.response['error']}")
        raise
