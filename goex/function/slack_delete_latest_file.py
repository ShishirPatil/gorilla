import os
import pickle
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

def slack_delete_latest_file(channel_id):
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
            channel=channel_id,
            limit=10
        )
        messages = result.get('messages', [])

        file_id = None
        msg_ts = None
        for message in messages:
            bots = message.get('files', [])
            if len(bots) > 0:
                file_id = bots[0].get('id', [])
                msg_ts = message.get('ts', [])
                break
        if file_id:
            # Delete the file
            deletion_result = client.files_delete(file=file_id)
            print("File deleted successfully.", deletion_result)

            msg_result = client.chat_delete(channel=channel_id, ts=msg_ts)
            print("Message deleted successfully.", msg_result)

        else:
            print("File not found.")
        
    except SlackApiError as e:
        print(f"Error deleting file: {e.response['error']}")
        raise
