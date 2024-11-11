from authlib.common.urls import extract_params
from authlib.integrations.requests_client import OAuth2Session
import json
from typing import Any

from fit.trackers.tracker import FitnessTracker
from fit.utils.conversions import kj_to_kcal

class Whoop(FitnessTracker):
    """Fitness tracker subclass for WHOOP devices.

    Attributes:
        session (authlib.OAuth2Session): Requests session for accessing the WHOOP API.
        user_id (str): User ID of the owner of the session. 
    
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
        """Initialize a Whoop session and set up parameters for making requests.
        
        Args:
            username (str): WHOOP account email.
            password (str): WHOOP account password.
        """
        self._username = username
        self._password = password
        self.user_id = ""

        self._session = OAuth2Session(
            token_endpont=f"{self.AUTH_URL}/oauth/token",
            token_endpoint_auth_method="password_json",
        )
        self._session.register_client_auth_method(("password_json", self._auth_password_json))

        super().__init__()
    
    def resting_heart_rate(self) -> float:
        cycle_dict = self._get_current_cycle()
        cycle_id = cycle_dict["id"]
        recovery_dict = self.get_recovery(cycle_id)
        return recovery_dict["score"]["resting_heart_rate"]

    def calories_burned(self) -> float:
        cycle_dict = self._get_current_cycle()
        calories = kj_to_kcal(cycle_dict["score"]["kilojoule"])
        return calories

    def get_recovery(self, cycle_id: str):
        return self._make_request(
            method="GET", url_slug=f"v1/cycle/{cycle_id}/recovery"
        )

    def _authenticate(self) -> None:
        """Authenticate OAuth2Session by fetching token.
    
        If `user_id` is `None`, it will be set according to the `user_id` returned with
        the token.
        """
        self._session.fetch_token(
            url=f"{self.AUTH_URL}/oauth/token",
            username=self._username,
            password=self._password,
            grant_type="password",
        )

        if not self.user_id:
            self.user_id = str(self._session.token.get("user", {}).get("id", ""))

    def _auth_password_json(self, _client, _method, uri, headers, body):
        body = json.dumps(dict(extract_params(body)))
        headers["Content-Type"] = "application/json"
        return uri, headers, body

    def _get_current_cycle(self):
        """Get the current cycle from Whoop API."""
        params = {
            "limit": "1"
        }
        results = self._make_request(
            method="GET",
            url_slug="v1/cycle",
            params=params
        )
        return results['records'][0]
    
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

