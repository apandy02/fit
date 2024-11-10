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
    """
    Make requests to the WHOOP API.

    Attributes:
        session (authlib.OAuth2Session): Requests session for accessing the WHOOP API.
        user_id (str): User ID of the owner of the session. Will default to an empty
            string before the session is authenticated and then replaced by the correct
            user ID once a token is fetched.
    Constants:
        AUTH_URL (str): Base URL for authentication requests.
        REQUEST_URL (str): Base URL for API requests.
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

        self._session = OAuth2Session(
            token_endpont=f"{self.AUTH_URL}/oauth/token",
            token_endpoint_auth_method="password_json",
        )

        self._session.register_client_auth_method(("password_json", self._auth_password_json))

        self.user_id = ""
        super().__init__()

    def _authenticate(self, **kwargs) -> None:
        """Authenticate OAuth2Session by fetching token.
    
        If `user_id` is `None`, it will be set according to the `user_id` returned with
        the token.

        Args:
            kwargs (dict[str, Any], optional): Additional arguments for `fetch_token()`.
        """
        self._session.fetch_token(
            url=f"{self.AUTH_URL}/oauth/token",
            username=self._username,
            password=self._password,
            grant_type="password",
            **kwargs,
        )

        if not self.user_id:
            self.user_id = str(self._session.token.get("user", {}).get("id", ""))

    def _auth_password_json(self, _client, _method, uri, headers, body):
        body = json.dumps(dict(extract_params(body)))
        headers["Content-Type"] = "application/json"

        return uri, headers, body
    
    def _make_request(
        self, method: str, url_slug: str, **kwargs: Any
    ) -> dict[str, Any]:
        response = self._session.request(
            method=method,
            url=f"{self.REQUEST_URL}/{url_slug}",
            **kwargs,
        )

        response.raise_for_status()
        return response.json()
    
    def resting_heart_rate(self):
        pass

    def calories_burned(self):
        pass

    def get_recovery(self, cycle_id: str):
        return self._make_request(
            method="GET", url_slug=f"v1/cycle/{cycle_id}/recovery"
        )
    
    def get_body_measurement(self) -> dict[str, Any]:
        """Make request to Get Body Measurement endpoint.

        Get the user's body measurements.

        Returns:
            dict[str, Any]: Response JSON data loaded into an object. Example:
                {
                    "height_meter": 1.8288,
                    "weight_kilogram": 90.7185,
                    "max_heart_rate": 200
                }
        """
        return self._make_request(method="GET", url_slug="v1/user/measurement/body")

    def get_cycle(self):
        """
        Get the current cycle from Whoop API.

        Returns:
            dict: JSON response containing cycle data
        """
        params = {
            "limit": "1"
        }
        return self._make_request(
            method="GET",
            url_slug="v1/cycle",
            params=params
        )
