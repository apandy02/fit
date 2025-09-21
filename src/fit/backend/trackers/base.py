import base64
import datetime
import hashlib
import logging
import os
from abc import ABC, abstractmethod
from typing import Any

from oauthlib.oauth2 import WebApplicationClient


class FitnessTrackerClient(WebApplicationClient, ABC):
    """
    Abstract base class for fitness tracker clients.
    This will handle interaction with the tracker-specific
    API to retrieve a standardized set of metrics.
    """

    def __init__(self, client_id, code=None, scope=None, **kwargs):
        super().__init__(client_id, code=code, scope=scope, **kwargs)
        self.code_verifier, self.code_challenge = (
            self.make_code_verifier_and_challenge()
        )

    @property
    @abstractmethod
    def tracker_type(self) -> str:
        pass

    @abstractmethod
    def login_link(self, redirect_uri, state=None):
        pass

    @abstractmethod
    def fetch_access_token(self, code, redirect_uri):
        pass

    @abstractmethod
    def get_info(self, token=None):
        pass

    def make_code_verifier_and_challenge(self):
        code_verifier = (
            base64.urlsafe_b64encode(os.urandom(64)).decode("utf-8").rstrip("=")
        )
        sha256 = hashlib.sha256(code_verifier.encode("utf-8")).digest()
        code_challenge = base64.urlsafe_b64encode(sha256).decode("utf-8").rstrip("=")
        return code_verifier, code_challenge


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

    @property
    @abstractmethod
    def tracker_type(self) -> str:
        pass

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
