import random
from typing import Dict, List, Optional, Union
from copy import deepcopy
DEFAULT_STATE = {
    "generated_ids": set(),
    "user_count": 4,
    "user_map": {
        "Alice": "USR001",
        "Bob": "USR002",
        "Catherine": "USR003",
        "Daniel": "USR004",
    },
    "inbox": {
        1: {
            "sender_id": "USR001",
            "receiver_id": "USR002",
            "message": "My name is Alice. I want to connect.",
        },
        2: {
            "sender_id": "USR001",
            "receiver_id": "USR003",
            "message": "Could you upload the file?",
        },
        3: {
            "sender_id": "USR001",
            "receiver_id": "USR004",
            "message": "Could you upload the file?",
        },
        4: {"sender_id": "USR001", "receiver_id": "USR002", "message": "I am busy."},
        5: {"sender_id": "USR001", "receiver_id": "USR002", "message": "I am on leave."},
    },
    "message_count": 0,
    "current_user": None,
}
    
class MessageAPI:
    """
    A class representing a Message API for managing user interactions in a workspace.

    This class provides methods for user management, messaging, and message retrieval
    within a specific workspace. It maintains user information, sent messages, and
    received messages for each user.

    Attributes:
        user_map (Dict[str, str]): A mapping of user names to user IDs.
        inbox (Dict[int, Dict[str, Union[str, int]]]): A dictionary storing all messages.
        message_count (int): The total count of messages in the workspace.
        current_user (Optional[str]): The ID of the currently logged-in user.

    Methods:
        generate_id(): Generate a unique ID for a message.
        list_users(): List all users in the workspace.
        get_user_id(user: str): Get the user ID for a given username.
        login(user_id: str): Log in a user.
        send_message(receiver_id: str, message: str): Send a message to another user.
        view_messages_received(): View messages received by the current user.
        view_messages_sent(): View messages sent by the current user.
        delete_message(receiver_id: str, message_index: int): Delete a sent message.
        add_contact(name: str, user_id: str): Add a new contact to the workspace.
        search_messages(keyword: str): Search for messages containing a keyword.
        get_message_stats(): Get messaging statistics for the current user.
    """

    def __init__(self):
        """
        Initialize the MessageAPI with a workspace ID.
        """
        DEFAULT_STATE_COPY = deepcopy(DEFAULT_STATE)
        self.generated_ids = DEFAULT_STATE_COPY["generated_ids"]
        self.user_count: int = DEFAULT_STATE_COPY["user_count"]
        self.user_map: Dict[str, str] = DEFAULT_STATE_COPY["user_map"]
        self.inbox: Dict[int, Dict[str, Union[str, int]]] = DEFAULT_STATE_COPY["inbox"]
        self.message_count: int = DEFAULT_STATE_COPY["message_count"]
        self.current_user: Optional[str] = DEFAULT_STATE_COPY["current_user"]

    def _load_scenario(self, scenario: dict, long_context=False) -> None:
        """
        Load a scenario into the MessageAPI.

        Args:
            scenario (dict): A dictionary containing message data.
        """
        DEFAULT_STATE_COPY = deepcopy(DEFAULT_STATE)
        self._random = random.Random((scenario.get("random_seed", 200191)))
        self.user_count = scenario.get("user_count", DEFAULT_STATE_COPY["user_count"])
        self.current_user = scenario.get("current_user", DEFAULT_STATE_COPY["current_user"])
        self.user_map = scenario.get("user_map", DEFAULT_STATE_COPY["user_map"])

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, MessageAPI):
            return False

        for attr_name in vars(self):
            if attr_name.startswith("_"):
                continue
            model_attr = getattr(self, attr_name)
            ground_truth_attr = getattr(value, attr_name)

            if model_attr != ground_truth_attr:
                return False

        return True

    def generate_id(self):
        """
        Generate a unique ID for a message.
        """
        new_id = self._random.randint(
            10000, 99999
        )  # first 5 mapped by initial configuration.
        while new_id in self.generated_ids:
            new_id = self._random.randint(10000, 99999)
        self.generated_ids.add(new_id)
        return new_id

    def list_users(self) -> Dict[str, List[str]]:
        """
        List all users in the workspace.

        Returns:
            user_list (List[str]): List of all users in the workspace.
        """
        return {"user_list": list(self.user_map.keys())}

    def get_user_id(self, user: str) -> Dict[str, Optional[str]]:
        """
        Get user ID from user name.

        Args:
            user (str): User name of the user.

        Returns:
            user_id (Optional[str]): User ID of the user, or None if not found.
        """
        if user not in self.user_map:
            return {"error": f"User '{user}' not found in the workspace."}
        return {"user_id": self.user_map.get(user)}

    def message_login(self, user_id: str) -> Dict[str, Union[str, bool]]:
        """
        Log in a user with the given user ID to messeage application.

        Args:
            user_id (str): User ID of the user to log in.

        Returns:
            login_status (bool): True if login was successful, False otherwise.
            message (str): A message describing the result of the login attempt.
        """
        if user_id not in [id for id in self.user_map.values()]:
            return {"login_status": False, "message": f"User ID '{user_id}' not found."}
        self.current_user = user_id
        return {
            "login_status": True,
            "message": f"User '{user_id}' logged in successfully.",
        }

    def send_message(
        self, receiver_id: str, message: str
    ) -> Dict[str, Union[str, bool]]:
        """
        Send a message to a user.
        Args:
            receiver_id (str): User ID of the user to send the message to.
            message (str): Message to be sent.
        Returns:
            sent_status (bool): True if the message was sent successfully, False otherwise.
            message_id (int): ID of the sent message.
            message (str): A message describing the result of the send attempt.
        """
        # Check if there is a current user logged in
        if not self.current_user:
            return {"error": "No user is currently logged in."}
        # Validate receiver existence
        if receiver_id not in self.user_map.values():
            return {"error": f"Receiver ID '{receiver_id}' not found."}
        # Generate a unique message ID
        message_id = self.generate_id()
        # Store the message in the inbox
        self.inbox[message_id] = {
            "sender_id": self.current_user,
            "receiver_id": receiver_id,
            "message": message,
        }
        self.message_count += 1
        return {
            "sent_status": True,
            "message_id": message_id,
            "message": f"Message sent to '{receiver_id}' successfully.",
        }

    def delete_message(
        self, receiver_id: str, message_id: int
    ) -> Dict[str, Union[bool, str]]:
        """
        Delete a message sent to a user.
        Args:
            receiver_id (str): User ID of the user to send the message to.
            message_id (int): ID of the message to be deleted.
        Returns:
            deleted_status (bool): True if the message was deleted successfully, False otherwise.
            message_id (int): ID of the deleted message.
            message (str): A message describing the result of the deletion attempt.
        """
        if not self.current_user:
            return {"error": "No user is currently logged in."}
        # Check if the message exists in the inbox
        if message_id not in self.inbox:
            return {"error": f"Message ID {message_id} not found."}
        # Ensure the current user is either the sender or receiver of the message
        message_data = self.inbox[message_id]
        if (
            message_data["sender_id"] != self.current_user
            and message_data["receiver_id"] != self.current_user
        ):
            return {"error": "You do not have permission to delete this message."}
        # Check if the sender and receiver match the input arguments
        if (
            message_data["sender_id"] != self.current_user
            or message_data["receiver_id"] != receiver_id
        ):
            return {
                "error": f"Message ID {message_id} does not match the provided sender and receiver."
            }
        # If everything checks out, delete the message
        del self.inbox[message_id]
        return {
            "deleted_status": True,
            "message_id": message_id,
            "message": f"Message ID {message_id} deleted successfully.",
        }

    def view_messages_received(self) -> Dict[str, Union[Dict[str, List[str]], str]]:
        """
        View all messages sent to the current user.

        Returns:
            messages (Dict[str, List[str]]): Dictionary of senders and their messages sent to the current user.
        """
        if not self.current_user:
            return {"error": "No user is currently logged in."}
        # Dictionary to collect messages grouped by sender
        received_messages = {}
        # Loop through the inbox and collect messages sent to the current user
        for message_id, message_data in self.inbox.items():
            if message_data["receiver_id"] == self.current_user:
                sender = message_data["sender_id"]
                if sender not in received_messages:
                    received_messages[sender] = []
                received_messages[sender].append(message_data["message"])
        return {"messages": received_messages}

    def view_messages_sent(self) -> Dict[str, Union[Dict[str, List[str]], str]]:
        """
        View all historical messages sent by the current user.

        Returns:
            messages (Dict[str, List[str]]): Dictionary of receivers and messages sent by the current user.
        """
        if not self.current_user:
            return {"error": "No user is currently logged in."}
        # Dictionary to collect messages grouped by receiver
        sent_messages = {}
        # Loop through the inbox and collect messages sent by the current user
        for message_id, message_data in self.inbox.items():
            if message_data["sender_id"] == self.current_user:
                receiver = message_data["receiver_id"]
                if receiver not in sent_messages:
                    sent_messages[receiver] = []
                sent_messages[receiver].append(message_data["message"])
        return {"messages": sent_messages}

    def add_contact(self, user_name: str) -> Dict[str, Union[bool, str]]:
        """
        Add a contact to the workspace.
        Args:
            user_name (str): User name of contact to be added.
        Returns:
            added_status (bool): True if the contact was added successfully, False otherwise.
            user_id (str): User ID of the added contact.
            message (str): A message describing the result of the addition attempt.
        """
        if user_name in self.user_map:
            return {"error": f"User name '{user_name}' already exists."}
        self.user_count += 1
        user_id = f"USR{str(self.user_count).zfill(3)}"
        if user_id in self.user_map.values():
            return {"error": f"User ID '{user_id}' already exists."}
        self.user_map[user_name] = user_id
        return {
            "added_status": True,
            "user_id": user_id,
            "message": f"Contact '{user_name}' added successfully.",
        }

    def search_messages(
        self, keyword: str
    ) -> Dict[str, Union[List[Dict[str, Union[str, List[str]]]], str]]:
        """
        Search for messages containing a specific keyword.
        Args:
            keyword (str): The keyword to search for in messages.
        Returns:
            results (List[Dict[str, Union[str, List[str]]]]): List of dictionaries containing matching messages.
                Each dictionary has keys:
                - sender_id (str): The ID of the user who sent the message.
                - receiver_id (str): The ID of the user who received the message.
                - messages (List[str]): List of messages containing the keyword.
        """
        if not self.current_user:
            return {"error": "No user is currently logged in."}
        keyword_lower = keyword.lower()
        results = []
        # Iterate through the inbox to search for the keyword in messages
        for message_id, message_data in self.inbox.items():
            # Check if the current user is either the sender or receiver
            if (
                message_data["sender_id"] == self.current_user
                or message_data["receiver_id"] == self.current_user
            ):
                # Check if the message contains the keyword (case-insensitive)
                if keyword_lower in message_data["message"].lower():
                    results.append(
                        {
                            "sender_id": message_data["sender_id"],
                            "receiver_id": message_data["receiver_id"],
                            "message": message_data["message"],
                        }
                    )
        return {"results": results}

    def get_message_stats(self) -> Dict[str, Union[Dict[str, int], str]]:
        """
        Get statistics about messages for the current user.
        Returns:
            stats (Dict[str, int]): Dictionary containing message statistics.
                - sent_count (int): Number of messages sent by the current user.
                - received_count (int): Number of messages received by the current user.
                - total_contacts (int): Total number of contacts the user has interacted with.
        """
        if not self.current_user:
            return {"error": "No user is currently logged in."}
        sent_count = 0
        received_count = 0
        contacts = set()
        # Loop through the inbox to calculate stats
        for message_id, message_data in self.inbox.items():
            if message_data["sender_id"] == self.current_user:
                sent_count += 1
                contacts.add(message_data["receiver_id"])
            if message_data["receiver_id"] == self.current_user:
                received_count += 1
                contacts.add(message_data["sender_id"])
        total_contacts = len(contacts)
        return {
            "stats": {
                "sent_count": sent_count,
                "received_count": received_count,
                "total_contacts": total_contacts,
            }
        }
