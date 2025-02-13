from datetime import datetime

import fasthtml.common as fh
from fasthtml.common import RedirectResponse

from fit.web.common import database_service


def auth_before(req, session):
    """beforeware that checks if the user is logged in"""
    access_token_expiry = session.get('access_token_expiry', None)
    req.scope['auth'] = access_token_expiry
    print(f"access_token_expiry: {access_token_expiry}")
    if not access_token_expiry or datetime.now().timestamp() > access_token_expiry:
        return RedirectResponse('/login', status_code=303)

def onboarding_before(req, session):
    """beforeware that checks if the user is onboarded"""
    print(session)
    user_profile = database_service.get_profile_data(session["user_id"])

    if user_profile["onboarding_stage"] == 0:
        return RedirectResponse('/onboarding/profile', status_code=303)
    
    elif user_profile["onboarding_stage"] == 1:
        return RedirectResponse('/onboarding/measurements', status_code=303)

    elif user_profile["onboarding_stage"] == 2:
        return RedirectResponse('/onboarding/dietary', status_code=303)
        
    elif user_profile["onboarding_stage"] == 3:
        return RedirectResponse('/onboarding/activity', status_code=303)
    
    elif user_profile["onboarding_stage"] == 4:
        return RedirectResponse('/onboarding/goals', status_code=303)
    

def onboarding_complete_before(req, session):
    """block the onboarding pages for users who have completed onboarding"""
    user_profile = database_service.get_profile_data(session["user_id"])
    if user_profile["onboarding_stage"] == 5:  # Updated to reflect new final stage
        return RedirectResponse('/nutrition', status_code=303)

auth_callback_path = "/auth_redirect"

auth_bware = fh.Beforeware(
    auth_before, skip=['/login', auth_callback_path, auth_callback_path + '/fitbit', auth_callback_path + '/whoop']
)
onboarding_bware = fh.Beforeware(
    onboarding_before, 
    skip=[
        '/login',
        auth_callback_path,
        auth_callback_path + '/fitbit',
        auth_callback_path + '/whoop',
        '/onboarding/profile',
        '/onboarding/measurements',
        '/onboarding/activity',
        '/onboarding/dietary',
        '/onboarding/goals',
        '/onboarding/complete_profile',
        '/onboarding/complete_measurements',
        '/onboarding/complete_dietary',
        '/onboarding/handle_activity_selection',
        '/onboarding/handle_goals_selection',
        '/add_restriction',
        '/remove_restriction',
    ]
)