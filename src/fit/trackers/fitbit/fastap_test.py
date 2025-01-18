import os
from typing import Optional

from authlib.integrations.requests_client import OAuth2Session
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import RedirectResponse

# ------------------------------------------------------------------------------
# 1. FASTAPI APP
# ------------------------------------------------------------------------------
app = FastAPI()

# 2. FAKE IN-MEMORY SESSION STORE (NOT FOR PRODUCTION)
FAKE_SESSIONS = {}

# 3. YOUR FITBIT CREDENTIALS
FITBIT_CLIENT_ID = os.environ.get("FITBIT_CLIENT_ID", "YOUR_FITBIT_CLIENT_ID")
print(f"FITBIT_CLIENT_ID: ({FITBIT_CLIENT_ID})")
FITBIT_CLIENT_SECRET = os.environ.get("FITBIT_CLIENT_SECRET", "YOUR_FITBIT_CLIENT_SECRET")
print(f"FITBIT_CLIENT_SECRET: ({FITBIT_CLIENT_SECRET})")

# 4. OAUTH ENDPOINTS FOR FITBIT
FITBIT_AUTHORIZATION_ENDPOINT ="https://www.fitbit.com/oauth2/authorize"
FITBIT_TOKEN_ENDPOINT = "https://api.fitbit.com/oauth2/token"

# ------------------------------------------------------------------------------
# Helper Function: Return an OAuth2Session with Fitbit config
# ------------------------------------------------------------------------------
def get_fitbit_oauth2_session(token=None):
    return OAuth2Session(
        client_id=FITBIT_CLIENT_ID,
        client_secret=FITBIT_CLIENT_SECRET,
        token=token,  # Pass in existing token if we have one
        authorization_endpoint=FITBIT_AUTHORIZATION_ENDPOINT,
        token_endpoint=FITBIT_TOKEN_ENDPOINT,
    )

# ------------------------------------------------------------------------------
# ROUTE 1: Redirect user to Fitbit's authorization page
# ------------------------------------------------------------------------------
@app.get("/fitbit/login")
def fitbit_login():
    """
    Step 1: Redirect user to Fitbit for Authorization with response_type=code.
    """
    fitbit = get_fitbit_oauth2_session()

    # Scopes you want access to: e.g. 'activity','heartrate','profile','sleep'
    scope = ["activity", "heartrate", "profile"]

    # Redirect URI where Fitbit should send the user back
    # Must match exactly what you have in Fitbit App settings
    redirect_uri = "http://localhost:8000/fitbit/authorize"  # Replace with your domain

    # Create the authorization URL
    authorization_url, state = fitbit.create_authorization_url(
        FITBIT_AUTHORIZATION_ENDPOINT,
        redirect_uri=redirect_uri,
        scope=scope,
    )

    # Save the state in our "fake session"
    FAKE_SESSIONS[state] = {}

    # Redirect to the Fitbit authorization URL
    return RedirectResponse(url=authorization_url)


# ------------------------------------------------------------------------------
# ROUTE 2: Callback/Authorize Endpoint (Fitbit sends code + state back here)
# ------------------------------------------------------------------------------
@app.get("/fitbit/authorize")
def fitbit_authorize(request: Request, code: Optional[str] = None, state: Optional[str] = None):
    """
    Step 2: Fitbit redirects the user back with ?code=...&state=...
    We exchange that code for an access token + refresh token.
    """
    # Validate presence of code and state
    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing code or state parameter")

    # Check if the state is in our "fake session"
    if state not in FAKE_SESSIONS:
        raise HTTPException(status_code=400, detail="Invalid state parameter")

    fitbit = get_fitbit_oauth2_session()

    redirect_uri = "http://localhost:8000/fitbit/authorize"  # Same as above

    try:
        # Exchange the authorization code for tokens
        token = fitbit.fetch_token(
            url=FITBIT_TOKEN_ENDPOINT,
            authorization_response=str(request.url),
            redirect_uri=redirect_uri,
            client_secret=FITBIT_CLIENT_SECRET,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error fetching token from Fitbit: {e}")

    # Store tokens in the fake session
    FAKE_SESSIONS[state]["token"] = token

    # Redirect to a route where we can use the token
    return RedirectResponse(url=f"/fitbit/profile?state={state}")


# ------------------------------------------------------------------------------
# ROUTE 3: Use the Access Token to Call Fitbit's API
# ------------------------------------------------------------------------------
@app.get("/fitbit/profile")
def fitbit_profile(state: str = Query(...)):
    """
    Step 3: We have a token; call Fitbit's user profile endpoint as an example.
    """
    # Retrieve token from our fake session store
    session_data = FAKE_SESSIONS.get(state)
    if not session_data or "token" not in session_data:
        raise HTTPException(status_code=401, detail="No token found. Please re-authenticate.")

    token = session_data["token"]

    # Create a new OAuth session with the existing token
    fitbit = get_fitbit_oauth2_session(token=token)

    # Make a GET request to the user profile endpoint
    # Fitbit docs: https://dev.fitbit.com/build/reference/web-api/user/
    resp = fitbit.get("https://api.fitbit.com/1/user/-/profile.json")
    if resp.status_code != 200:
        return {
            "error": f"Failed to fetch profile: {resp.status_code}",
            "response": resp.text
        }

    profile_data = resp.json()
    return {
        "message": "Successfully fetched Fitbit profile!",
        "profile": profile_data
    }
