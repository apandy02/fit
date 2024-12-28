import datetime

import fasthtml.common as fh

from fit.web.common import create_fab_menu, page_outline, active_tracker, create_time_filter, create_overview_card


def get():
    """Return the rest tracking page content"""
    fab_buttons = [
        ("Sleep", "😴", None),
        ("Strain", "📈", None),
        ("Readiness", "🔋", None)
    ]
    
    content = fh.Div(
            fh.Card(
                fh.H3("Rest Overview", cls="text-2xl font-bold text-center mb-2 text-primary-content"),
                fh.P(
                    "Monitor your rest and readiness",
                    cls="text-slate-400 text-center"
                ),
                create_time_filter("daily"),
                create_overview_card("daily"),
                fh.Div(
                    get_rest_metrics_section()
                ),
                cls="bg-black shadow-lg rounded-lg p-6"
            ),
            create_fab_menu(fab_buttons),
            cls="max-w-4xl mx-auto p-6"
        ),
    return page_outline(4, "Rest Tracking", content)

def rest_card(title: str, value: str):
    return fh.Card(
        fh.Div(
            fh.H4(title, cls="text-lg font-semibold text-primary-content mb-4 text-center"),
            fh.P(value, cls="text-4xl font-bold text-secondary-content text-center"),
            cls="p-6 flex flex-col"
        ),
        cls="bg-base-200 outline outline-1 outline-primary-content rounded-lg"
    )

def get_rest_metrics_section():
    """Return the rest tracking metrics section"""
    recovery, sleep = get_rest_info()
    print(f"recovery: {recovery}")
    
    return fh.Div(
        # Recovery Metrics Grid
        fh.Div(
            fh.H3("Today's Recovery", cls="text-xl font-bold text-primary-content mb-8 text-center"),
            fh.Div(
                rest_card("Recovery Score", f"{recovery['recovery_score']}%"),
                rest_card("Resting Heart Rate", f"{recovery['resting_heart_rate']} bpm"),
                rest_card("HRV", f"{recovery['hrv_rmssd_milli']:.2f} ms"),
                cls="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8 md:[&>*:last-child:nth-child(2n-1)]:col-span-2 md:[&>*:last-child:nth-child(2n-1)]:mx-auto md:[&>*:last-child:nth-child(2n-1)]:w-1/2"
            ),
            cls="mb-16"
        ),
        # Sleep Section
        fh.Div(
            fh.H3("Today's Sleep", cls="text-xl font-bold text-primary-content mb-8 text-center"),
            create_sleep_cards(sleep) if sleep else fh.P("No sleep recorded today", cls="text-primary-content text-center italic"),
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
                    fh.H4("Nap" if entry.get("nap", False) else "Sleep", cls="text-lg font-semibold text-primary-content"),
                    cls="collapse-title"
                ),
                fh.Div(
                    # Sleep details will go here
                    fh.P("hello"),
                    cls="collapse-content bg-base-300"
                ),
                tabindex="0",
                cls="collapse bg-base-200 outline outline-1 outline-primary-content rounded-lg hover:bg-base-300"
            ) for entry in sleep_entries
        ],
        cls="space-y-4"
    )

def get_rest_info():
    """
    Retrieve rest and recovery information for the day
    """
    today = datetime.date.today() - datetime.timedelta(days=1)  # TODO: for testing
    recovery = active_tracker.get_daily_recovery(today)
    if recovery is not None and len(recovery) > 0:
        recovery_scores = recovery[0]["score"]
    else:
        recovery_scores = None
    
    sleep = active_tracker.get_daily_sleep(today)

    
    return recovery_scores, sleep  