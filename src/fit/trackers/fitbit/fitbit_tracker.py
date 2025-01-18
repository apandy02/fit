import base64
import datetime
import hashlib
import os
from typing import Any

import httpx
from oauthlib.oauth2 import WebApplicationClient

from fit.trackers.base import FitnessTracker


def make_code_verifier_and_challenge():
    code_verifier = base64.urlsafe_b64encode(os.urandom(64)).decode('utf-8').rstrip('=')
    sha256 = hashlib.sha256(code_verifier.encode('utf-8')).digest()
    code_challenge = base64.urlsafe_b64encode(sha256).decode('utf-8').rstrip('=')
    return code_verifier, code_challenge

class FitbitAppClient(WebApplicationClient):
    """
    A PKCE-capable client for Fitbit.
    """
    base_url = "https://www.fitbit.com/oauth2/authorize"
    token_url = "https://api.fitbit.com/oauth2/token"
    info_url  = "https://api.fitbit.com/1/user/-/profile.json"  # or whichever userinfo you want
    
    def __init__(self, client_id, code=None, scope=None, **kwargs):
        super().__init__(client_id, code=code, scope=scope, **kwargs)
        # Generate or store the PKCE code_verifier/challenge
        self.code_verifier, self.code_challenge = make_code_verifier_and_challenge()
    
    def login_link(self, redirect_uri, scope=None, state=None):
        """Create the Fitbit login link with PKCE parameters."""
        if scope is None: scope = self.scope
        if state is None: state = self.state

        # Build up the extra PKCE query params
        extra_params = {
            "code_challenge": self.code_challenge,
            "code_challenge_method": "S256"
        }

        # Use the built-in method, but pass extra_auth_params for PKCE
        auth_url = self.prepare_request_uri(
            self.base_url,
            redirect_uri=redirect_uri,
            scope=scope,
            state=state,
            **extra_params
        )
        return auth_url

    def parse_response(self, code, redirect_uri):
        """
        Exchange the code for an access token, including the code_verifier.
        """
        data = {
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": self.client_id,
            "grant_type": "authorization_code",
            # PKCE: pass the code_verifier
            "code_verifier": self.code_verifier,
        }
        # If your Fitbit app is registered as a confidential client,
        # you may also have a client_secret – then you'd pass it here:
        #     data["client_secret"] = self.client_secret

        r = httpx.post(self.token_url, data=data)
        r.raise_for_status()
        self.parse_request_body_response(r.text)

    def fetch_access_token(self, code, redirect_uri):
        # Exchange the code for an access token, including the PKCE code_verifier
        data = {
            "client_id": self.client_id,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
            "code": code,
            "code_verifier": self.code_verifier,
        }
        # If your Fitbit app is a confidential client, include client_secret:
        data["client_secret"] = self.client_secret

        r = httpx.post(self.token_url, data=data)
        r.raise_for_status()
        self.parse_request_body_response(r.text)
        return self.token 

    def get_info(self, token=None):
        """Fetch user profile info from Fitbit's API."""
        if token is None:
            token = self.token["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print(f"headers: {headers}")
        resp = httpx.get(self.info_url, headers=headers)
        resp.raise_for_status()
        return resp.json()

    def is_token_valid(self, token=None):
        """Check if the access token is valid."""
        if token is None:
            token = self.token["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        try:
            resp = httpx.get(self.info_url, headers=headers)
            resp.raise_for_status()
            return True
        except httpx.HTTPStatusError as e:
            print(f"Token validation failed: {e}")
            return False

    def retr_info(self, code, redirect_uri):
        """Convenience method to parse token response then fetch user info."""
        self.parse_response(code, redirect_uri)
        info = self.get_info()
        print(f"info: {info}")
        return info

    def retr_id(self, code, redirect_uri):
        """Fitbit's user_id is in the profile."""
        profile = self.retr_info(code, redirect_uri)
        print(f"profile: {profile}")
        return profile["user"]["encodedId"]  # Or whichever field is your 'id'


class FitbitTracker(FitnessTracker):
    SCOPE = ["activity", "heartrate", "profile"]
    def __init__(self, client: FitbitAppClient):
        self.client = client
        super().__init__()

    def _authenticate(self) -> None:
        self.client.is_token_valid()
    
    def get_daily_resting_heart_rate(self, day: datetime.date) -> float:
        """Fetch the most recent resting heart rate data."""
        return 65.0  # Dummy value
    
    def get_daily_calories_burned(self, day: datetime.date) -> float:
        """Fetch calories burned for the most recent day."""
        return 2000.0  # Dummy value
    
    def get_daily_sleep(self, day: datetime.date) -> float:
        """Fetch sleep for a given day."""
        return 7.5  # Dummy value in hours
        
    def get_daily_workouts(self, day: datetime.date) -> list[dict[str, Any]]:
        """Fetch workouts for a given day."""
        return [  # Dummy workout data
            {
                "type": "Running",
                "duration": 30,  # minutes
                "calories": 300,
                "distance": 5.0  # km
            }
        ]
