import datetime
import random
from typing import Dict, List, Union, Optional

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

DEFAULT_STATE = {
    "_records": {
        datetime.datetime.now().date(): [
            -1322510522584581004, -2456134008116096979
        ]
    },
    "_events": {
        -1322510522584581004: Event(
                'Coffee daily doze ☕️',
                datetime.datetime.now(),
                datetime.timedelta(seconds=1)
            ),
        -2456134008116096979: Event(
                'Study sesh 📚',
                datetime.datetime.now(),
                datetime.timedelta(hours=2)
            )
    },
    "event_counter": 2,
    "name": None
}


class Event:
    """
    A class representing an event in the Calendar API.
    
    This class provides methods for event modification, including notifying guests and updating status of the event.
    
    Attributes: 
        title (str): The name or title of the event.
        start (datetime.datetime): The starting date and time of the event.
        ttl (datetime.timedelta): The time duration for which the event will last.
        end (datetime.datetime): The calculated end date and time of the event.
        eid (int): A unique identifier of the event, assigned only after adding this event to the Calendar instance.
        _status (str): The current status of the event ('Upcoming', 'Current', or 'Completed').
        _guests (List[str]): A list of guest emails associated with the event.
    
    Methods:
        get_guests(): Returns the guest list for the event.
        get_status(): Returns the current status of the event.
        set_event_id(eid: int): Assigns a unique event identifier after adding the event to the calendar.
        update_status(): Updates the event's status based on the current date and time.
        add_guest(guest_contact: str): Adds a guest's email to the event's guest list.
        remove_guest(guest_contact: str): Removes a guest's email from the guest list if present.
        notify_guests(): Sends notification messages to all guests in the event's guest list.

    """
    def __init__(self, title, start, ttl):
        """
        Initialize an Event instance.
        """
        self.title: str = title
        self.start: datetime.datetime = start
        self.ttl: datetime.timedelta = ttl
        self.end: datetime.datetime = start + ttl
        self.eid: int
        self._status: str = None
        self._guests: List[str] = []
    
    def __str__(self):
        """
        An event description.
        
        Returns:
            title (a string): A title of the events.
        """
        print(f'The event "{self.title}" is starting on {self.start}, and ending on {self.end}.')
        print(f'Note that the event happens on {WEEKDAYS[self.start.weekday()]}.')
        if self.get_guests():
            print(f'Guest list: {self.get_guests()}')
        return f'Status: {self._status}.'
    
    def get_guests(self) -> List[str]:
        return self._guests
    
    def get_status(self) -> str:
        return self._status
    
    def set_event_id(self, eid: int) -> None:
        "Set a unique event identifier after adding it to the Calendar instance."
        self.eid = eid
    
    def update_status(self) -> None:
        "Update and assign the event status."
        updated_status = 'Current'
        if datetime.datetime.now() < self.start:
            updated_status = 'Upcoming'
        elif datetime.datetime.now() > self.end:
            updated_status = 'Completed'
        self._status = updated_status
    
    def add_guest(self, guest_contact) -> None:
        "Add guest email to the guests list."
        assert '@' in guest_contact
        self._guests.append(guest_contact)
    
    def remove_guest(self, guest_contact) -> None:
        assert guest_contact in self._guests
        self._guests.remove(guest_contact)
    
    def notify_guests(self) -> None:
        "Notify guests about the upcoming event or any event changes."
        for guest_contact in self.get_guests():
            print(f'The invite was succesfully sent to {guest_contact}!')


class Calendar:
    """
    A calendar system that manages the scheduling and tracking of events, allowing the user to add, cancel, and update events.

    Attributes:
        name (Optional[str]): The owner's name or identifier for the calendar.
        _records (Dict): A dictionary storing event records by date, mapping to lists of event IDs.
        _events (Dict): A dictionary of scheduled events, stored by their unique IDs.
        event_counter (int): The total count of events scheduled in the calendar.

    Methods:
        schedule_event(event: Event, eid: Optional[int] = None): Add an Event instance into the calendar.
        cancel_event(eid: int): Remove a specified event from the calendar.
        update(): Update status of all events with respect to the current time.
        event_history(): Return how many events have been scheduled so far.
        get_upcoming_events(): Return all upcoming events.
        get_current_events(): Return event(s) that is happening right now.
    """
    def __init__(self, name: Optional[str] = None):
        self.name: Optional[str] = name
        self._records: Dict = {}
        self._events: Dict = {}
        self.event_counter: int = 0
        
    def __str__(self) -> str:
        """
        Print the calendar owner's name and all the scheduled events by increasing event date.
        
        Returns:
            current date (a string): Current date in '<month> <day>, <year>' format
        """
        print(f'This is a personal calendar of {self.name}.\n')
        print(f'The current list of events:\n')
        if not self._events:
            print('(empty)')
        else:
            for date in sorted(self._records):
                if not self._records[date]:
                    continue
                print(date.strftime("%B %d, %Y"))
                print('###################')
                for eid in self._records[date]:
                    print(self._events[eid])
                    print('###################')
                print('\n')
        return datetime.datetime.now().strftime("%B %d, %Y")
        
    def schedule_event(self, event: Event, eid: Optional[int] = None) -> None:
        """
        Add an Event instance into the calendar.
        
        The structure of the calendar's:
            records:
                date1: {
                    event1_id, ..., eventN_id
                },
                ...
            events: {
                event1_id: <associated Event instance>,
                ...
            }
        """
        if not eid:
            eid = hash(event.title + str(random.random()))
        event.set_event_id(eid)
        self._events[eid] = event
        if event.start.date() in self._records:
            self._records[event.start.date()].append(eid)
        else:
            self._records[event.start.date()] = [eid]
        self.event_counter += 1    
        
    def cancel_event(self, eid: int) -> bool:
        """
        Remove a specified event from the calendar.
        
        Returns:
            canceled_event (bool): return True if successfully canceled the event; False otherwise.
        """
        if eid not in self._events:
            return False
        event_date = self._events[eid].start.date()
        self._records[event_date].remove(eid)
        del self._events[eid]
        return True
        
    def update(self) -> None:
        """
        Update status of all events with respect to the current time.
        """
        for eid in self._events:
            self._events[eid].update_status()
    
    def event_history(self) -> int:
        """
        Return how many events have been scheduled so far.
        
        Returns:
            event_counter (int): number of events that have ever been added.
        """
        print(f'You had {self.event_counter} events scheduled so far.')
        return self.event_counter
        
    def get_upcoming_events(self) -> Union[Event, List[str]]:
        """
        Return all upcoming events.
        
        Returns:
            upcoming_eids (Union[Event, List[str]]): an event or a list of events' IDs in the calendar that has not started.
        """
        upcoming_eids = []
        for eid in self._events:
            if self._events[eid].get_status() == 'Upcoming':
                upcoming_eids.append(eid)
        if len(upcoming_eids) == 1:
            print(self._events[upcoming_eids[0]])
            return upcoming_eids[0]
        return upcoming_eids
    
    def get_current_events(self) -> Union[Event, List[Event]]:
        """
        Return event(s) that is happening right now.
        
        Returns:
            current_eids (Union[Event, List[str]]): an event or a list of events' IDs in the calendar that are happening right now.
        """
        current_eids = []
        for eid in self._events:
            if self._events[eid].get_status() == 'Current':
                current_eids.append(eid)
        if len(current_eids) == 1:
            print(self._events[current_eids[0]])
            return current_eids[0]
        return current_eids
