
import fasthtml.common as fh
from fit.nutrition.assistants import NutritionTracker

DB_PATH = "data/nutrition.db"

def init_db():
    """
    Initialize the database and create tables if they don't exist.
    """
    db = fh.database(DB_PATH)

    meals_table = db.t.meals
    if meals_table not in db.t:
        meals_table.create(
            dict(
                datetime_entered=str,
                meal_time=str,
                user_description=str,

                llm_summary=str,
                calories=float,
                protein=float,
                carbs=float,
                fat=float,

                fiber=float,
                vitamin_a=float,
                vitamin_c=float,
                vitamin_d=float,
                calcium=float,
                iron=float,
                potassium=float,
                sodium=float,
                
            ),
            pk='datetime_entered' # TODO: change to a more suitable primary key
        )

    measurements_table = db.t.measurements  
    if measurements_table not in db.t:
        measurements_table.create(
            dict(
                datetime=str,
                height=float,
                weight=float,
            ),
            pk='datetime' # TODO: change to a more suitable primary key
        )

    return meals_table, measurements_table


MEALS_TABLE, MEASUREMENTS_TABLE = init_db()

nutrition_tracker = NutritionTracker()

def page_outline(selidx, title, *c, logged_in: bool = False):
    """
    Return the common page outline for the frontend.
    """
    if not logged_in:
        get_started_btn = fh.A(
            "Get started",
            href="/register",
            cls="btn bg-emerald-700 opacity-90 hover:bg-emerald-500 text-white border-none",
        )
    else:
        get_started_btn = ()

    return (
        fh.Title(title),
        fh.Body(
            fh.Html(data_theme="winter"),
            fh.Div(
                fh.Div(
                    
                    get_started_btn,
                    cls="w-full px-4 flex items-center",
                ),
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
                cls="navbar bg-slate-950 bg-opacity-100 rounded-m h-[5vh]",
            ),
            fh.Div(
                fh.Div(*c, cls="min-h-[calc(100vh-8vh)] pb-[3vh]"),
                cls="overflow-y-auto",
            ),
        ),
    )
