from fit.trackers.base import FitnessTracker
from fit.trackers.implementations.fitbit import Fitbit
from fit.trackers.implementations.whoop import Whoop

def tracker_factory(tracker_type: str, access_token: str) -> FitnessTracker:
    """Create a tracker instance using an access token."""
    if tracker_type == "fitbit":
        return Fitbit(access_token)
    elif tracker_type == "whoop":
        return Whoop(access_token)
    raise ValueError(f"Invalid tracker type: {tracker_type}")