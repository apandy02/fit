
import logging

import fasthtml.common as fh
from fasthtml.common import RedirectResponse

from fit.web.common import database_service
from fit.web.onboarding import ui


def get_profile_page(session):
    """Return the profile completion page"""
    user_data = database_service.get_profile_data(session["user_id"])
    block_onboarded_users(session)
    return ui.create_profile_page(user_data)

def get_activity_page(session):
    """Return the activity selection page"""
    block_onboarded_users(session)
    return ui.create_activity_page(session)

def get_dietary_page(session):
    """Return the dietary restrictions page"""
    block_onboarded_users(session)
    return ui.create_dietary_page(session)

def get_goals_page(session):
    """Return the goals selection page"""
    block_onboarded_users(session)
    return ui.create_goals_page(session)

async def handle_profile_completion(session, request: fh.Request):
    """Handle profile form submission"""
    try:
        form = await request.form()
        form_data = dict(form)
        form_data["user_id"] = session["user_id"]
        form_data["onboarding_stage"] = 1
        database_service.update_profile(form_data)
        return fh.Response(headers={"HX-Redirect": "/onboarding/dietary"})

    except Exception as e:
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
        
        database_service.update_profile(
            {"user_id": session["user_id"], "dietary_restrictions": restrictions_str, "onboarding_stage": 2}
        )
        
        return fh.Response(headers={"HX-Redirect": "/onboarding/activity"})
    except Exception as e:
        return fh.P(
            f"Error updating dietary restrictions: {str(e)}",
            cls="text-error font-semibold text-center mt-4"
        )

async def handle_activity_selection(session, request: fh.Request):
    """Handle activity level selection"""
    try:
        form = await request.form()
        activity_level = form.get("activity_level")
        database_service.update_profile(
            {"user_id": session["user_id"], "activity_level": activity_level, "onboarding_stage": 3}
        )
        
        return fh.Response(headers={"HX-Redirect": "/onboarding/goals"})
    except Exception as e:
        logging.error(f"Error updating activity level: {e}")
        return fh.P(
            f"Error updating activity level: {str(e)}",
            cls="text-error font-semibold text-center mt-4"
        )

async def handle_goals_selection(session, request: fh.Request):
    """Handle goals selection"""
    try:
        form = await request.form()
        weight_goal = form.get("weight_goal")
        fitness_goal = form.get("fitness_goal")
        database_service.update_profile(
            {
                "user_id": session["user_id"],
                "weight_goal": weight_goal,
                "fitness_goal": fitness_goal,
                "onboarding_stage": 4
            }
        )
        
        return fh.Response(headers={"HX-Redirect": "/nutrition"})
    except Exception as e:
        logging.error(f"Error updating goals: {e}")
        return fh.P(
            f"Error updating goals: {str(e)}",
            cls="text-error font-semibold text-center mt-4"
        ) 

def block_onboarded_users(session):
    """Block users who have already completed onboarding"""
    user_data = database_service.get_profile_data(session["user_id"])
    if user_data["onboarding_stage"] == 4:
        return RedirectResponse('/nutrition', status_code=303)