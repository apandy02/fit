import json
from pathlib import Path
from oauthlib.oauth2 import WebApplicationClient
from fasthtml.oauth import _AppClient
import os, hashlib, base64, httpx
from oauthlib.oauth2 import WebApplicationClient
from urllib.parse import urlencode

def make_code_verifier_and_challenge():
    code_verifier = base64.urlsafe_b64encode(os.urandom(64)).decode('utf-8').rstrip('=')
    sha256 = hashlib.sha256(code_verifier.encode('utf-8')).digest()
    code_challenge = base64.urlsafe_b64encode(sha256).decode('utf-8').rstrip('=')
    return code_verifier, code_challenge


class FitbitAppClient(WebApplicationClient):
    """
    A PKCE-capable client for Fitbit.
    """
    base_url = "https://www.fitbit.com/oauth2/authorize"
    token_url = "https://api.fitbit.com/oauth2/token"
    info_url  = "https://api.fitbit.com/1/user/-/profile.json"  # or whichever userinfo you want

    def __init__(self, client_id, code=None, scope=None, **kwargs):
        super().__init__(client_id, code=code, scope=scope, **kwargs)
        # Generate or store the PKCE code_verifier/challenge
        self.code_verifier, self.code_challenge = make_code_verifier_and_challenge()
    
    def login_link(self, redirect_uri, scope=None, state=None):
        """Create the Fitbit login link with PKCE parameters."""
        if scope is None: scope = self.scope
        if state is None: state = self.state

        # Build up the extra PKCE query params
        extra_params = {
            "code_challenge": self.code_challenge,
            "code_challenge_method": "S256"
        }

        # Use the built-in method, but pass extra_auth_params for PKCE
        auth_url = self.prepare_request_uri(
            self.base_url,
            redirect_uri=redirect_uri,
            scope=scope,
            state=state,
            **extra_params
        )
        return auth_url

    def parse_response(self, code, redirect_uri):
        """
        Exchange the code for an access token, including the code_verifier.
        """
        data = {
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": self.client_id,
            "grant_type": "authorization_code",
            # PKCE: pass the code_verifier
            "code_verifier": self.code_verifier,
        }
        # If your Fitbit app is registered as a confidential client,
        # you may also have a client_secret – then you'd pass it here:
        #     data["client_secret"] = self.client_secret

        r = httpx.post(self.token_url, data=data)
        r.raise_for_status()
        self.parse_request_body_response(r.text)

    def fetch_access_token(self, code, redirect_uri):
        # Exchange the code for an access token, including the PKCE code_verifier
        data = {
            "client_id": self.client_id,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
            "code": code,
            "code_verifier": self.code_verifier,
        }
        # If your Fitbit app is a confidential client, include client_secret:
        # data["client_secret"] = self.client_secret

        r = httpx.post(self.token_url, data=data)
        r.raise_for_status()
        self.parse_request_body_response(r.text)
        return self.token 

    def get_info(self, token=None):
        """Fetch user profile info from Fitbit's API."""
        if token is None:
            token = self.token["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print(f"headers: {headers}")
        resp = httpx.get(self.info_url, headers=headers)
        resp.raise_for_status()
        return resp.json()

    def retr_info(self, code, redirect_uri):
        """Convenience method to parse token response then fetch user info."""
        self.parse_response(code, redirect_uri)
        info = self.get_info()
        print(f"info: {info}")
        return info

    def retr_id(self, code, redirect_uri):
        """Fitbit's user_id is in the profile."""
        profile = self.retr_info(code, redirect_uri)
        print(f"profile: {profile}")
        return profile["user"]["encodedId"]  # Or whichever field is your 'id'

    

fitbit_config_path = Path(__file__).parent / 'config' / 'fitbit_config.json'

with open(fitbit_config_path, 'r') as f:
    config = json.load(f)

print(config)
fitbit_client_oauth = FitbitAppClient(
    client_id=config['web']['client_id'],
    client_secret=config['web']['client_secret'],
    scope=["activity", "heartrate", "profile"], 
)

print(fitbit_client_oauth.__dir__())

payload={
    'code': '3d029df7d1257009da9f85a09e3b7f54e03d2803',
    'redirect_uri': 'http://localhost:5001/auth_redirect', 
    'client_id': '23PYH2', 
    'client_secret': 'e843af75a5ecb9231f274e97f5bf7601', 
    'grant_type': 'authorization_code'
}

