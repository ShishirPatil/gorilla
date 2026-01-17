from typing import Dict, List, Union, Optional
from datetime import datetime

class ReadingManager:
    """
    This class is the Reading Manager API, which tracks reading progress and related statistics.
    """

    def __init__(self):
        """
        Initialize the ReadingManager instance.
        """
        self.reading_entries: List[Dict[str, Union[str, int]]] = []
        self.total_pages_read: int = 0
        self.reading_sessions: List[Dict[str, Union[str, float]]] = []
        self.daily_reading_goal: Optional[int] = None
        self.current_session_start: Optional[datetime] = None

    def add_book(self, title: str, author: str, total_pages: int) -> Dict[str, str]:
        """
        Add a book to the reading list.

        Args:
            title (str): Title of the book.
            author (str): Author of the book.
            total_pages (int): Total number of pages in the book.

        Returns:
            result (Dict[str, str]): Book added confirmation message.
        """
        if total_pages <= 0:
            return {"error": "Total pages must be greater than zero."}
        
        self.reading_entries.append({"title": title, "author": author, "total_pages": total_pages, "pages_read": 0})
        return {"result": f"Added '{title}' by {author} with {total_pages} total pages."}

    def create_reading_goal(self, pages: int) -> Dict[str, str]:
        """
        Set a specific reading goal in pages.

        Args:
            pages (int): The target number of pages to read.

        Returns:
            result (Dict[str, str]): Goal created confirmation message.
        """
        if pages <= 0:
            return {"error": "Reading goal must be greater than zero."}

        self.daily_reading_goal = pages
        return {"result": f"Daily reading goal set to {pages} pages."}

    def pages_read(self, pages: int) -> Dict[str, str]:
        """
        Log the number of pages read in the current session.

        Args:
            pages (int): Number of pages read.

        Returns:
            result (Dict[str, str]): Pages logged confirmation message.
        """
        if pages <= 0:
            return {"error": "Pages read must be greater than zero."}
        
        self.total_pages_read += pages
        for entry in self.reading_entries:
            if entry['pages_read'] + pages <= entry['total_pages']:
                entry['pages_read'] += pages
                break

        return {"result": f"Logged {pages} pages read."}

    def start_reading_session(self) -> Dict[str, str]:
        """
        Start a new reading session.

        Returns:
            result (Dict[str, str]): Session started message.
        """
        self.current_session_start = datetime.now()
        return {"result": "Reading session has started."}

    def end_reading_session(self) -> Dict[str, Union[str, float]]:
        """
        End the current reading session and log the duration.

        Returns:
            result (Dict[str, Union[str, float]]): Duration of the session in minutes.
        """
        if not self.current_session_start:
            return {"error": "No active reading session."}

        session_end_time = datetime.now()
        duration = (session_end_time - self.current_session_start).total_seconds() / 60
        self.current_session_start = None
        self.reading_sessions.append({"duration": duration})
        return {"result": f"Reading session ended. Duration: {duration:.2f} minutes."}

    def calculate_reading_speed(self) -> Optional[float]:
        """
        Calculate reading speed in pages per minute.

        Returns:
            speed (Optional[float]): Pages read per minute, or None if no session occurred.
        """
        if not self.reading_sessions:
            return None

        total_duration = sum(session['duration'] for session in self.reading_sessions)
        return self.total_pages_read / total_duration if total_duration > 0 else None

    def pages_left_to_goal(self) -> int:
        """
        Calculate how many pages remain to meet the daily goal.

        Returns:
            remaining (int): Pages remaining to reach the goal.
        """
        if self.daily_reading_goal is None:
            return 0
        return max(0, self.daily_reading_goal - self.total_pages_read)

    def reading_overview(self) -> Dict[str, Union[int, Optional[int]]]:
        """
        Provide an overview of reading progress.

        Returns:
            overview (Dict[str, Union[int, Optional[int]]]): Total pages read and remaining pages to the goal.
        """
        return {
            "total_pages_read": self.total_pages_read,
            "daily_goal": self.daily_reading_goal,
            "remaining_pages": self.pages_left_to_goal(),
            "message": "Your reading progress overview."
        }

    def goal_status(self) -> Dict[str, str]:
        """
        Check if the reading goal has been met.

        Returns:
            status (Dict[str, str]): Goal achievement status.
        """
        status = "met" if self.daily_reading_goal and self.total_pages_read >= self.daily_reading_goal else "not met"
        return {"goal_status": f"Your daily reading goal is {status}."}

    def get_reading_summary(self) -> Dict[str, Union[str, float]]:
        """
        Provide a summary of reading activities.

        Returns:
            summary (Dict[str, Union[str, float]]): Summary of reading progress, sessions, and speed.
        """
        reading_speed = self.calculate_reading_speed()
        return {
            "total_pages_read": self.total_pages_read,
            "total_sessions": len(self.reading_sessions),
            "reading_speed": reading_speed,
            "message": "Summary of your reading progress."
        }
