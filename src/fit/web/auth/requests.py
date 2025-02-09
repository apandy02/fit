from datetime import datetime

from fasthtml.common import RedirectResponse
from fasthtml.oauth import redir_url
from oauthlib.oauth2 import WebApplicationClient

from fit.trackers.implementations.fitbit import FitbitAppClient
from fit.web.auth.clients import fitbit_client_oauth as fitbit_client
from fit.web.auth.clients import whoop_client_oauth as whoop_client
from fit.web.auth.ui import get_login_page
from fit.web.common import database_service

auth_callback_path = "/auth_redirect"
fitbit_auth_callback_path = auth_callback_path + '/fitbit'
whoop_auth_callback_path = auth_callback_path + '/whoop'

fitbit_scope = ["activity", "heartrate", "profile"]
whoop_scope = ["offline", "read:recovery", "read:cycles", "read:workout", "read:sleep", "read:profile"]


def login(req):
    fitbit_redir = redir_url(req, f"{auth_callback_path}/fitbit")
    whoop_redir = redir_url(req, f"{auth_callback_path}/whoop")
    fitbit_login_link = fitbit_client.login_link(fitbit_redir, scope=fitbit_scope)
    whoop_login_link = whoop_client.login_link(whoop_redir, scope=whoop_scope)
    return get_login_page(req, fitbit_login_link=fitbit_login_link, whoop_login_link=whoop_login_link)

def fitbit_auth_redirect(code:str, request, session):
    new_user, user_id, access_token_dict = _handle_new_user("fitbit", fitbit_client, code, request)
    return _session_setup_redirect(new_user, user_id, access_token_dict, session)

def whoop_auth_redirect(code:str, request, session):
    new_user, user_id, access_token_dict = _handle_new_user("whoop", whoop_client, code, request)
    return _session_setup_redirect(new_user, user_id, access_token_dict, session)

def _session_setup_redirect(new_user: bool, user_id: int, access_token_dict: dict, session: dict):
    session['user_id'] = user_id
    session['access_token'] = access_token_dict['access_token']
    session['access_token_expiry'] = access_token_dict['expires_at']
    session['refresh_token'] = access_token_dict['refresh_token']
    session["tracker"] = "whoop"
    if new_user:
        return RedirectResponse('/onboarding/profile', status_code=303)
    else:
        return RedirectResponse('/nutrition', status_code=303)

def _handle_new_user(provider: str, client: WebApplicationClient, code: str, request):
    redir = redir_url(request, f"{auth_callback_path}/{provider}")
    access_token_dict = client.fetch_access_token(code, redir)
    if provider == "fitbit":
        provider_user_id = access_token_dict['user_id']
    else:
        provider_user_id = client.get_info()['user_id']
    
    user_id = database_service.get_user_id(provider_user_id, provider)
    new_user = False
    if user_id is None:
        new_user = True
        user_dict = {"provider_user_id": provider_user_id, "provider": provider}
        row = database_service.insert_new_user(user_dict)
        user_id = row['user_id']
        profile_info = client.get_info(token=access_token_dict['access_token'])
        profile_dict = {
            "user_id": user_id,
            "onboarding_stage": 0
        }
        
        if isinstance(client, FitbitAppClient):
            profile_dict.update({
                "name": profile_info['user']['fullName'],
                "gender": profile_info['user']['gender'],
                "date_of_birth": datetime.strptime(profile_info['user']['dateOfBirth'], '%Y-%m-%d').strftime('%m-%d-%Y')
            })
        else:
            profile_dict.update(
                {"name": f"{profile_info['first_name']} {profile_info['last_name']}", "email": profile_info['email']}
            )

        database_service.insert_profile(profile_dict)
        
    return new_user, user_id, access_token_dict