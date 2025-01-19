import json
from pathlib import Path

from fit.trackers.implementations.fitbit import FitbitAppClient

fitbit_config_path = Path(__file__).parent / 'config' / 'fitbit_config.json'

with open(fitbit_config_path, 'r') as f:
    config = json.load(f)

fitbit_client_oauth = FitbitAppClient(
    client_id=config['web']['client_id'],
    client_secret=config['web']['client_secret'],
    scope=["activity", "heartrate", "profile"], 
)

print(f"fitbit_client_oauth.__dir__(): {fitbit_client_oauth.__dir__()}")
print(f"{fitbit_client_oauth.redirect_url=}")