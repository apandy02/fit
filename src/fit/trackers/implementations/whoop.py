import datetime
import json
import os
from typing import Any

from authlib.common.urls import extract_params
from authlib.integrations.requests_client import OAuth2Session

from fit.trackers.base import FitnessTracker
from fit.utils.conversions import kj_to_kcal

json_path = os.path.join(os.path.dirname(__file__), "config/whoop_sports.json")

with open(json_path, "r") as f:
    SPORTS_MAP = json.load(f)["sports"]

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

    def _authenticate(self) -> None:
            """Authenticate OAuth2Session by fetching token.
        
            If `user_id` is `None`, it will be set according to the `user_id` returned with
            the token.

            Raises:
                requests.exceptions.HTTPError: If authentication fails due to invalid credentials
                ValueError: If user ID cannot be retrieved from token response
            """
            try:
                self._session.fetch_token(
                    url=f"{self.AUTH_URL}/oauth/token", 
                    username=self._username,
                    password=self._password,
                    grant_type="password",
                )
            except Exception as e:
                raise RuntimeError(f"Failed to authenticate with Whoop: {str(e)}")

            if not self.user_id:
                user_id = self._session.token.get("user", {}).get("id")
                if not user_id:
                    raise ValueError("Could not retrieve user ID from authentication response")
                self.user_id = str(user_id)

    def _auth_password_json(self, _client, _method, uri, headers, body):
        body = json.dumps(dict(extract_params(body)))
        headers["Content-Type"] = "application/json"
        return uri, headers, body
    
    def get_daily_resting_heart_rate(self, day: datetime.date) -> float:
        cycle_dict = self._max_overlap_cycle(day=day, cycles=self._get_cycles_for_day(day))
        cycle_id = cycle_dict["id"]
        recovery_dict = self.get_recovery(cycle_id)
        return recovery_dict["score"]["resting_heart_rate"]

    def get_daily_calories_burned(self, day: datetime.date) -> float:
        cycle_dict = self._max_overlap_cycle(day=day, cycles=self._get_cycles_for_day(day))
        if cycle_dict is None:
            raise ValueError(f"No cycle found for day {day}")
        
        calories = kj_to_kcal(cycle_dict["score"]["kilojoule"])
        return calories

    def get_daily_recovery(self, day: datetime.date) -> float:
        start_dt = datetime.datetime.combine(day, datetime.time.min)
        end_dt = datetime.datetime.combine(day, datetime.time.max)
        return self._get_recovery_collection(start_date=start_dt, end_date=end_dt)
    
    def get_daily_workouts(self, day: datetime.date) -> list[dict[str, Any]]:
        """Get all workouts for a given day.
        
        Args:
            day (datetime.date): The date to get workouts for.
        
        Returns:
            list[dict[str, Any]]: A list of workout dictionaries.
        """
        start_dt = datetime.datetime.combine(day, datetime.time.min)
        end_dt = datetime.datetime.combine(day, datetime.time.max)
        workouts = self._get_workout_collection(start_date=start_dt, end_date=end_dt)
        for workout in workouts:
            workout["sport"] = SPORTS_MAP[str(workout["sport_id"])]
            if workout["score_state"] == "SCORED":
                workout["score"]["calories"] = kj_to_kcal(workout["score"]["kilojoule"])
        return workouts
    
    def get_daily_sleep(self, day: datetime.date) -> dict[str, Any]:
        """Get all sleep for a given day.
        
        Args:
            day (datetime.date): The date to get sleep for.
        
        Returns:
            dict[str, Any]: A dictionary of sleep data.
            Dates are adjusted to the local timezone.
        """
        start_dt = datetime.datetime.combine(day, datetime.time.min)
        end_dt = datetime.datetime.combine(day, datetime.time.max)
        sleep = self._get_sleep_collection(start_date=start_dt, end_date=end_dt)
        
        for sleep_dict in sleep:
            sleep_dict["start"] = datetime.datetime.fromisoformat(sleep_dict["start"].replace("Z", "+00:00"))
            sleep_dict["start"] = self.adjust_datetime_by_offset(sleep_dict["start"], sleep_dict["timezone_offset"])
            sleep_dict["end"] = datetime.datetime.fromisoformat(sleep_dict["end"].replace("Z", "+00:00"))
            sleep_dict["end"] = self.adjust_datetime_by_offset(sleep_dict["end"], sleep_dict["timezone_offset"])
        
        return sleep

    def _get_cycles_for_day(self, day: datetime.date) -> list[dict[str, Any]]:
        start_dt = datetime.datetime.combine(day, datetime.time.min)
        end_dt = datetime.datetime.combine(day, datetime.time.max)
        return self._get_cycle_collection(start_date=start_dt, end_date=end_dt)
    
    def get_cycle_for_day(self, day: datetime.date) -> dict[str, Any]:
        """
        Get the cycle for a given day.
        
        Args:
            day (datetime.date): The date to get the cycle for.
        
        Returns:
            dict[str, Any]: A dictionary of cycle data.
        """
        return self._max_overlap_cycle(day=day, cycles=self._get_cycles_for_day(day))


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

    def _get_cycle_collection(
        self,
        start_date: datetime.date,
        end_date: datetime.date,
    ) -> list[dict[str, Any]]:
        """Make request to Get Cycle Collection endpoint.

        Get all physiological cycles for a user. Results are sorted by start time in
        descending order.

        Returns:
            list[dict[str, Any]]: Response JSON data loaded into an object. Example:
                [
                    {
                        "id": 93845,
                        "user_id": 10129,
                        "created_at": "2022-04-24T11:25:44.774Z",
                        "updated_at": "2022-04-24T14:25:44.774Z",
                        "start": "2022-04-24T02:25:44.774Z",
                        "end": "2022-04-24T10:25:44.774Z",
                        "timezone_offset": "-05:00",
                        "score_state": "SCORED",
                        "score": {
                            "strain": 5.2951527,
                            "kilojoule": 8288.297,
                            "average_heart_rate": 68,
                            "max_heart_rate": 141
                        }
                    },
                    ...
                ]
        """
        start = start_date.isoformat() + "Z"
        end = end_date.isoformat(timespec="seconds") + "Z"
        return self._make_paginated_request(
            method="GET",
            url_slug="v1/cycle",
            params={"start": start, "end": end, "limit": 25},
        )
    
    def _get_recovery_collection(
        self,
        start_date: datetime.date,
        end_date: datetime.date,
    ) -> list[dict[str, Any]]:
        start = start_date.isoformat() + "Z"
        end = end_date.isoformat(timespec="seconds") + "Z"
        return self._make_paginated_request(
            method="GET",
            url_slug="v1/recovery",
            params={"start": start, "end": end, "limit": 25},
        )
    
    def _get_workout_collection(
        self,
        start_date: datetime.date,
        end_date: datetime.date,
    ) -> list[dict[str, Any]]:
        """Make request to Get Cycle Collection endpoint.

        Get all physiological cycles for a user. Results are sorted by start time in
        descending order.

        Returns:
            list[dict[str, Any]]: Response JSON data loaded into an object. Example:
                [
                    {
                        "id": 1043,
                        "user_id": 9012,
                        "created_at": "2022-04-24T11:25:44.774Z",
                        "updated_at": "2022-04-24T14:25:44.774Z",
                        "start": "2022-04-24T02:25:44.774Z",
                        "end": "2022-04-24T10:25:44.774Z",
                        "timezone_offset": "-05:00",
                        "sport_id": 1,
                        "score_state": "SCORED",
                        "score": {
                            "strain": 8.2463,
                            "average_heart_rate": 123,
                            "max_heart_rate": 146,
                            "kilojoule": 1569.34033203125,
                            "percent_recorded": 100,
                            "distance_meter": 1772.77035916,
                            "altitude_gain_meter": 46.64384460449,
                            "altitude_change_meter": -0.781372010707855,
                        "zone_duration": {}
                    }
                    ...
                ]
        """
        start = start_date.isoformat() + "Z"
        end = end_date.isoformat(timespec="seconds") + "Z"
        return self._make_paginated_request(
            method="GET",
            url_slug="v1/activity/workout",
            params={"start": start, "end": end, "limit": 25},
        )
    
    def _get_sleep_collection(
        self,
        start_date: datetime.date,
        end_date: datetime.date,
    ) -> list[dict[str, Any]]:
        start = start_date.isoformat() + "Z"
        end = end_date.isoformat(timespec="seconds") + "Z"
        return self._make_paginated_request(
            method="GET",
            url_slug="v1/activity/sleep",
            params={"start": start, "end": end, "limit": 25},
        )
    
    def _make_paginated_request(
        self, method, url_slug, **kwargs
    ) -> list[dict[str, Any]]:
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

            if next_token := response["next_token"]:
                params["nextToken"] = next_token
            else:
                break

        return response_data
    
    def _max_overlap_cycle(self, day: datetime.date, cycles: list[dict[str, Any]]) -> dict[str, Any]:
        if len(cycles) == 1:
            return cycles[0]
        
        max_overlap = 0
        cycle_dict = None
        
        day_start = datetime.datetime.combine(day, datetime.time.min).astimezone(datetime.timezone.utc)
        day_end = datetime.datetime.combine(day, datetime.time.max).astimezone(datetime.timezone.utc)

        for cycle in cycles:
            cycle_start = datetime.datetime.fromisoformat(cycle["start"].replace("Z", "+00:00"))
            cycle_start = self.adjust_datetime_by_offset(cycle_start, cycle["timezone_offset"])            
            
            if "end" not in cycle or cycle["end"] is None:
                return cycle # if no end, then it's the current cycle. TODO: improve the fault tolerance here"""
            
            cycle_end = datetime.datetime.fromisoformat(cycle["end"].replace("Z", "+00:00"))
            cycle_end = self.adjust_datetime_by_offset(cycle_end, cycle["timezone_offset"])
            overlap_start = max(day_start, cycle_start)
            overlap_end = min(day_end, cycle_end)
            
            if overlap_end > overlap_start:  # If there is overlap
                overlap_duration = (overlap_end - overlap_start).total_seconds()
                if overlap_duration > max_overlap:
                    max_overlap = overlap_duration
                    cycle_dict = cycle
        
        return cycle_dict
    
    def adjust_datetime_by_offset(self, dt, offset_str):
        """Adjusts a datetime object by a timezone offset string (e.g., '-5:00')."""
        hours, minutes = map(int, offset_str.split(':'))
        offset_sign = -1 if hours < 0 else 1
        offset = datetime.timedelta(hours=abs(hours), minutes=abs(minutes)) * offset_sign
        return dt + offset
