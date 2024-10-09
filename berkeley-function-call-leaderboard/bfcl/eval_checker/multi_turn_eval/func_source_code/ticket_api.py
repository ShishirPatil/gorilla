from typing import Dict, List, Optional, Union


class TicketAPI:
    """
    A class representing the Ticket API for managing support tickets.

    This class provides methods for creating, retrieving, and managing
    support tickets within a ticketing system. It maintains a queue of
    tickets and handles ticket-related operations such as creation,
    status updates, and retrieval.

    Attributes:
        ticket_queue (List[Dict[str, Union[int, str]]]): A list of ticket dictionaries.
        ticket_counter (int): A counter for generating unique ticket IDs.
        current_user (Optional[str]): The currently authenticated user.
    """

    def __init__(self):
        """
        Initialize the TicketAPI instance.
        """
        self.ticket_queue: List[Dict[str, Union[int, str]]] = []
        self.ticket_counter: int = 1
        self.current_user: Optional[str] = None

    def _load_scenario(self, scenario: dict, long_context=False) -> None:
        """
        Load a scenario into the ticket queue.

        Args:
            scenario (dict): A dictionary containing ticket data.
        """
        self.ticket_queue = scenario.get("ticket_queue", [])
        self.ticket_counter = scenario.get("ticket_counter", 1)
        self.current_user = scenario.get("current_user", None)

    def create_ticket(
        self, title: str, description: str = "", priority: int = 1
    ) -> Dict[str, Union[int, str]]:
        """
        Create a ticket in the system and queue it.

        Args:
            title (str): Title of the ticket.
            description (str): Description of the ticket. Defaults to an empty string.
            priority (int): Priority of the ticket, from 1 to 5. Defaults to 1.

        Returns:
            ticket (Dict[str, str]): Created ticket object.
                id (int): Unique identifier of the ticket.
                title (str): Title of the ticket.
                description (str): Description of the ticket.
                status (str): Current status of the ticket.
                priority (int): Priority level of the ticket.
        """
        if not self.current_user:
            return {"error": "User not authenticated. Please log in to create a ticket."}
        if priority < 1 or priority > 5:
            return {"error": "Invalid priority. Priority must be between 1 and 5."}
        ticket = {
            "id": self.ticket_counter,
            "title": title,
            "description": description,
            "status": "Open",
            "priority": priority,
            "created_by": self.current_user,
        }
        self.ticket_queue.append(ticket)
        self.ticket_counter += 1
        return ticket

    def get_ticket(self, ticket_id: int) -> Dict[str, Union[int, str]]:
        """
        Get a specific ticket by its ID.

        Args:
            ticket_id (int): ID of the ticket to retrieve.

        Returns:
            ticket (Dict[str, str]): Retrieved ticket object.
                id (int): Unique identifier of the ticket.
                title (str): Title of the ticket.
                description (str): Description of the ticket.
                status (str): Current status of the ticket.
                priority (int): Priority level of the ticket.
                created_by (str): Username of the ticket creator.
        """
        ticket = self.find_ticket(ticket_id)
        if not ticket:
            return {"error": f"Ticket with ID {ticket_id} not found."}
        return ticket

    def close_ticket(self, ticket_id: int) -> Dict[str, str]:
        """
        Close a ticket.

        Args:
            ticket_id (int): ID of the ticket to be closed.

        Returns:
            result (Dict[str, str]): Result of the close operation.
                status (str): Status of the close operation.
        """
        ticket = self.find_ticket(ticket_id)
        if not ticket:
            return {"error": f"Ticket with ID {ticket_id} not found."}
        if ticket["status"] == "Closed":
            return {"error": f"Ticket with ID {ticket_id} is already closed."}
        ticket["status"] = "Closed"
        return {"status": f"Ticket {ticket_id} has been closed successfully."}

    def resolve_ticket(self, ticket_id: int, resolution: str) -> Dict[str, str]:
        """
        Resolve a ticket with a resolution.

        Args:
            ticket_id (int): ID of the ticket to be resolved.
            resolution (str): Resolution details for the ticket.

        Returns:
            result (Dict[str, str]): Result of the resolve operation.
                status (str): Status of the resolve operation.
        """
        ticket = self.find_ticket(ticket_id)
        if not ticket:
            return {"error": f"Ticket with ID {ticket_id} not found."}
        if ticket["status"] == "Resolved":
            return {"error": f"Ticket with ID {ticket_id} is already resolved."}
        ticket["status"] = "Resolved"
        ticket["resolution"] = resolution
        return {"status": f"Ticket {ticket_id} has been resolved successfully."}

    def edit_ticket(
        self, ticket_id: int, updates: Dict[str, Optional[Union[str, int]]]
    ) -> Dict[str, str]:
        """
        Modify the details of an existing ticket.

        Args:
            ticket_id (int): ID of the ticket to be changed.
            updates (Dict[str, str]]): Dictionary containing the fields to be updated.
                                                            Keys can be 'title', 'description', 'status', or 'priority'.
                                                            Values are the new values for these fields.

        Returns:
            result (Dict[str, str]): Result of the update operation.
                status (str): Status of the update operation.
        """
        ticket = self.find_ticket(ticket_id)
        if not ticket:
            return {"error": f"Ticket with ID {ticket_id} not found."}

        valid_fields = {"title", "description", "status", "priority"}
        invalid_fields = set(updates.keys()) - valid_fields
        if invalid_fields:
            return {"error": f"Invalid fields for update: {', '.join(invalid_fields)}"}

        for key, value in updates.items():
            if value is not None:
                ticket[key] = value

        return {"status": f"Ticket {ticket_id} has been updated successfully."}

    def find_ticket(self, ticket_id: int) -> Optional[Dict[str, Union[int, str]]]:
        """
        Find a ticket by its ID.

        Args:
            ticket_id (int): ID of the ticket to find.

        Returns:
            ticket (Dict[str, str]): Ticket object if found, None otherwise. Optional parameter.
        """
        for ticket in self.ticket_queue:
            if ticket["id"] == ticket_id:
                return ticket
        return None

    def ticket_login(self, username: str, password: str) -> Dict[str, bool]:
        """
        Authenticate a user for ticket system.

        Args:
            username (str): Username of the user.
            password (str): Password of the user.

        Returns:
            result (Dict[str, bool]): Result of the login operation.
                success (bool): True if login was successful, False otherwise.
        """
        # In a real system, you would validate the credentials against a database
        if username and password:  # Simplified authentication
            self.current_user = username
            return {"success": True}
        return {"success": False}

    def logout(self) -> Dict[str, bool]:
        """
        Log out the current user.

        Returns:
            result (Dict[str, bool]): Result of the logout operation.
                success (bool): True if logout was successful, False otherwise.
        """
        if self.current_user:
            self.current_user = None
            return {"success": True}
        return {"success": False}

    def get_user_tickets(
        self, status: Optional[str] = None
    ) -> List[Dict[str, Union[int, str]]]:
        """
        Get all tickets created by the current user, optionally filtered by status.

        Args:
            status (Optional[str]): Status to filter tickets by. If None, return all tickets.

        Returns:
            tickets (List[Dict[str, str]]): List of ticket objects matching the criteria.
        """
        if not self.current_user:
            return [{"error": "User not authenticated. Please log in to view tickets."}]

        user_tickets = [
            ticket
            for ticket in self.ticket_queue
            if ticket["created_by"] == self.current_user
        ]

        if status:
            user_tickets = [
                ticket
                for ticket in user_tickets
                if ticket["status"].lower() == status.lower()
            ]

        return user_tickets
