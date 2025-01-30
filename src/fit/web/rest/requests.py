from datetime import datetime, timedelta

import fasthtml.common as fh

import fit.rest.assistants as assistants
import fit.web.databases as databases
from fit.trackers.manager import tracker_factory
from fit.trackers.implementations.whoop import Whoop

async def generate_overview(session):
    """Generate the rest overview analysis by getting the user's sleep data, meals, activities,
    and recovery metrics for the previous day."""
    try:
        # Get tracker instance
        tracker = tracker_factory(session["tracker"], session["access_token"])
        
        # Get yesterday's date
        yesterday = datetime.today().date() - timedelta(days=1)
        
        # Get sleep data from tracker
        sleep_data = tracker.get_daily_sleep(yesterday)
        
        # Get meals from database
        meals = databases.get_daily_meals(databases.DB, yesterday)
        # Convert to format expected by LMP: list of (datetime, MealBreakdown)
        formatted_meals = [(datetime.combine(yesterday, meal["meal_time"]), meal["meal"]) for meal in meals]
        
        # Get activities from tracker
        activities = tracker.get_daily_activities(yesterday)
        # Convert to format expected by LMP: list of (datetime, str, float)
        formatted_activities = [(activity.start_time, activity.type, activity.intensity) for activity in activities]
        
        # Get recovery metrics based on tracker type
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
        
        # Static sleep target for now (8 hours = 480 minutes)
        sleep_target = 480.0
        
        # Call the LMP
        analysis = assistants.analyze_rest_patterns(
            sleep_data=sleep_data,
            meals=formatted_meals,
            activities=formatted_activities,
            sleep_targets=sleep_target,
            recovery_metrics=recovery_metrics
        ).content[0].parsed
        
        return fh.Card(
            fh.Div(
                fh.P(analysis, cls="text-primary-content"),
                cls="p-4 space-y-2"
            ),
            cls="bg-base-200 outline outline-1 outline-primary-content rounded-lg mt-8"
        )
        
    except Exception as e:
        return fh.P(
            f"Error generating rest analysis: {str(e)}",
            cls="text-red-500 font-semibold text-center"
        ) 