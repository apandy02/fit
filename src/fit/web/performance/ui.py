import fasthtml.common as fh

from fit.web.common import (create_fab_menu, create_text_generation_card,
                            create_time_filter, page_outline)


def create_performance_page(performance_info: tuple[dict, list[dict]], is_whoop: bool, text_generation_endpoint: str, fab_buttons: list[tuple[str, str, str]]):
    content = fh.Div(
            fh.Card(
                fh.H3("Performance Overview", cls="text-2xl font-light text-center mb-2 text-base-content"),
                fh.P(
                    "Track your athletic performance and training",
                    cls="text-slate-400 text-center font-light"
                ),
                create_time_filter("daily"),
                create_text_generation_card(text_generation_endpoint, "Generate Performance Overview"),
                fh.Div(
                    get_performance_metrics_section(performance_info, is_whoop)
                ),
                cls="bg-base-100 shadow-none rounded-lg p-6"
            ),
            create_fab_menu(fab_buttons),
            cls="max-w-4xl mx-auto p-6"
        )
    return page_outline(4, "Performance Overview", True, True, content)


def get_performance_metrics_section(performance_info: tuple[dict, list[dict]], is_whoop: bool):
    """Return the performance tracking card content"""
    daily_stats, workouts = performance_info
    return fh.Div(
        fh.Div(
            fh.H3("Today's Overview", cls="text-xl font-light text-base-content mb-6 text-center"),
            fh.Div(
                performance_card("Strain", f"{daily_stats['strain']:.2f}") if is_whoop else None,
                performance_card("Calories", f"{int(daily_stats['calories'])}"),
                performance_card("Average Heart Rate", f"{int(daily_stats['average_heart_rate'])} bpm"),
                performance_card("Max Heart Rate", f"{int(daily_stats['max_heart_rate'])} bpm"),
                cls="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8"
            ),
            cls="mb-8"
        ),
        fh.Div(
            fh.H3("Today's Workouts", cls="text-xl font-light text-base-content mb-6 text-center"),
            create_workout_cards(workouts) if workouts else fh.P("No workouts recorded today", cls="text-base-content text-center italic font-light"),
            cls="mb-8"
        ),
        cls="p-6"
    )

def performance_card(title: str, value: str):
    return fh.Card(
        fh.Div(
            fh.H4(title, cls="text-lg font-light text-base-content mb-4 text-center"),
            fh.P(value, cls="text-4xl font-light text-base-content text-center"),
            cls="p-6 flex flex-col"
        ),
        cls="bg-base-200 outline outline-1 outline-base-content rounded-lg shadow-none"
    )

def create_workout_cards(workouts: list[dict]) -> fh.Div:
    """Create collapsible cards for each workout"""
    return fh.Div(
        *[
            fh.Div(
                fh.Div(
                    fh.H4(workout["sport"], cls="text-lg font-light text-base-content"),
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

def analysis_card(analysis: str):
    return fh.Card(
        fh.Div(
            fh.P(analysis, cls="text-base-content font-light"),
            cls="p-4 space-y-2"
        ),
        cls="bg-base-200 outline outline-1 outline-base-content rounded-lg mt-8 shadow-none"
    )