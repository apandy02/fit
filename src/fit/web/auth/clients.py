import json
from pathlib import Path

from fit.backend.trackers.implementations.fitbit import FitbitAppClient
from fit.backend.trackers.implementations.whoop import WhoopAppClient

fitbit_config_path = Path(__file__).parent / 'config' / 'fitbit_config.json'

with open(fitbit_config_path, 'r') as f:
    fitbit_config = json.load(f)

fitbit_client_oauth = FitbitAppClient(
    client_id=fitbit_config['client_id'],
    client_secret=fitbit_config['client_secret'],
    scope=["activity", "heartrate", "profile"], 
)

whoop_config_path = Path(__file__).parent / 'config' / 'whoop_config.json'

with open(whoop_config_path, 'r') as f:
    whoop_config = json.load(f)

whoop_client_oauth = WhoopAppClient(
    client_id=whoop_config['client_id'],
    client_secret=whoop_config['client_secret'],
    scope=["offline", "read:recovery", "read:cycles", "read:workout", "read:sleep", "read:profile"], 
)
