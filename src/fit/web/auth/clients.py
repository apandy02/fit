import json
from pathlib import Path
from oauthlib.oauth2 import WebApplicationClient

class _AppClient(WebApplicationClient):
    id_key = 'sub'
    def __init__(self, client_id, client_secret, code=None, scope=None, **kwargs):
        super().__init__(client_id, code=code, scope=scope, **kwargs)
        self.client_secret = client_secret


class FitbitClient(_AppClient):
    base_url = "https://www.fitbit.com/oauth2/authorize"
    token_url = "https://api.fitbit.com/oauth2/token"

    def __init__(self, client_id, client_secret, code=None, scope=None, **kwargs):
        super().__init__(client_id, client_secret, code=code, scope=scope, **kwargs)

    @classmethod
    def from_file(cls, fname, code=None, scope=None, **kwargs):
        cred = Path(fname).read_json()['web']
        return cls(cred['client_id'], client_secret=cred['client_secret'], code=code, scope=scope, **kwargs)

fitbit_config_path = Path(__file__).parent / 'config' / 'fitbit_config.json'

with open(fitbit_config_path, 'r') as f:
    config = json.load(f)

print(config)
fitbit_client_oauth = FitbitClient(
    client_id=config['web']['client_id'],
    client_secret=config['web']['client_secret'],
    scope=["activity", "heartrate", "profile"], 
    redirect_uri=config['web']['redirect_uri']
)

print(fitbit_client_oauth.__dir__())