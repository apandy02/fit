import datetime

import fasthtml.common as fh

import fit.performance.assistants as assistants
from fit.nutrition.targets import WeightGoal, calculate_caloric_target
from fit.trackers.base import FitnessTracker
from fit.trackers.implementations.whoop import Whoop
from fit.trackers.manager import tracker_factory
from fit.utils.conversions import kj_to_kcal
from fit.web.common import database_service
from fit.web.performance import ui


def get(session):
    """
    Get request:
        Return the performance tracking page content
    """
    tracker = tracker_factory(session["tracker"], session["access_token"])
    fab_buttons = [
        ("Activity", "🏃", None), 
        ("Workout", "💪", None),  
        ("Stats", "📊", None)      
    ]
    text_generation_endpoint = "/generate_performance_overview"
    is_whoop = isinstance(tracker, Whoop)
    performance_info = get_performance_info(tracker)
    return ui.create_performance_page(performance_info, is_whoop, text_generation_endpoint, fab_buttons)


async def generate_overview(session):
    """
    Post request:
        Generate the performance overview analysis by getting the user's daily stats, activities,
        and caloric information.
    """
    try:
        tracker = tracker_factory(session["tracker"], session["access_token"])
        today = datetime.date.today()
        daily_stats, workouts = get_performance_info(tracker)
        daily_nutrition = database_service.get_daily_cumulative_nutrition(today, session["user_id"])
        caloric_consumption = daily_nutrition.calories
        caloric_target = calculate_caloric_target(daily_nutrition, WeightGoal.MAINTAIN)
        workout_trend_summary = assistants.summarize_workout_trends(workouts)
        current_time = datetime.datetime.now().time()
        time_cutoff = datetime.time(hour=20)  # 8 PM cutoff

        analysis = assistants.early_daily_performance_overview(
            daily_stats=daily_stats,
            activities=workouts,
            caloric_target=caloric_target,
            caloric_consumption=caloric_consumption,
            workout_trend_summary=workout_trend_summary,
            time=current_time,
            time_cutoff=time_cutoff
        )
        return ui.analysis_card(analysis)
        
    except Exception as e:
        return fh.P(
            f"Error generating performance analysis: {str(e)}",
            cls="text-red-500 font-semibold text-center"
        )


def get_performance_info(tracker: FitnessTracker):
    """
    Retrieve performance information for the day
    """
    today = datetime.date.today()
    if isinstance(tracker, Whoop):
        cycle = tracker.get_cycle_for_day(today)
        daily_stats = cycle["score"]
        daily_stats["calories"] = kj_to_kcal(daily_stats["kilojoule"])
    else: # fitbit for now
        heart_rate_data = tracker.get_intraday_heart_rate(datetime.date(2019, 6, 21))
        print(f"heart_rate_data: {heart_rate_data}")
        daily_stats = {
            "calories": tracker.get_daily_calories_burned(today),
            "average_heart_rate": 55,
            "max_heart_rate": 100,
        } # TODO: use the timeseries data to get the average and max heart rate

    workouts = tracker.get_daily_workouts(today)
    return daily_stats, workouts