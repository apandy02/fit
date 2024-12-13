import os
import json
import fasthtml.common as fh
from fit.nutrition.assistants import NutritionLogger
from fit.trackers.manager import get_active_tracker

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

    return db, (meals_table, measurements_table)


DB, (MEALS_TABLE, MEASUREMENTS_TABLE) = init_db()
nutrition_tracker = NutritionLogger()
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
