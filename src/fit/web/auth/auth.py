from datetime import datetime

from fasthtml.common import RedirectResponse
from fasthtml.oauth import redir_url

from fit.web.auth.clients import fitbit_client_oauth as fitbit_client
from fit.web.auth.clients import whoop_client_oauth as whoop_client
from fit.web.auth.login_page import get_login_page
from fit.web.common import DB
from fit.web.databases import get_user_id, insert_new_user

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
    redir = redir_url(request, f"{auth_callback_path}/fitbit")
    access_token_dict = fitbit_client.fetch_access_token(code, redir)
    provider_user_id = access_token_dict['user_id']
    user_id = get_user_id(DB, provider_user_id, "fitbit")
    if user_id is None:
        user_dict = {
            "provider_user_id": provider_user_id,
            "provider": "fitbit"
        }
        more_info = fitbit_client.get_info(token=access_token_dict['access_token'])
        user_dict["name"] = more_info['user']['fullName']
        user_dict["gender"] = more_info['user']['gender']
        user_dict["date_of_birth"] = datetime.strptime(more_info['user']['dateOfBirth'], '%Y-%m-%d').strftime('%m-%d-%Y')
        row = insert_new_user(DB, user_dict)
        user_id = row['user_id']
        # TODO: separate handling of new and existing users
    else:
        user_id = user_id[0] # TODO: assess if this is the best way to handle this
    
    session['user_id'] = user_id
    session['access_token'] = access_token_dict['access_token']
    session['access_token_expiry'] = access_token_dict['expires_at']
    session['refresh_token'] = access_token_dict['refresh_token']
    session["tracker"] = "fitbit"
    return RedirectResponse('/nutrition', status_code=303)

def whoop_auth_redirect(code:str, request, session):
    redir = redir_url(request, whoop_auth_callback_path)
    access_token_dict = whoop_client.fetch_access_token(code, redir)
    user_info = whoop_client.get_info()
    provider_user_id = user_info['user_id']
    user_id = get_user_id(DB, provider_user_id, "whoop")
    
    if user_id is None:
        user_dict = {
            "provider_user_id": provider_user_id,
            "provider": "whoop"
        }
        more_info = whoop_client.get_info(token=access_token_dict['access_token'])
        # TODO: The whoop doesn't give me gender or dob, so when I implement the front end, 
        # there should be a form where the user must input this information
        user_dict["name"] = more_info['user']['first_name'] + " " + more_info['user']['last_name']
        user_dict["email"] = more_info['user']['email']
        row = insert_new_user(DB, user_dict)
        user_id = row['user_id']
        # TODO: separate handling of new and existing users
    else:
        user_id = user_id[0] # TODO: see if raising user doesnt exist error is better than returning None
    
    session['user_id'] = user_id
    session['access_token'] = access_token_dict['access_token']
    session['access_token_expiry'] = access_token_dict['expires_at']
    session['refresh_token'] = access_token_dict['refresh_token']
    session["tracker"] = "whoop"
    return RedirectResponse('/nutrition', status_code=303)
