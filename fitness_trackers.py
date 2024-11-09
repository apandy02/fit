from abc import ABC, abstractmethod

class FitnessTracker(ABC):
    """Abstract base class for fitness trackers."""
    def __init__(self):
        try:
            self._authenticate()
        
        except Exception as e:
            print(f"Error authenticating: {e}")

    @abstractmethod
    def _authenticate(self):
        pass

    @abstractmethod
    def resting_heart_rate(self):
        """Fetch the resting heart rate data."""

    @abstractmethod
    def calories_burned(self):
        """Fetch the calories burned data."""