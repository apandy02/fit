from datetime import datetime

import fasthtml.common as fh
from fasthtml.common import RedirectResponse
from fasthtml.oauth import redir_url

from fit.web.auth.clients import fitbit_client_oauth as fitbit_client
from fit.web.auth.clients import whoop_client_oauth as whoop_client
from fit.web.auth.ui import get_login_page
from fit.web.common import DB, page_outline
from fit.web.databases import get_profile_data, get_user_id, insert_new_user
from fit.web.user_profile import (create_basic_info_card,
                                  create_dietary_restrictions_card)

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
    new_user = False
    if user_id is None:
        new_user = True
        user_dict = {
            "provider_user_id": provider_user_id,
            "provider": "fitbit"
        }
        row = insert_new_user(DB, user_dict)
        user_id = row['user_id']
        profile_info = fitbit_client.get_info(token=access_token_dict['access_token'])
        profile_dict = {
            "user_id": user_id,
            "name": profile_info['user']['fullName'],
            "gender": profile_info['user']['gender'],
            "date_of_birth": datetime.strptime(profile_info['user']['dateOfBirth'], '%Y-%m-%d').strftime('%m-%d-%Y'),
            "onboarding_stage": 0
        }
        
        DB.t.profile.insert(profile_dict)

    else:
        user_id = user_id[0] # TODO: assess if this is the best way to handle this
    
    session['user_id'] = user_id
    session['access_token'] = access_token_dict['access_token']
    session['access_token_expiry'] = access_token_dict['expires_at']
    session['refresh_token'] = access_token_dict['refresh_token']
    session["tracker"] = "fitbit"

    if new_user:
        return RedirectResponse('/onboarding/profile', status_code=303)
    else:
        return RedirectResponse('/nutrition', status_code=303)

def whoop_auth_redirect(code:str, request, session):
    redir = redir_url(request, whoop_auth_callback_path)
    access_token_dict = whoop_client.fetch_access_token(code, redir)
    user_info = whoop_client.get_info()
    provider_user_id = user_info['user_id']
    user_id = get_user_id(DB, provider_user_id, "whoop")
    new_user = False
    if user_id is None:
        new_user = True
        user_dict = {
            "provider_user_id": provider_user_id,
            "provider": "whoop"
        }
        # TODO: The whoop doesn't give me gender or dob, so when I implement the front end, 
        # there should be a form where the user must input this information
        row = insert_new_user(DB, user_dict)
        user_id = row['user_id']
        profile_info = whoop_client.get_info(token=access_token_dict['access_token'])
        profile_dict = {
            "user_id": user_id,
            "name": profile_info['first_name'] + " " + profile_info['last_name'],
            "email": profile_info['email'],
            "onboarding_stage": 0
        }
        DB.t.profile.insert(profile_dict)
    else:
        user_id = user_id[0] # TODO: see if raising user doesnt exist error is better than returning None
    
    session['user_id'] = user_id
    session['access_token'] = access_token_dict['access_token']
    session['access_token_expiry'] = access_token_dict['expires_at']
    session['refresh_token'] = access_token_dict['refresh_token']
    session["tracker"] = "whoop"
    if new_user:
        return RedirectResponse('/onboarding/profile', status_code=303)
    else:
        return RedirectResponse('/nutrition', status_code=303)


def get_profile_page(session):
    """Return the profile completion page"""
    user_data = get_profile_data(DB, session["user_id"])
    if user_data["onboarding_stage"] == 3:
        return RedirectResponse('/nutrition', status_code=303)
    content = fh.Article(
        fh.Div(
            fh.Card(
                fh.Form(
                    hx_post="/onboarding/complete_profile",
                    cls="space-y-6"
                )(
                    create_basic_info_card(user_data),
                    fh.Button(
                        "Next →",
                        type="submit",
                        cls="btn btn-primary outline outline-1 outline-primary-content w-full mt-8"
                    ),
                    cls="p-6"
                ),
                cls="bg-base-200 shadow-lg rounded-lg"
            ),
            cls="max-w-2xl mx-auto p-6"
        ),
        cls="bg-base-100 min-h-screen flex items-center"
    )
    
    return page_outline(None, "Complete Profile", False, False, content)

def get_activity_page(session):
    """Return the activity selection page"""
    user_data = get_profile_data(DB, session["user_id"])
    if user_data["onboarding_stage"] == 3:
        return RedirectResponse('/nutrition', status_code=303)
    content = fh.Article(
        fh.Div(
            fh.Card(
                fh.Div(
                    fh.Header(
                        fh.H3("How Active Are You?", cls="text-2xl font-bold text-center mb-6 text-primary-content"),
                        cls="mb-6 bg-base-200"
                    ),
                    fh.Form(
                        hx_post="/onboarding/handle_activity_selection",
                        cls="space-y-6"
                    )(
                        fh.Div(
                            fh.Button(
                                fh.Div(
                                    fh.H4("Not at all", cls="text-lg font-bold mb-2 text-primary-content"),
                                    fh.P("0 workouts per week", cls="text-sm"),
                                    cls="text-center"
                                ),
                                type="submit",
                                name="activity_level",
                                value="sedentary",
                                cls="btn btn-ghost outline outline-1 outline-primary-content w-full h-24 mb-4"
                            ),
                            fh.Button(
                                fh.Div(
                                    fh.H4("Lightly active", cls="text-lg font-bold mb-2 text-primary-content"),
                                    fh.P("1-2 workouts per week", cls="text-sm"),
                                    cls="text-center"
                                ),
                                type="submit",
                                name="activity_level",
                                value="lightly_active",
                                cls="btn btn-ghost outline outline-1 outline-primary-content w-full h-24 mb-4"
                            ),
                            fh.Button(
                                fh.Div(
                                    fh.H4("Active", cls="text-lg font-bold mb-2 text-primary-content"),
                                    fh.P("3-5 workouts per week", cls="text-sm"),
                                    cls="text-center"
                                ),
                                type="submit",
                                name="activity_level",
                                value="active",
                                cls="btn btn-ghost outline outline-1 outline-primary-content w-full h-24 mb-4"
                            ),
                            fh.Button(
                                fh.Div(
                                    fh.H4("Very active", cls="text-lg font-bold mb-2 text-primary-content"),
                                    fh.P("6+ workouts per week", cls="text-sm"),
                                    cls="text-center"
                                ),
                                type="submit",
                                name="activity_level",
                                value="very_active",
                                cls="btn btn-ghost outline outline-1 outline-primary-content w-full h-24"
                            ),
                            cls="space-y-4"
                        ),
                        cls="p-6"
                    ),
                    cls="bg-base-200 outline outline-1 outline-primary-content rounded-lg p-6"
                ),
                cls="bg-base-200 shadow-lg rounded-lg"
            ),
            cls="max-w-2xl mx-auto p-6"
        ),
        cls="bg-base-100 min-h-screen flex items-center"
    )
    
    return page_outline(None, "Activity Level", False, False, content)

async def handle_profile_completion(session, request: fh.Request):
    """Handle profile form submission"""
    try:
        form = await request.form()
        form_data = dict(form)
        form_data["user_id"] = session["user_id"]
        form_data["onboarding_stage"] = 1
        DB.t.profile.update(form_data)
        return fh.Response(headers={"HX-Redirect": "/onboarding/dietary"})

    except Exception as e:
        print(f"Error updating profile: {e}")
        return fh.P(
            f"Error updating profile: {str(e)}",
            cls="text-error font-semibold text-center mt-4"
        )

async def handle_dietary_completion(session, request: fh.Request):
    """Handle dietary preferences submission"""
    try:
        form = await request.form()
        restrictions = form.getlist("existing_restrictions[]")
        
        restrictions_str = ",".join(restrictions) if restrictions else ""
        
        DB.t.profile.update({
            "user_id": session["user_id"],
            "dietary_restrictions": restrictions_str,
            "onboarding_stage": 2
        })
        
        return fh.Response(headers={"HX-Redirect": "/onboarding/activity"})
    except Exception as e:
        print(f"Error updating dietary restrictions: {e}")
        return fh.P(
            f"Error updating dietary restrictions: {str(e)}",
            cls="text-error font-semibold text-center mt-4"
        )

async def handle_activity_selection(session, request: fh.Request):
    """Handle activity level selection"""
    try:
        form = await request.form()
        activity_level = form.get("activity_level")
        user_profile = get_profile_data(DB, session["user_id"])
        print(f"user_profile: {user_profile}")
        print(f"activity_level: {activity_level}")
        # Store activity level in profile
        DB.t.profile.update({
            "user_id": session["user_id"],
            "activity_level": activity_level,
            "onboarding_stage": 3
        })
        
        return fh.Response(headers={"HX-Redirect": "/nutrition"})
    except Exception as e:
        print(f"Error updating activity level: {e}")
        return fh.P(
            f"Error updating activity level: {str(e)}",
            cls="text-error font-semibold text-center mt-4"
        )

def get_dietary_page(session):
    """Return the dietary restrictions page"""
    user_data = get_profile_data(DB, session["user_id"])
    if user_data["onboarding_stage"] == 3:
        return RedirectResponse('/nutrition', status_code=303)
    
    content = fh.Article(
        fh.Div(
            fh.Card(
                fh.Div(
                    fh.Form(
                        hx_post="/onboarding/complete_dietary",
                        cls="space-y-6"
                    )(
                        create_dietary_restrictions_card([], hx_target="onboarding-restrictions-list"),  # Pass empty list for initial state
                        fh.Button(
                            "Next →",
                            type="submit",
                            cls="btn btn-primary outline outline-1 outline-primary-content w-full mt-8"
                        ),
                        cls="p-6"
                    ),
                    cls="bg-base-200 outline outline-1 outline-primary-content rounded-lg p-6"
                ),
                cls="bg-base-200 shadow-lg rounded-lg"
            ),
            cls="max-w-2xl mx-auto p-6"
        ),
        cls="bg-base-100 min-h-screen flex items-center"
    )
    
    return page_outline(None, "Dietary Restrictions", False, False, content) 