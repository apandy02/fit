
import fasthtml.common as fh

from fit.nutrition.assistants import NutritionLogger
from fit.trackers.manager import get_active_tracker
from fit.web.databases import init_db

DB_PATH = "data/nutrition.db"

DB = init_db(DB_PATH)
nutrition_logger = NutritionLogger()
active_tracker = get_active_tracker()

def page_outline(selidx, title, *c):
    """
    Return the common page outline for the frontend.
    """
    return (
        fh.Title(title),
        fh.Body(
            fh.Html(data_theme="winter"),
            fh.Div(
                fh.Div(
                    fh.A(
                        "Food",
                        href="/food",
                        cls="btn btn-ghost text-white",
                    ),
                    fh.A(
                        "Personal",
                        href="/personal", 
                        cls="btn btn-ghost text-white",
                    ),
                    fh.A(
                        "Progress",
                        href="/progress",
                        cls="btn btn-ghost text-white",
                    ),
                    fh.A(
                        "Trackers",
                        href="/trackers",
                        cls="btn btn-ghost text-white",
                    ),
                    cls="flex justify-center items-center flex-1",
                ),
                cls="navbar bg-slate-950 bg-opacity-100 rounded-m h-[5vh] flex justify-center",
            ),
            fh.Div(
                fh.Div(*c, cls="min-h-[calc(100vh-8vh)] pb-[3vh]"),
                cls="overflow-y-auto",
            ),
        ),
    )
