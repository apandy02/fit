import datetime

import fasthtml.common as fh

import fit.rest.assistants as assistants
from fit.backend.trackers.base import FitnessTracker
from fit.backend.trackers.implementations.whoop import Whoop
from fit.backend.trackers.manager import tracker_factory
from fit.web.common import database_service
from fit.web.rest import ui


def get(session):
    """
    Get request:
        Return the rest tracking page content
    """
    tracker = tracker_factory(session["tracker"], session["access_token"])
    fab_buttons = [
        ("Sleep", "😴", None),
        ("Strain", "📈", None),
        ("Readiness", "🔋", None)
    ]
    text_generation_endpoint = "/generate_rest_overview"
    recovery, sleep = _get_rest_info(tracker)
    return ui.create_rest_page(tracker, text_generation_endpoint, fab_buttons, recovery, sleep)

async def generate_overview(session):
    """
    Post request:
        Generate the rest overview analysis by getting the user's sleep data, meals, activities,
        and recovery metrics for the previous day.
    """
    try:
        tracker = tracker_factory(session["tracker"], session["access_token"])
        yesterday = datetime.datetime.today().date() - datetime.timedelta(days=1)
        analysis_data = _get_rest_analysis_data(tracker, yesterday, session["user_id"])
        
        sleep_target = 480.0
        analysis = assistants.analyze_rest_patterns(
            sleep_data=analysis_data["sleep_data"],
            meals=analysis_data["formatted_meals"],
            activities=analysis_data["formatted_activities"], 
            sleep_targets=sleep_target,
            recovery_metrics=analysis_data["recovery_metrics"]
        )
        
        return fh.Card(
            fh.Div(
                fh.P(analysis, cls="text-base-content"),
                cls="p-4 space-y-2"
            ),
            cls="bg-base-200 outline outline-1 outline-primary-content rounded-lg mt-8"
        )
        
    except Exception as e:
        return fh.P(
            f"Error generating rest analysis: {str(e)}",
            cls="text-red-500 font-semibold text-center"
        )

def _get_rest_analysis_data(tracker: FitnessTracker, date: datetime.date, user_id: int) -> dict:
    """
    Get all the data needed for rest analysis for a given date
    Args:
        tracker: The fitness tracker to use
        date: The date to get data for
        user_id: The user ID to get meal data for
    Returns:
        Dictionary containing sleep data, meals, activities and recovery metrics
    """
    sleep_data = tracker.get_daily_sleep(date)
    meals = database_service.get_daily_meals(date, user_id)
    formatted_meals = [(datetime.datetime.combine(date, meal["meal_time"]), meal["meal"]) for meal in meals]
    activities = tracker.get_daily_workouts(date)
    formatted_activities = [(activity.start_time, activity.type, activity.intensity) for activity in activities]
    
    if isinstance(tracker, Whoop):
        recovery = tracker.get_daily_recovery(date)
        if recovery is not None and len(recovery) > 0:
            scores = recovery["score"]
            recovery_metrics = {
                "recovery_score": scores["recovery_score"],
                "resting_heart_rate": scores["resting_heart_rate"],
                "hrv": scores["hrv_rmssd_milli"]
            }
        else:
            recovery_metrics = {
                "recovery_score": None,
                "resting_heart_rate": None,
                "hrv": None
            }
    else:
        recovery_metrics = {
            "resting_heart_rate": tracker.get_daily_resting_heart_rate(date),
            "hrv": tracker.get_daily_hrv(date),
            "recovery_score": None
        }
        
    return {
        "sleep_data": sleep_data,
        "formatted_meals": formatted_meals,
        "formatted_activities": formatted_activities,
        "recovery_metrics": recovery_metrics
    }
    
def _get_rest_info(tracker: FitnessTracker):
    """
    Retrieve rest and recovery information for the day
    """
    today = datetime.date.today()
    if tracker.tracker_type == "whoop":
        recovery = tracker.get_daily_recovery(today)
        if recovery is not None and len(recovery) > 0:
            scores = recovery["score"]
            recovery_score = scores["recovery_score"]
            resting_hr = scores["resting_heart_rate"]
            hrv = scores["hrv_rmssd_milli"]
        else:
            recovery_score = None
            resting_hr = None
            hrv = None
    else:
        resting_hr = tracker.get_daily_resting_heart_rate(today)
        hrv = tracker.get_daily_hrv(today)
        recovery_score = None
    
    sleep = tracker.get_daily_sleep(today)
    
    recovery_data = {
        "score": recovery_score,
        "resting_hr": resting_hr,
        "hrv": hrv,
    }
    
    return recovery_data, sleep
