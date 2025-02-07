import fasthtml.common as fh

from fit.trackers.base import FitnessTracker
from fit.trackers.implementations.whoop import Whoop
from fit.web.common import (create_fab_menu, create_text_generation_card,
                            create_time_filter, page_outline)


def create_rest_page(tracker: FitnessTracker, text_generation_endpoint: str, fab_buttons: list[tuple[str, str, str]], recovery: dict, sleep: list[dict]):
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
                    get_rest_metrics_section(tracker, recovery, sleep)
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


def get_rest_metrics_section(tracker: FitnessTracker, recovery: dict, sleep: list[dict]):
    """Return the rest tracking metrics section"""    
    return fh.Div(
        fh.Div(
            fh.H3("Today's Recovery", cls="text-xl font-bold text-base-content mb-8 text-center"),
            fh.Div(
                fh.P("No recovery data available for today", cls="text-base-content text-center italic") if not recovery else
                fh.Div(
                    rest_card("Recovery Score", f"{recovery.get('score', 'N/A')}%") if isinstance(tracker, Whoop) else None,
                    rest_card("Resting Heart Rate", f"{recovery.get('resting_hr', 'N/A')} bpm"), 
                    rest_card("HRV", f"{recovery.get('hrv', 'N/A'):.2f} ms" if recovery.get('hrv') is not None else "N/A ms"),
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