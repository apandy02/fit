from datetime import datetime

from fasthtml.common import RedirectResponse
from fasthtml.oauth import redir_url
from oauthlib.oauth2 import WebApplicationClient

from fit.web.auth.clients import fitbit_client_oauth as fitbit_client
from fit.web.auth.clients import whoop_client_oauth as whoop_client
from fit.web.auth.ui import get_login_page
from fit.web.common import database_service

auth_callback_path = "/auth_redirect"

def login(req):
    fitbit_redir = redir_url(req, f"{auth_callback_path}/fitbit")
    whoop_redir = redir_url(req, f"{auth_callback_path}/whoop")
    fitbit_login_link = fitbit_client.login_link(fitbit_redir)
    whoop_login_link = whoop_client.login_link(whoop_redir)
    return get_login_page(req, fitbit_login_link=fitbit_login_link, whoop_login_link=whoop_login_link)

def fitbit_auth_redirect(code:str, request, session):
    redir = redir_url(request, f"{auth_callback_path}/fitbit")
    access_token_dict = fitbit_client.fetch_access_token(code, redir)
    fitbit_user_id = access_token_dict['user_id']
    user_id, new_user = _get_user_id("fitbit", fitbit_user_id, fitbit_client, access_token_dict)
    return _session_setup_redirect(new_user, user_id, access_token_dict, session, "fitbit")

def whoop_auth_redirect(code:str, request, session):
    redir = redir_url(request, f"{auth_callback_path}/whoop")
    access_token_dict = whoop_client.fetch_access_token(code, redir)
    provider_id = whoop_client.get_info()['user_id']
    user_id, new_user = _get_user_id("whoop", provider_id, whoop_client, access_token_dict)
    return _session_setup_redirect(new_user, user_id, access_token_dict, session, "whoop")

def _session_setup_redirect(
        new_user: bool, user_id: int, access_token_dict: dict, session: dict, provider: str
    ):
    session['user_id'] = user_id
    session['access_token'] = access_token_dict['access_token']
    session['access_token_expiry'] = access_token_dict['expires_at']
    session['refresh_token'] = access_token_dict['refresh_token']
    session["tracker"] = provider
    if new_user:
        return RedirectResponse('/onboarding/profile', status_code=303)
    else:
        return RedirectResponse('/nutrition', status_code=303)

def _is_user_new(provider: str, provider_user_id: str) -> bool:
    user_id = database_service.get_user_id(provider_user_id, provider)
    return user_id is None

def _get_user_id(
        provider: str, provider_user_id: str, client: WebApplicationClient, access_token_dict: dict
    ) -> int:
    new_user = _is_user_new(provider, provider_user_id)
    if new_user:
        user_id = _handle_new_user(provider, client, access_token_dict, provider_user_id)
    else:
        user_id = database_service.get_user_id(provider_user_id, provider)
    return user_id, new_user

def _handle_new_user(
        provider: str, client: WebApplicationClient, access_token_dict: dict, provider_user_id: str
    ) -> int:
    user_dict = {"provider_user_id": provider_user_id, "provider": provider}
    row = database_service.insert_new_user(user_dict)
    user_id = row['user_id']
    profile_info = client.get_info(token=access_token_dict['access_token'])
    profile_dict = {
        "user_id": user_id,
        "onboarding_stage": 0
    }
    
    if client.tracker_type == "fitbit":
        profile_dict.update({
            "name": profile_info['user']['fullName'],
            "gender": profile_info['user']['gender'],
            "date_of_birth": datetime.strptime(
                profile_info['user']['dateOfBirth'], '%Y-%m-%d').strftime('%m-%d-%Y'
            )
        })
    elif client.tracker_type == "whoop":
        profile_dict.update(
            {"name": f"{profile_info['first_name']} {profile_info['last_name']}", "email": profile_info['email']}
        )

    database_service.insert_profile(profile_dict)
    
    return user_id