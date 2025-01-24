import datetime

import fasthtml.common as fh
from fit.trackers.base import FitnessTracker
from fit.trackers.implementations.whoop import Whoop
from fit.trackers.manager import tracker_factory
from fit.utils.conversions import kj_to_kcal
from fit.web.common import (create_fab_menu, create_text_generation_card,
                            create_time_filter, page_outline)


def get(session):
    """Return the performance tracking page content"""
    tracker = tracker_factory(session["tracker"], session["access_token"])
    fab_buttons = [
        ("Activity", "🏃", None), 
        ("Workout", "💪", None),  
        ("Stats", "📊", None)      
    ]
    text_generation_endpoint = "/generate_performance_overview"

    content = fh.Div(
            fh.Card(
                fh.H3("Performance Overview", cls="text-2xl font-bold text-center mb-2 text-primary-content"),
                fh.P(
                    "Track your athletic performance and training",
                    cls="text-slate-400 text-center"
                ),
                create_time_filter("daily"),
                create_text_generation_card(text_generation_endpoint, "Generate Performance Overview"),
                fh.Div(
                    get_performance_metrics_section(tracker)
                ),
                cls="bg-black shadow-lg rounded-lg p-6"
            ),
            # Add FAB menu
            create_fab_menu(fab_buttons),
            cls="max-w-4xl mx-auto p-6"
        ),

    return page_outline(3, "Performance Tracking", True, True, content) 

def performance_card(title: str, value: str):
    return fh.Card(
        fh.Div(
            fh.H4(title, cls="text-lg font-semibold text-primary-content mb-4 text-center"),
            fh.P(value, cls="text-4xl font-bold text-secondary-content text-center"),
            cls="p-6 flex flex-col"
        ),
        cls="bg-base-200 outline outline-1 outline-primary-content rounded-lg"
    )

def get_performance_metrics_section(tracker: FitnessTracker):
    """Return the performance tracking card content"""
    daily_stats, workouts = get_performance_info(tracker)
    return fh.Div(
        # Cycle Metrics Grid
        fh.Div(
            fh.H3("Today's Overview", cls="text-xl font-bold text-primary-content mb-6 text-center"),
            fh.Div(
                performance_card("Strain", f"{daily_stats['strain']:.2f}") if isinstance(tracker, Whoop) else None,
                performance_card("Calories", f"{int(daily_stats['calories'])}"),
                performance_card("Average Heart Rate", f"{int(daily_stats['average_heart_rate'])} bpm"),
                performance_card("Max Heart Rate", f"{int(daily_stats['max_heart_rate'])} bpm"),
                cls="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8"
            ),
            cls="mb-8"
        ),
        fh.Div(
            fh.H3("Today's Workouts", cls="text-xl font-bold text-primary-content mb-6 text-center"),
            create_workout_cards(workouts) if workouts else fh.P("No workouts recorded today", cls="text-primary-content text-center italic"),
            cls="mb-8"
        ),
        cls="p-6"
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
    else:
        daily_stats = {
            "calories": tracker.get_daily_calories_burned(today),
            "average_heart_rate": 55,
            "max_heart_rate": 100,
        } # TODO: wrap the retrieval of averages etc into functions so we can use them here

    workouts = tracker.get_daily_workouts(today)
    return daily_stats, workouts

def create_workout_cards(workouts: list[dict]) -> fh.Div:
    """Create collapsible cards for each workout"""
    return fh.Div(
        *[
            fh.Div(
                fh.Div(
                    fh.H4(workout["sport"], cls="text-lg font-semibold text-primary-content"),
                    cls="collapse-title"
                ),
                fh.Div(
                    # Workout details will go here
                    cls="collapse-content bg-base-300"
                ),
                tabindex="0",
                cls="collapse bg-base-200 outline outline-1 outline-primary-content rounded-lg hover:bg-base-300"
            ) for workout in workouts
        ],
        cls="space-y-4"
    )
