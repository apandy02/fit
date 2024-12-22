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

    return db

def get_daily_meals(database: fh.Database, date: datetime):
    """
    Get meals entered for a given date.
    """
    query = """
        select llm_summary, ingredients, calories, protein, carbs, fat, fiber, vitamin_a, vitamin_c, vitamin_d,
        calcium, iron, potassium, sodium 
        from
        meals where date_entered = ?
    """
    result = database.execute(query, (date,)).fetchall()
    return [
        MealBreakdown(
            summary=row[0],
            ingredients=row[1],
            calories=row[2],
            protein=row[3],
            carbs=row[4],
            fat=row[5],
            fiber=row[6],
            vitamin_a=row[7],
            vitamin_c=row[8],
            vitamin_d=row[9],
            calcium=row[10],
            iron=row[11],
            potassium=row[12],
            sodium=row[13]
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

def insert_meal(database: fh.Database, meal_description: str, meal: MealBreakdown):
    """
    Insert a meal into the database.
    """
    meals_table = database.t.meals
    meals_table.insert(
        date_entered=datetime.date(datetime.today()),
        meal_time=datetime.now().isoformat(),
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
    print(metrics)
    database.execute(query, (metrics, user_id))
