from abc import ABC, abstractmethod
from typing import Any

from authlib.common.urls import extract_params
from authlib.integrations.requests_client import OAuth2Session
import json

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


class Whoop(FitnessTracker):
    """Make requests to the WHOOP API.

    Attributes:
        session (authlib.OAuth2Session): Requests session for accessing the WHOOP API.
        user_id (str): User ID of the owner of the session. Will default to an empty
            string before the session is authenticated and then replaced by the correct
            user ID once a token is fetched.

    Raises:
        ValueError: If `start_date` is after `end_date`.
    """
    AUTH_URL = "https://api-7.whoop.com"
    REQUEST_URL = "https://api.prod.whoop.com/developer"

    def __init__(
        self,
        username: str,
        password: str,
    ):
        """
        Initialize an OAuth2 session for making API requests.

        Optionally makes a request to the WHOOP API to acquire an access token.

        Args:
            username (str): WHOOP account email.
            password (str): WHOOP account password.
            kwargs (dict[str, Any], optional): Additional arguments for OAuth2Session.
        """
        self._username = username
        self._password = password

        self.session = OAuth2Session(
            token_endpont=f"{self.AUTH_URL}/oauth/token",
            token_endpoint_auth_method="password_json",
        )

        self.session.register_client_auth_method("password_json", self._auth_password_json)

        self.user_id = ""
        super().__init__()

    
    def _authenticate(self, **kwargs) -> None:
        """Authenticate OAuth2Session by fetching token.

        If `user_id` is `None`, it will be set according to the `user_id` returned with
        the token.

        Args:
            kwargs (dict[str, Any], optional): Additional arguments for `fetch_token()`.
        """
        self.session.fetch_token(
            url=f"{self.AUTH_URL}/oauth/token",
            username=self._username,
            password=self._password,
            grant_type="password",
            **kwargs,
        )

        if not self.user_id:
            self.user_id = str(self.session.token.get("user", {}).get("id", ""))

    def _auth_password_json(self, _client, _method, uri, headers, body):
        body = json.dumps(dict(extract_params(body)))
        headers["Content-Type"] = "application/json"

        return uri, headers, body
    
    def resting_heart_rate(self):
        pass

    def calories_burned(self):
        pass

    def get_recovery(self, cycle_id: str):
        return self._make_request(
            method="GET", url_slug=f"v1/cycle/{cycle_id}/recovery"
        )

    def _get_cycle(self):
        """
        Get the current cycle from Whoop API.

        Returns:
            dict: JSON response containing cycle data
        """
        params = {
            "limit": "1"
        }
        
        response = self.session.get(
            f"{self.API_URL}/developer/v1/cycle",
            params=params
        )

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Received {response.status_code} status from Whoop")

    def _make_request(
        self, method: str, url_slug: str, **kwargs: Any
    ) -> dict[str, Any]:
        response = self.session.request(
            method=method,
            url=f"{self.REQUEST_URL}/{url_slug}",
            **kwargs,
        )

        response.raise_for_status()

        return response.json()