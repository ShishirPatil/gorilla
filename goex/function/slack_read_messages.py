import os
import pickle
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


def slack_read_messages(channel_id, limit=100):
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
        # Call the conversations.history method using the WebClient
        # conversations.history returns the first 100 messages by default
        # These results are paginated, see: https://api.slack.com/methods/conversations.history$pagination
        result = client.conversations_history(channel=channel_id, limit=limit)

        conversation_history = result["messages"]

        # Print results
        print("Message read successfully.", conversation_history, channel_id)
    
    except SlackApiError as e:
        # Print the error
        print(f"Error sending message: {e.response['error']}")
        raise