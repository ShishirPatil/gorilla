import os
import pickle
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


def slack_add_emoji_reaction(channel_id, emoji_name, timestamp_id):
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
        result = client.reactions_add(
            # The name of the conversation
            channel=channel_id,
            name=emoji_name,
            timestamp=timestamp_id,
        )
        print("Message sent successfully.", result)

    except SlackApiError as e:
        # Print the error
        print(f"Error sending message: {e.response['error']}")
        raise
