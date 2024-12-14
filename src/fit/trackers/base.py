from abc import ABC, abstractmethod
import logging


class FitnessTracker(ABC):
    """Abstract base class for fitness trackers."""
    def __init__(self):
        try:
            print("Authenticating...")
            self._authenticate()
        
        except Exception as e:
            logging.error(f"Error authenticating: {e}")

    @abstractmethod
    def resting_heart_rate_today(self) -> float:
        """Fetch the most recent resting heart rate data."""

    @abstractmethod
    def calories_burned_today(self) -> float:
        """Fetch calories burned for the most recent day."""
    
    
    @abstractmethod
    def _authenticate(self):
        pass

