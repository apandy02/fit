import datetime
import logging
from abc import ABC, abstractmethod
from typing import Any


class FitnessTracker(ABC):
    """
    Abstract base class for fitness trackers.
    This will handle interaction with the tracker-specific
    API to retrieve a standardized set of metrics.
    """

    def __init__(self):
        try:
            logging.info("Authenticating...")
            self._authenticate()
            logging.info("Authentication successful")

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
    def get_daily_sleep(self, day: datetime.date) -> float:
        """Fetch sleep for a given day."""

    @abstractmethod
    def get_daily_workouts(self, day: datetime.date) -> list[dict[str, Any]]:
        """Fetch workouts for a given day."""

    @abstractmethod
    def get_daily_hrv(self, day: datetime.date) -> float:
        """Fetch hrv for a given day."""

    @abstractmethod
    def _authenticate(self):
        pass
