import os
import pickle
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


def slack_remove_latest_emoji_reaction(channel_name, emoji_name):
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
        result = client.conversations_history(
            channel=channel_name,
            limit=1
        )
        last_message = result['messages'][0]['ts'] if result['messages'] else None
        if last_message:
            react_result = client.reactions_remove(
                # The name of the conversation
                channel=channel_name,
                name=emoji_name,
                timestamp=last_message
            )
            print("Message sent successfully.", react_result)
        else:
            print("No message found to remove react.")

    except SlackApiError as e:
        # Print the error
        print(f"Error sending message: {e.response['error']}")
        raise
