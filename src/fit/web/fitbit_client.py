# src/fit/web/fitbit/oauth.py

from pathlib import Path
from oauthlib.oauth2 import WebApplicationClient
import json
# Fitbit credentials
FITBIT_CLIENT_ID = "YOUR_FITBIT_CLIENT_ID"
FITBIT_CLIENT_SECRET = "YOUR_FITBIT_CLIENT_SECRET"

# OAuth client setup
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



class GoogleAppClient(_AppClient):
    "A `WebApplicationClient` for Google oauth2"
    base_url = "https://accounts.google.com/o/oauth2/v2/auth"
    token_url = "https://oauth2.googleapis.com/token"
    info_url = "https://openidconnect.googleapis.com/v1/userinfo"
    
    def __init__(self, client_id, client_secret, code=None, scope=None, **kwargs):
        scope_pre = "https://www.googleapis.com/auth/userinfo"
        if not scope: scope=["openid", f"{scope_pre}.email", f"{scope_pre}.profile"]
        super().__init__(client_id, client_secret, code=code, scope=scope, **kwargs)
    
    @classmethod
    def from_file(cls, fname, code=None, scope=None, **kwargs):
        cred = Path(fname).read_json()['web']
        return cls(cred['client_id'], client_secret=cred['client_secret'], code=code, scope=scope, **kwargs)

with open('fitbit_config.json', 'r') as f: # TODO: change to absolute path
    config = json.load(f)

print(config)
fitbit_client_oauth = FitbitClient(
    client_id=config['web']['client_id'],
    client_secret=config['web']['client_secret'],
    scope=["activity", "heartrate", "profile"], 
    redirect_uri=config['web']['redirect_uri']
)
