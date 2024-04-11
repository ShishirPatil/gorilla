import os
import pickle
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


def slack_delete_most_recent_message_dummy():
    # Load Slack credentials
    credentials_path = './credentials/slack/token.pickle'
    if os.path.exists(credentials_path):
        with open(credentials_path, 'rb') as token_file:
            slack_token = pickle.load(token_file)
    else:
        raise FileNotFoundError("Slack token file not found.")
    client = WebClient(token=slack_token)


    try:
        result = client.conversations_history(
            channel="<<channel_id_placeholder>>",
            limit=1
        )
        last_message = result['messages'][0]['ts'] if result['messages'] else None
        if last_message:
            # Call the chat.delete method to delete the most recent message
            delete_result = client.chat_delete(
                channel="<<channel_id_placeholder>>",
                ts=last_message
            )
            print("Last message deleted successfully.", delete_result)
        else:
            print("No message found to delete.")

    except SlackApiError as e:
        # Print the error
        print(f"Error sending message: {e.response['error']}")
        raise
