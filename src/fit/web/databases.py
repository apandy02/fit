from datetime import datetime

import fasthtml.common as fh

from fit.nutrition.data import NutritionalInfo

# TODO: consider creating a class for the database

def init_db(database_path: str):
    """
    Initialize the database and create tables if they don't exist.
    """
    db = fh.database(database_path)

    meals_table = db.t.meals
    if meals_table not in db.t:
        meals_table.create(
            dict(
                uuid=str,
                date_entered=str,
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

    return db

def get_daily_meals(database: fh.Database, date: datetime):
    """
    Get meals entered for a given date.
    """
    query = """
        select llm_summary, calories, protein, carbs, fat, fiber, vitamin_a, vitamin_c, vitamin_d,
        calcium, iron, potassium, sodium 
        from
        meals where date_entered = ?
    """
    result = database.execute(query, (date,)).fetchall()
    for row in result:
        NutritionalInfo(
            summary=row[0],
            calories=row[1],
            protein=row[2],
            carbs=row[3],
            fat=row[4],
            fiber=row[5],
            vitamin_a=row[6],
            vitamin_c=row[7],
            vitamin_d=row[8],
            calcium=row[9],
            iron=row[10],
            potassium=row[11],
            sodium=row[12]
        )
    return [
        NutritionalInfo(
            summary=row[0],
            calories=row[1],
            protein=row[2],
            carbs=row[3],
            fat=row[4],
            fiber=row[5],
            vitamin_a=row[6],
            vitamin_c=row[7],
            vitamin_d=row[8],
            calcium=row[9],
            iron=row[10],
            potassium=row[11],
            sodium=row[12]
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
    result_dict = {
        "calories": result[0] if result[0] is not None else 0,
        "protein": result[1] if result[1] is not None else 0,
        "carbs": result[2] if result[2] is not None else 0,
        "fat": result[3] if result[3] is not None else 0,
        "fiber": result[4] if result[4] is not None else 0,
        "vitamin_a": result[5] if result[5] is not None else 0,
        "vitamin_c": result[6] if result[6] is not None else 0,
        "vitamin_d": result[7] if result[7] is not None else 0,
        "calcium": result[8] if result[8] is not None else 0,
        "iron": result[9] if result[9] is not None else 0,
        "potassium": result[10] if result[10] is not None else 0,
        "sodium": result[11] if result[11] is not None else 0
    } # TODO: hardcoded, need to fix (create a separate dataclass containing nutrition info)
    return result_dict

def insert_meal(database: fh.Database, meal_description: str, nutrition_info):
    """
    Insert a meal into the database.
    """
    meals_table = database.t.meals
    meals_table.insert(
        date_entered=datetime.date(datetime.today()),
        meal_time=datetime.now().isoformat(),
        user_description=meal_description,
        llm_summary=nutrition_info.summary,
        calories=nutrition_info.calories,
        protein=nutrition_info.protein,
        carbs=nutrition_info.carbs,
        fat=nutrition_info.fat,
        vitamin_a=nutrition_info.vitamin_a,
        vitamin_c=nutrition_info.vitamin_c,
        vitamin_d=nutrition_info.vitamin_d,
        calcium=nutrition_info.calcium,
        iron=nutrition_info.iron,
        potassium=nutrition_info.potassium,
        sodium=nutrition_info.sodium,
        fiber=nutrition_info.fiber
    )