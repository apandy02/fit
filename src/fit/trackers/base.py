from abc import ABC, abstractmethod
import logging
import datetime

class FitnessTracker(ABC):
    """
    Abstract base class for fitness trackers.
    
    I'm not the biggest fan of abstractions, so let's try and keep the
    responsibilities of this class down to the bare minimum as necessary.
    """
    def __init__(self):
        try:
            print("Authenticating...")
            self._authenticate()
            print("Authentication successful")

        except Exception as e:
            logging.error(f"Error authenticating: {e}")
            raise e

    @abstractmethod
    def get_daily_resting_heart_rate(self, day: datetime.date) -> float:
        """Fetch the most recent resting heart rate data."""

    @abstractmethod
    def get_daily_calories_burned(self, day: datetime.date) -> float:
        """Fetch calories burned for the most recent day."""
    
    @abstractmethod
    def _authenticate(self):
        pass

