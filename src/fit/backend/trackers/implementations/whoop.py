import datetime
import json
import logging
import os
import secrets
from typing import Any

import httpx

from fit.backend.trackers.base import FitnessTracker, FitnessTrackerClient
from fit.utils.conversions import kj_to_kcal

json_path = os.path.join(os.path.dirname(__file__), "config/whoop_sports.json")

with open(json_path, "r") as f:
    SPORTS_MAP = json.load(f)["sports"]

class WhoopAppClient(FitnessTrackerClient):
    """
    A PKCE-capable client for WHOOP.
    """

    base_url = "https://api.prod.whoop.com/oauth/oauth2/auth"
    token_url = "https://api.prod.whoop.com/oauth/oauth2/token"
    info_url = "https://api.prod.whoop.com/developer/v1/user/profile/basic"

    @property
    def tracker_type(self) -> str:
        return "whoop"

    def login_link(self, redirect_uri, state=None):
        """Create the WHOOP login link with PKCE parameters."""
        if state is None:
            state = secrets.token_urlsafe(16)
            self.state = state

        extra_params = {
            "code_challenge": self.code_challenge,
            "code_challenge_method": "S256",
            "state": state,
        }

        auth_url = self.prepare_request_uri(
            self.base_url, redirect_uri=redirect_uri, scope=self.scope, **extra_params
        )
        return auth_url

    def fetch_access_token(self, code, redirect_uri):
        """Exchange the code for an access token, including the PKCE code_verifier."""
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
            "code": code,
            "code_verifier": self.code_verifier,
        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }

        r = httpx.post(self.token_url, data=data, headers=headers)
        r.raise_for_status()
        self.parse_request_body_response(r.text)
        return self.token

    def get_info(self, token=None):
        """Fetch user profile info from WHOOP's API."""
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


class Whoop(FitnessTracker):
    """
    Fitness tracker subclass for WHOOP devices.

    Attributes:
        access_token (str): OAuth2 access token for the WHOOP API.

    Constants:
        SCOPE (list): Required OAuth2 scopes for the WHOOP API.
        BASE_URL (str): Base URL for API requests.
        INFO_URL (str): URL for user profile info.
    """
    BASE_URL = "https://api.prod.whoop.com/developer"
    INFO_URL = "https://api.prod.whoop.com/developer/v1/user/profile/basic"

    def __init__(self, access_token: str):
        """Initialize a Whoop session with OAuth2 access token.

        Args:
            access_token (str): OAuth2 access token for WHOOP API access.
        """
        self.access_token = access_token
        super().__init__()

    @property
    def tracker_type(self) -> str:
        return "whoop"

    def _authenticate(self) -> None:
        if not self.is_token_valid():
            raise Exception("WHOOP authentication failed")

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

    def get_cycle_for_day(self, day: datetime.date) -> dict[str, Any]:
        """
        Get the cycle for a given day.

        Args:
            day (datetime.date): The date to get the cycle for.

        Returns:
            dict[str, Any]: A dictionary of cycle data.
        """
        return self._max_overlap_cycle(day=day, cycles=self._get_cycles_for_day(day))

    def get_daily_resting_heart_rate(self, day: datetime.date) -> float:
        cycle_dict = self._max_overlap_cycle(
            day=day, cycles=self._get_cycles_for_day(day)
        )
        if cycle_dict is None:
            return 0.0
        cycle_id = cycle_dict["id"]
        recovery_dict = self.get_recovery(cycle_id)
        return recovery_dict["score"]["resting_heart_rate"]

    def get_daily_calories_burned(self, day: datetime.date) -> float:
        cycle_dict = self._max_overlap_cycle(
            day=day, cycles=self._get_cycles_for_day(day)
        )
        if cycle_dict is None:
            return 0.0

        calories = kj_to_kcal(cycle_dict["score"]["kilojoule"])
        return calories

    def get_daily_sleep(self, day: datetime.date) -> float:
        start_dt = datetime.datetime.combine(day, datetime.time.min)
        end_dt = datetime.datetime.combine(day, datetime.time.max)
        sleep_data = self._get_sleep_collection(start_date=start_dt, end_date=end_dt)

        if not sleep_data:
            return 0.0

        total_minutes = sum(
            sleep.get("score", {}).get("sleep_duration", 0) for sleep in sleep_data
        )
        return round(total_minutes / 60.0, 2)

    def get_daily_workouts(self, day: datetime.date) -> list[dict[str, Any]]:
        start_dt = datetime.datetime.combine(day, datetime.time.min)
        end_dt = datetime.datetime.combine(day, datetime.time.max)
        workouts = self._get_workout_collection(start_date=start_dt, end_date=end_dt)

        formatted_workouts = []
        for workout in workouts:
            if workout["score_state"] == "SCORED":
                formatted_workout = {
                    "type": SPORTS_MAP.get(str(workout["sport_id"]), "Unknown"),
                    "duration": workout["score"].get("duration", 0),
                    "calories": kj_to_kcal(workout["score"].get("kilojoule", 0)),
                    "distance": workout["score"].get("distance_meter", 0),
                }
                formatted_workouts.append(formatted_workout)
        return formatted_workouts

    def get_daily_hrv(self, day: datetime.date) -> float:
        cycle_dict = self._max_overlap_cycle(
            day=day, cycles=self._get_cycles_for_day(day)
        )
        if cycle_dict is None:
            return 0.0
        cycle_id = cycle_dict["id"]
        recovery_dict = self.get_recovery(cycle_id)
        return float(recovery_dict["score"].get("hrv_rmssd", 0))

    def get_daily_recovery(self, day: datetime.date) -> float:
        cycle_dict = self._max_overlap_cycle(
            day=day, cycles=self._get_cycles_for_day(day)
        )
        if cycle_dict is None:
            return 0.0
        cycle_id = cycle_dict["id"]
        return self.get_recovery(cycle_id)

    def get_recovery(self, cycle_id: str) -> dict[str, Any]:
        """Get recovery data for a specific cycle."""
        return self._make_request(
            method="GET",
            url_slug=f"v1/cycle/{cycle_id}/recovery",
        )

    def _make_request(
        self, method: str, url_slug: str, **kwargs: Any
    ) -> dict[str, Any]:
        """Helper method to make authenticated requests to WHOOP API"""
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self.access_token}"

        response = httpx.request(
            method=method,
            url=f"{self.BASE_URL}/{url_slug}",
            headers=headers,
            **kwargs,
        )
        response.raise_for_status()
        return response.json()

    def _get_cycles_for_day(self, day: datetime.date) -> list[dict[str, Any]]:
        """Get all cycles for a given day."""
        start_dt = datetime.datetime.combine(day, datetime.time.min)
        end_dt = datetime.datetime.combine(day, datetime.time.max)
        return self._get_cycle_collection(start_date=start_dt, end_date=end_dt)

    def _get_cycle_collection(
        self,
        start_date: datetime.datetime,
        end_date: datetime.datetime,
    ) -> list[dict[str, Any]]:
        """Get cycle collection for a date range."""
        start = start_date.isoformat() + "Z"
        end = end_date.isoformat(timespec="seconds") + "Z"
        return self._make_paginated_request(
            method="GET",
            url_slug="v1/cycle",
            params={"start": start, "end": end, "limit": 25},
        )

    def _get_workout_collection(
        self,
        start_date: datetime.datetime,
        end_date: datetime.datetime,
    ) -> list[dict[str, Any]]:
        """Get workout collection for a date range."""
        start = start_date.isoformat() + "Z"
        end = end_date.isoformat(timespec="seconds") + "Z"
        return self._make_paginated_request(
            method="GET",
            url_slug="v1/activity/workout",
            params={"start": start, "end": end, "limit": 25},
        )

    def _get_sleep_collection(
        self,
        start_date: datetime.datetime,
        end_date: datetime.datetime,
    ) -> list[dict[str, Any]]:
        """Get sleep collection for a date range."""
        start = start_date.isoformat() + "Z"
        end = end_date.isoformat(timespec="seconds") + "Z"
        return self._make_paginated_request(
            method="GET",
            url_slug="v1/activity/sleep",
            params={"start": start, "end": end, "limit": 25},
        )

    def _make_paginated_request(
        self, method: str, url_slug: str, **kwargs: Any
    ) -> list[dict[str, Any]]:
        """Make a paginated request to the WHOOP API."""
        params = kwargs.pop("params", {})
        response_data: list[dict[str, Any]] = []

        while True:
            response = self._make_request(
                method=method,
                url_slug=url_slug,
                params=params,
                **kwargs,
            )

            response_data += response["records"]

            if next_token := response.get("next_token"):
                params["nextToken"] = next_token
            else:
                break

        return response_data

    def _max_overlap_cycle(
        self, day: datetime.date, cycles: list[dict[str, Any]]
    ) -> dict[str, Any] | None:
        """
        Find the whoop "cycle" with maximum overlap for a given day.

        Args:
            day (datetime.date): The date to find the cycle for.
            cycles (list[dict[str, Any]]): The list of cycles to search through.

        Returns:
            dict[str, Any] | None: The cycle with maximum overlap.
        """
        if not cycles:
            return None
        if len(cycles) == 1:
            return cycles[0]

        max_overlap = 0
        cycle_dict = None

        day_start = datetime.datetime.combine(day, datetime.time.min).astimezone(
            datetime.timezone.utc
        )
        day_end = datetime.datetime.combine(day, datetime.time.max).astimezone(
            datetime.timezone.utc
        )

        for cycle in cycles:
            cycle_start = datetime.datetime.fromisoformat(
                cycle["start"].replace("Z", "+00:00")
            )
            cycle_start = self.adjust_datetime_by_offset(
                cycle_start, cycle["timezone_offset"]
            )

            if "end" not in cycle or cycle["end"] is None:
                return cycle

            cycle_end = datetime.datetime.fromisoformat(
                cycle["end"].replace("Z", "+00:00")
            )
            cycle_end = self.adjust_datetime_by_offset(
                cycle_end, cycle["timezone_offset"]
            )
            overlap_start = max(day_start, cycle_start)
            overlap_end = min(day_end, cycle_end)

            if overlap_end > overlap_start:
                overlap_duration = (overlap_end - overlap_start).total_seconds()
                if overlap_duration > max_overlap:
                    max_overlap = overlap_duration
                    cycle_dict = cycle

        return cycle_dict

    def adjust_datetime_by_offset(
        self, dt: datetime.datetime, offset_str: str
    ) -> datetime.datetime:
        """Adjusts a datetime object by a timezone offset string (e.g., '-5:00')."""
        hours, minutes = map(int, offset_str.split(":"))
        offset_sign = -1 if hours < 0 else 1
        offset = (
            datetime.timedelta(hours=abs(hours), minutes=abs(minutes)) * offset_sign
        )
        return dt + offset
