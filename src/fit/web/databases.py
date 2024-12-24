import json
from datetime import datetime

import fasthtml.common as fh

from fit.nutrition.data import MealBreakdown, NutritionalInformation

# TODO: consider creating a class for the database

def init_db(database_path: str, metrics: dict[str, list[str]], user_id: str):
    """
    Initialize the database and create tables if they don't exist.
    """
    db = fh.database(database_path)
    user_id = "default" # TODO: get user id from auth, hardcode for now

    meals_table = db.t.meals
    if meals_table not in db.t:
        meals_table.create(
            dict(
                uuid=str,
                date_entered=str,
                ingredients=str,
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
            pk='uuid'
        )

    measurements_table = db.t.measurements  
    if measurements_table not in db.t:
        measurements_table.create(
            dict(
                datetime=str,
                height=float,
                weight=float,
            ),
            pk='uuid'
        )
    
    visible_metrics_table = db.t.visible_metrics
    if visible_metrics_table not in db.t:
        visible_metrics_table.create(
            dict(
                user_id=str,
                metrics=str,
            ),
            pk='user_id'
        )
        metrics = json.dumps(metrics)
        visible_metrics_table.insert(
            user_id=user_id,
            metrics=metrics
        )

    user_data_table = db.t.user_data
    if user_data_table not in db.t:
        user_data_table.create(
            dict(
                user_id=str,
                name=str,
                email=str,
                date_of_birth=str,
                units=str,
                dietary_restrictions=str,
            ),
            pk='user_id'
        )
        user_data_table.insert(
            user_id=user_id,
        )

    return db

def get_daily_meals(database: fh.Database, date: datetime):
    """
    Get meals entered for a given date.
    """
    query = """
        select llm_summary, ingredients, meal_time, calories, protein, carbs, fat, fiber, vitamin_a, vitamin_c, vitamin_d,
        calcium, iron, potassium, sodium 
        from meals 
        where date_entered = ?
        order by meal_time
    """
    result = database.execute(query, (date,)).fetchall()
    return [
        MealBreakdown(
            summary=row[0],
            ingredients=row[1],
            meal_time=row[2],
            calories=row[3],
            protein=row[4],
            carbs=row[5],
            fat=row[6],
            fiber=row[7],
            vitamin_a=row[8],
            vitamin_c=row[9],
            vitamin_d=row[10],
            calcium=row[11],
            iron=row[12],
            potassium=row[13],
            sodium=row[14]
        ) for row in result
    ]

def get_daily_cumulative_nutrition(database: fh.Database, date: datetime):
    """
    Get the cumulative daily nutrition for a given date.
    """
    query = """
        SELECT 
            SUM(calories) as calories,
            SUM(protein) as protein,
            SUM(carbs) as carbs, 
            SUM(fat) as fat,
            SUM(fiber) as fiber,
            SUM(vitamin_a) as vitamin_a,
            SUM(vitamin_c) as vitamin_c,
            SUM(vitamin_d) as vitamin_d,
            SUM(calcium) as calcium,
            SUM(iron) as iron,
            SUM(potassium) as potassium,
            SUM(sodium) as sodium
        FROM meals 
        WHERE date_entered = ?
    """
    result = database.execute(query, (date,)).fetchone()
    # calories should never be None
    if result is None or result[0] is None:
        return NutritionalInformation()
    
    result_info = NutritionalInformation(
        calories=result[0],
        protein=result[1],
        carbs=result[2],
        fat=result[3],
        fiber=result[4],
        vitamin_a=result[5],
        vitamin_c=result[6],
        vitamin_d=result[7],
        calcium=result[8],
        iron=result[9],
        potassium=result[10],
        sodium=result[11]
    )

    return result_info

def insert_meal(database: fh.Database, meal_description: str, meal: MealBreakdown, meal_time: str):
    """
    Insert a meal into the database.
    """
    meals_table = database.t.meals
    meals_table.insert(
        date_entered=datetime.date(datetime.today()),
        meal_time=meal_time,
        user_description=meal_description,
        llm_summary=meal.summary,
        ingredients=meal.ingredients,
        calories=meal.calories,
        protein=meal.protein,
        carbs=meal.carbs,
        fat=meal.fat,
        vitamin_a=meal.vitamin_a,
        vitamin_c=meal.vitamin_c,
        vitamin_d=meal.vitamin_d,
        calcium=meal.calcium,
        iron=meal.iron,
        potassium=meal.potassium,
        sodium=meal.sodium,
        fiber=meal.fiber
    )


def get_visible_metrics(database: fh.Database, user_id: str):
    """
    Get the visible metrics from the database.
    """
    query = """
        select metrics from visible_metrics where user_id = ?
    """
    result = database.execute(query, (user_id,)).fetchone()
    return json.loads(result[0])

def set_visible_metrics(database: fh.Database, metrics: list[str], user_id: str):
    """
    Set the visible metrics in the database.
    """
    query = """
        update visible_metrics set metrics = ? where user_id = ?
    """
    metrics = json.dumps(metrics)
    database.execute(query, (metrics, user_id))

def get_user_data(db: fh.Database, user_id="default"):
    """Get user data from the database"""
    query = """
            SELECT name, email, date_of_birth, units, dietary_restrictions FROM user_data WHERE user_id = ?
    """
    result = db.execute(query, (user_id,)).fetchone()
    if result:
        return {
            "name": result[0],
            "email": result[1],
            "date_of_birth": result[2],
            "units": result[3],
            "dietary_restrictions": result[4]
        }
    return {}


def get_dietary_restrictions(database: fh.Database, user_id: str):
    """Get the dietary restrictions from the database"""
    query = """
        select dietary_restrictions from user_data where user_id = ?
    """
    result = database.execute(query, (user_id,)).fetchone()
    return result[0]