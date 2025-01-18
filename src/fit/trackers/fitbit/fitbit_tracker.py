import fitbit
from authlib.integrations.requests_client import OAuth2Session
from fit.trackers.base import FitnessTracker

class FitbitTracker(FitnessTracker):
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str, refresh_token_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.refresh_token_uri = refresh_token_uri

        self.client = fitbit.Fitbit(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            refresh_token_uri=self.refresh_token_uri
        )
        super().__init__()

    def _authenticate(self) -> None:
        session = OAuth2Session(self.client_id, self.client_secret)
        session.fetch_token(
            url=f"{self.refresh_token_uri}/oauth/token", 
        )
        self.__access_token = session.token["access_token"]

        self.client.client.fetch_token(
            url=self.refresh_token_uri,
            username=self.client_id,
            password=self.client_secret,
            grant_type="password",
        )
