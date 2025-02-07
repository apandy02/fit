import datetime

import fasthtml.common as fh

import fit.rest.assistants as assistants
from fit.trackers.base import FitnessTracker
from fit.trackers.implementations.whoop import Whoop
from fit.trackers.manager import tracker_factory
from fit.web.common import (create_fab_menu, create_text_generation_card,
                            create_time_filter, database_service, page_outline)


def get(session):
    """Return the rest tracking page content"""
    tracker = tracker_factory(session["tracker"], session["access_token"])
    fab_buttons = [
        ("Sleep", "😴", None),
        ("Strain", "📈", None),
        ("Readiness", "🔋", None)
    ]
    text_generation_endpoint = "/generate_rest_overview"
    
    content = fh.Div(
            fh.Card(
                fh.H3("Rest Overview", cls="text-2xl font-bold text-center mb-2 text-base-content"),
                fh.P(
                    "Monitor your rest and readiness",
                    cls="text-slate-400 text-center"
                ),
                create_time_filter("daily"),
                create_text_generation_card(text_generation_endpoint, "Generate Rest Overview"),
                fh.Div(
                    get_rest_metrics_section(tracker)
                ),
                cls="bg-base-100 shadow-none rounded-lg p-6"
            ),
            create_fab_menu(fab_buttons),
            cls="max-w-4xl mx-auto p-6"
        ),
    return page_outline(4, "Rest Tracking", True, True, content)

def rest_card(title: str, value: str):
    return fh.Card(
        fh.Div(
            fh.H4(title, cls="text-lg font-semibold text-base-content mb-4 text-center"),
            fh.P(value, cls="text-4xl font-bold text-base-content text-center"),
            cls="p-6 flex flex-col"
        ),
        cls="bg-base-200 outline outline-1 outline-base-content rounded-lg shadow-none"
    )

def get_rest_metrics_section(tracker: FitnessTracker):
    """Return the rest tracking metrics section"""
    recovery, sleep = get_rest_info(tracker)
    
    return fh.Div(
        fh.Div(
            fh.H3("Today's Recovery", cls="text-xl font-bold text-base-content mb-8 text-center"),
            fh.Div(
                fh.P("No recovery data available for today", cls="text-base-content text-center italic") if not recovery else
                fh.Div(
                    rest_card("Recovery Score", f"{recovery.get('score', 'N/A')}%") if isinstance(tracker, Whoop) else None,
                    rest_card("Resting Heart Rate", f"{recovery.get('resting_heart_rate', 'N/A')} bpm"), 
                    rest_card("HRV", f"{recovery.get('hrv_rmssd_milli', 'N/A'):.2f} ms" if recovery.get('hrv_rmssd_milli') is not None else "N/A ms"),
                    cls="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8 md:[&>*:last-child:nth-child(2n-1)]:col-span-2 md:[&>*:last-child:nth-child(2n-1)]:mx-auto md:[&>*:last-child:nth-child(2n-1)]:w-1/2"
                ),
            ),
            cls="mb-16"
        ),
        fh.Div(
            fh.H3("Today's Sleep", cls="text-xl font-bold text-base-content mb-8 text-center"),
            create_sleep_cards(sleep) if sleep else fh.P("No sleep data available for today", cls="text-base-content text-center italic"),
            cls="mb-8"
        ),
        cls="p-6"
    )

def create_sleep_cards(sleep_entries: list[dict]) -> fh.Div:
    """Create collapsible cards for each sleep entry"""
    return fh.Div(
        *[
            fh.Div(
                fh.Div(
                    fh.H4("Nap" if entry.get("nap", False) else "Sleep", cls="text-lg font-semibold text-base-content"),
                    cls="collapse-title"
                ),
                fh.Div(
                    # TODO: Sleep details will go here
                    fh.P("hello"),
                    cls="collapse-content bg-base-300"
                ),
                tabindex="0",
                cls="collapse bg-base-200 outline outline-1 outline-primary-content rounded-lg hover:bg-base-300"
            ) for entry in sleep_entries
        ],
        cls="space-y-4"
    )

def get_rest_info(tracker: FitnessTracker):
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


async def generate_overview(session):
    """Generate the rest overview analysis by getting the user's sleep data, meals, activities,
    and recovery metrics for the previous day."""
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