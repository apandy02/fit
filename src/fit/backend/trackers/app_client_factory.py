import os

from fit.trackers.implementations.fitbit import FitbitAppClient
from fit.trackers.implementations.whoop import WhoopAppClient


def make_app_client(provider: str, restore_code_verifier: str | None = None):
    if provider == "whoop":
        client = WhoopAppClient(
            client_id=os.environ["WHOOP_CLIENT_ID"],
            scope=os.environ.get("WHOOP_SCOPES", "openid offline_access"),
        )
        client.client_secret = os.environ["WHOOP_CLIENT_SECRET"]
    elif provider == "fitbit":
        client = FitbitAppClient(
            client_id=os.environ["FITBIT_CLIENT_ID"],
            scope=os.environ.get("FITBIT_SCOPES", "activity heartrate sleep profile"),
        )
    else:
        raise ValueError("Unknown provider")
    if restore_code_verifier:
        client.code_verifier = restore_code_verifier
    return client


def extract_provider_user_id(provider: str, profile: dict) -> str:
    if provider == "whoop":
        # basic profile contains user id
        return str(profile.get("user", {}).get("user_id") or profile.get("id") or "")
    if provider == "fitbit":
        return profile["user"]["encodedId"]
    raise ValueError("Unknown provider")


