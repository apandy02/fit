from fit.trackers.implementations.whoop import Whoop
from fit.trackers.base import FitnessTracker

def get_tracker(tracker_type: str, username: str, password: str) -> FitnessTracker:
    """Return a FitnessTracker instance based on the tracker type"""
    if tracker_type == "whoop":
        return Whoop(username, password)
    # Other trackers go here 
    raise ValueError(f"Invalid tracker type: {tracker_type}")