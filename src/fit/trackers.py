from abc import ABC, abstractmethod


class FitnessTracker(ABC):
    """Abstract base class for fitness trackers."""
    def __init__(self):
        try:
            self._authenticate()
        
        except Exception as e:
            print(f"Error authenticating: {e}")

    @abstractmethod
    def resting_heart_rate(self) -> float:
        """Fetch the most recent resting heart rate data."""

    @abstractmethod
    def calories_burned(self) -> float:
        """Fetch calories burned for the most recent day."""
    
    @abstractmethod
    def _authenticate(self):
        pass

