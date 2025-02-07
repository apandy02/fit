import datetime

import fasthtml.common as fh

import fit.rest.assistants as assistants
from fit.trackers.base import FitnessTracker
from fit.trackers.implementations.whoop import Whoop
from fit.trackers.manager import tracker_factory
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
        sleep_data = tracker.get_daily_sleep(yesterday)
        meals = database_service.get_daily_meals(yesterday, session["user_id"])
        formatted_meals = [(datetime.datetime.combine(yesterday, meal["meal_time"]), meal["meal"]) for meal in meals]
        activities = tracker.get_daily_workouts(yesterday)
        formatted_activities = [(activity.start_time, activity.type, activity.intensity) for activity in activities]
        
        if isinstance(tracker, Whoop):
            recovery = tracker.get_daily_recovery(yesterday)
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
                "resting_heart_rate": tracker.get_daily_resting_heart_rate(yesterday),
                "hrv": tracker.get_daily_hrv(yesterday),
                "recovery_score": None
            }
        
        sleep_target = 480.0
        analysis = assistants.analyze_rest_patterns(
            sleep_data=sleep_data,
            meals=formatted_meals,
            activities=formatted_activities,
            sleep_targets=sleep_target,
            recovery_metrics=recovery_metrics
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
    
def _get_rest_info(tracker: FitnessTracker):
    """
    Retrieve rest and recovery information for the day
    """
    today = datetime.date.today()
    if isinstance(tracker, Whoop):
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
