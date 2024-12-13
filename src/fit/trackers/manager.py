import json
import os
from pathlib import Path
from typing import Optional, Dict, Any

from fit.trackers.base import FitnessTracker
from fit.trackers.implementations.whoop import Whoop

SECRETS_PATH = "data/secrets.json"
CONFIG_PATH = "data/config.json"

def create_tracker(tracker_type: str, username: str, password: str) -> FitnessTracker:
    """Create and return a FitnessTracker instance based on the tracker type."""
    if tracker_type == "whoop":
        return Whoop(username, password)
    # Add other tracker types here
    raise ValueError(f"Invalid tracker type: {tracker_type}")

def load_secrets() -> Dict[str, Any]:
    """Load existing secrets if they exist."""
    if os.path.exists(SECRETS_PATH):
        with open(SECRETS_PATH, 'r') as f:
            return json.load(f)
    return {}

def save_secrets(tracker_type: str, username: str, password: str) -> None:
    """Save tracker credentials to secrets file."""
    secrets = load_secrets()
    Path("data").mkdir(exist_ok=True)
    
    secrets[tracker_type] = {
        "username": username,
        "password": password
    }
    
    with open(SECRETS_PATH, 'w') as f:
        json.dump(secrets, f, indent=2)
    os.chmod(SECRETS_PATH, 0o600)  # Read/write for owner only

def load_config() -> Dict[str, Any]:
    """Load config if it exists."""
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)
    return {"active_tracker": None}

def save_config(active_tracker: str) -> None:
    """Save active tracker choice to config file."""
    config = load_config()
    Path("data").mkdir(exist_ok=True)
    config["active_tracker"] = active_tracker
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=2)

def get_active_tracker_type() -> Optional[str]:
    """Return the type of the currently active tracker."""
    config = load_config()
    return config.get("active_tracker")

def get_active_tracker_credentials() -> Optional[Dict[str, str]]:
    """Return the credentials for the active tracker if it exists."""
    active_type = get_active_tracker_type()
    if not active_type:
        return None
    
    secrets = load_secrets()
    return secrets.get(active_type)

def get_active_tracker() -> Optional[FitnessTracker]:
    """Get an instance of the active tracker if one is configured."""
    active_type = get_active_tracker_type()
    if not active_type:
        return None
    
    try:
        secrets = load_secrets()
        if active_type in secrets:
            creds = secrets[active_type]
            return create_tracker(
                active_type,
                creds["username"],
                creds["password"]
            )
    except Exception as e:
        print(f"Failed to load active tracker: {e}")
    return None

def set_active_tracker(tracker_type: str) -> Optional[FitnessTracker]:
    """Set the active tracker and return an instance of it."""
    secrets = load_secrets()
    if tracker_type not in secrets:
        raise ValueError(f"No credentials found for tracker type: {tracker_type}")
    
    save_config(tracker_type)
    return get_active_tracker()