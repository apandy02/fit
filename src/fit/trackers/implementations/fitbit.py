import datetime
import logging
from typing import Any

import httpx

from fit.trackers.base import FitnessTracker, FitnessTrackerClient


class FitbitAppClient(FitnessTrackerClient):
    """
    A PKCE-capable client for Fitbit.
    """

    base_url = "https://www.fitbit.com/oauth2/authorize"
    token_url = "https://api.fitbit.com/oauth2/token"
    info_url = "https://api.fitbit.com/1/user/-/profile.json"

    @property
    def tracker_type(self) -> str:
        return "fitbit"

    def login_link(
        self, redirect_uri: str, state: str = None
    ) -> str:
        """Create the Fitbit login link with PKCE parameters."""
        if not state:
            state = self.state

        extra_params = {
            "code_challenge": self.code_challenge,
            "code_challenge_method": "S256",
        }

        auth_url = self.prepare_request_uri(
            self.base_url,
            redirect_uri=redirect_uri,
            scope=self.scope,
            state=state,
            **extra_params,
        )
        return auth_url

    def parse_response(self, code: str, redirect_uri: str) -> None:
        """
        Exchange the code for an access token, including the code_verifier.
        """
        data = {
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": self.client_id,
            "grant_type": "authorization_code",
            "code_verifier": self.code_verifier,
        }
        r = httpx.post(self.token_url, data=data)
        r.raise_for_status()
        self.parse_request_body_response(r.text)

    def fetch_access_token(self, code: str, redirect_uri: str) -> None:
        data = {
            "client_id": self.client_id,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
            "code": code,
            "code_verifier": self.code_verifier,
        }
        r = httpx.post(self.token_url, data=data)
        r.raise_for_status()
        self.parse_request_body_response(r.text)
        return self.token

    def get_info(self, token: str = None) -> dict:
        """Fetch user profile info from Fitbit's API."""
        if not token:
            token = self.token["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        resp = httpx.get(self.info_url, headers=headers)
        resp.raise_for_status()
        return resp.json()

    def is_token_valid(self, token: str = None) -> bool:
        """Check if the access token is valid."""
        if not token:
            token = self.token["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        try:
            resp = httpx.get(self.info_url, headers=headers)
            resp.raise_for_status()
            return True
        except httpx.HTTPStatusError as e:
            logging.error(f"Token validation failed: {e}")
            return False

    def retr_info(self, code: str, redirect_uri: str) -> dict:
        """Convenience method to parse token response then fetch user info."""
        self.parse_response(code, redirect_uri)
        info = self.get_info()
        logging.info(f"info: {info}")
        return info

    def retr_id(self, code: str, redirect_uri: str) -> str:
        """Fitbit's user_id is in the profile."""
        profile = self.retr_info(code, redirect_uri)
        logging.info(f"profile: {profile}")
        return profile["user"]["encodedId"]


class Fitbit(FitnessTracker):
    BASE_URL = "https://api.fitbit.com/1/user/-"
    INFO_URL = "https://api.fitbit.com/1/user/-/profile.json"

    def __init__(self, access_token: str):
        self.access_token = access_token
        super().__init__()

    @property
    def tracker_type(self) -> str:
        return "fitbit"

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
            activities_heart = data.get("activities-heart", [])
            if activities_heart:
                return float(
                    activities_heart[0].get("value", {}).get("restingHeartRate", 0)
                )
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
            summary = data.get("summary", {})
            return float(summary.get("caloriesOut", 0))
        except Exception as e:
            logging.error(f"Error fetching calories burned: {e}")
            return 0.0

    def get_daily_sleep(self, day: datetime.date) -> float:
        """Fetch sleep data for a specific day in hours."""
        date_str = day.strftime("%Y-%m-%d")
        endpoint = f"/sleep/date/{date_str}.json"

        try:
            data = self._make_request(endpoint)
            sleep_data = data.get("sleep", [])
            total_minutes = sum(sleep.get("minutesAsleep", 0) for sleep in sleep_data)
            return round(total_minutes / 60.0, 2)

        except Exception as e:
            logging.error(f"Error fetching sleep data: {e}")
            return 0.0

    def get_daily_workouts(self, day: datetime.date) -> list[dict[str, Any]]:
        """Fetch workouts for a specific day."""
        date_str = day.strftime("%Y-%m-%d")
        endpoint = f"/activities/date/{date_str}.json"

        try:
            data = self._make_request(endpoint)
            activities = data.get("activities", [])

            workouts = []
            for activity in activities:
                workout = {
                    "type": activity.get("activityName", "Unknown"),
                    "duration": activity.get("duration", 0),
                    "calories": activity.get("calories", 0),
                    "distance": activity.get("distance", 0),
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
            hrv_data = data.get("hrv", [])
            if hrv_data:
                rmssd = hrv_data[0].get("value", {}).get("dailyRmssd", 0)
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
            intraday_data = data.get("activities-heart-intraday", {}).get("dataset", [])
            return [
                {"time": entry.get("time"), "value": entry.get("value")}
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
            br_data = data.get("br", [])
            if br_data:
                return float(br_data[0].get("value", {}).get("breathingRate", 0))
            return 0.0
        except Exception as e:
            logging.error(f"Error fetching breathing rate data: {e}")
            return 0.0
