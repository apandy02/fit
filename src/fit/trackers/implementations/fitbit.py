import base64
import datetime
import hashlib
import logging
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
        if scope is None: 
            scope = self.SCOPE
        if state is None: 
            state = self.state

        extra_params = {
            "code": self.code_challenge,
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
        # 

        r = httpx.post(self.token_url, data=data)
        r.raise_for_status()
        self.parse_request_body_response(r.text)
        return self.token 

    def get_info(self, token=None):
        """Fetch user profile info from Fitbit's API."""
        if token is None:
            token = self.token["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
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
            logging.error(f"Token validation failed: {e}")
            return False

    def retr_info(self, code, redirect_uri):
        """Convenience method to parse token response then fetch user info."""
        self.parse_response(code, redirect_uri)
        info = self.get_info()
        logging.info(f"info: {info}")
        return info

    def retr_id(self, code, redirect_uri):
        """Fitbit's user_id is in the profile."""
        profile = self.retr_info(code, redirect_uri)
        logging.info(f"profile: {profile}")
        return profile["user"]["encodedId"]  # Or whichever field is your 'id'


class Fitbit(FitnessTracker):
    SCOPE = ["activity", "heartrate", "profile", "sleep", "oxygen_saturation", "respiratory_rate"]
    BASE_URL = "https://api.fitbit.com/1/user/-"
    INFO_URL = "https://api.fitbit.com/1/user/-/profile.json"

    def __init__(self, access_token: str):
        self.access_token = access_token
        super().__init__()

    def _authenticate(self) -> None:
        if not self.is_token_valid():
            raise Exception("Fitbit authentication failed")

    def is_token_valid(self) -> bool:
        """Check if the access token is valid."""
        headers = {"Authorization": f"Bearer {self.access_token}"}
        try:
            resp = httpx.get(self.INFO_URL, headers=headers)
            resp.raise_for_status()
            return True
        except httpx.HTTPStatusError as e:
            logging.error(f"Token validation failed: {e}")
            return False

    def _make_request(self, endpoint: str) -> dict:
        """Helper method to make authenticated requests to Fitbit API"""
        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = httpx.get(f"{self.BASE_URL}{endpoint}", headers=headers)
        response.raise_for_status()
        return response.json()

    def get_daily_resting_heart_rate(self, day: datetime.date) -> float:
        """Fetch the resting heart rate data for a specific day."""
        date_str = day.strftime("%Y-%m-%d")
        endpoint = f"/activities/heart/date/{date_str}/1d/1min.json"
        
        try:
            data = self._make_request(endpoint)
            logging.info(f"data: {data}")
            activities_heart = data.get('activities-heart', [])
            if activities_heart:
                return float(activities_heart[0].get('value', {}).get('restingHeartRate', 0))
            return 0.0
        except Exception as e:
            logging.error(f"Error fetching resting heart rate: {e}")
            return 0.0

    def get_daily_calories_burned(self, day: datetime.date) -> float:
        """Fetch calories burned for a specific day."""
        date_str = day.strftime("%Y-%m-%d")
        endpoint = f"/activities/date/{date_str}.json"
        
        try:
            data = self._make_request(endpoint)
            summary = data.get('summary', {})
            return float(summary.get('caloriesOut', 0))
        except Exception as e:
            logging.error(f"Error fetching calories burned: {e}")
            return 0.0

    def get_daily_sleep(self, day: datetime.date) -> float:
        """Fetch sleep data for a specific day in hours."""
        date_str = day.strftime("%Y-%m-%d")
        endpoint = f"/sleep/date/{date_str}.json"
        
        try:
            data = self._make_request(endpoint)
            sleep_data = data.get('sleep', [])
            total_minutes = sum(
                sleep.get('minutesAsleep', 0) 
                for sleep in sleep_data
            )
            return round(total_minutes / 60.0, 2)  # Convert to hours
        except Exception as e:
            logging.error(f"Error fetching sleep data: {e}")
            return 0.0

    def get_daily_workouts(self, day: datetime.date) -> list[dict[str, Any]]:
        """Fetch workouts for a specific day."""
        date_str = day.strftime("%Y-%m-%d")
        endpoint = f"/activities/date/{date_str}.json"
        
        try:
            data = self._make_request(endpoint)
            activities = data.get('activities', [])
            
            workouts = []
            for activity in activities:
                workout = {
                    "type": activity.get('activityName', 'Unknown'),
                    "duration": round(activity.get('duration', 0) / 60000, 2),  # Convert from milliseconds to minutes
                    "calories": activity.get('calories', 0),
                    "distance": round(activity.get('distance', 0) * 1.60934, 2)  # Convert miles to km
                }
                workouts.append(workout)
            return workouts
        except Exception as e:
            logging.error(f"Error fetching workout data: {e}")
            return []

    def get_daily_hrv(self, day: datetime.date) -> float:
        """Fetch HRV data for a specific day."""
        date_str = day.strftime("%Y-%m-%d")
        endpoint = f"/hrv/date/{date_str}.json"
        
        try:
            data = self._make_request(endpoint)
            hrv_data = data.get('hrv', [])
            if hrv_data:
                # Get the daily rmssd value
                rmssd = hrv_data[0].get('value', {}).get('dailyRmssd', 0)
                return float(rmssd)
            return 0.0
        except Exception as e:
            logging.error(f"Error fetching HRV data: {e}")
            return 0.0

    def get_intraday_heart_rate(self, day: datetime.date) -> list[dict[str, Any]]:
        """Fetch intraday heart rate data with 1-minute detail."""
        date_str = day.strftime("%Y-%m-%d")
        endpoint = f"/activities/heart/date/{date_str}/1d/1min.json"
        
        try:
            data = self._make_request(endpoint)
            intraday_data = data.get('activities-heart-intraday', {}).get('dataset', [])
            return [
                {
                    "time": entry.get('time'),
                    "value": entry.get('value')
                }
                for entry in intraday_data
            ]
        except Exception as e:
            logging.error(f"Error fetching intraday heart rate data: {e}")
            return []

    def get_breathing_rate(self, day: datetime.date) -> float:
        """Fetch breathing rate data for a specific day."""
        date_str = day.strftime("%Y-%m-%d")
        endpoint = f"/br/date/{date_str}.json"
        
        try:
            data = self._make_request(endpoint)
            br_data = data.get('br', [])
            if br_data:
                return float(br_data[0].get('value', {}).get('breathingRate', 0))
            return 0.0
        except Exception as e:
            logging.error(f"Error fetching breathing rate data: {e}")
            return 0.0
