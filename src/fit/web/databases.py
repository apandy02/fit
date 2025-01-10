import json
from datetime import datetime

import fasthtml.common as fh
from fit.nutrition.data import (Carbohydrates, ConditionalNutrients, Fats,
                                Macronutrients, MealBreakdown, Micronutrients,
                                NutritionalInformation)

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
                carbohydrates=float,
                fat=float,
                fiber=float,
                vitamin_a=float,
                vitamin_c=float,
                vitamin_d=float,
                calcium=float,
                iron=float,
                potassium=float,
                sodium=float,
                creatine=float,
                is_supplement=bool,
            ),
            pk='uuid'
        )

    # Table for storing supplement definitions
    supplements_table = db.t.supplements
    if supplements_table not in db.t:
        supplements_table.create(
            dict(
                name=str, 
                description=str,
                calories=float,
                protein=float,
                carbohydrates=float,
                fat=float,
                fiber=float,
                vitamin_a=float,
                vitamin_c=float,
                vitamin_d=float,
                calcium=float,
                iron=float,
                potassium=float,
                sodium=float,
                creatine=float,
            ),
            pk='name'
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
        select llm_summary, ingredients, meal_time, calories, protein, carbohydrates, fat, fiber, vitamin_a, vitamin_c, vitamin_d,
        calcium, iron, potassium, sodium, creatine
        from meals 
        where date_entered = ?
        order by meal_time
    """
    result = database.execute(query, (str(date),)).fetchall()
    return [
        MealBreakdown(
            title=row[0],
            ingredients=row[1],
            calories=row[3],
            macronutrients=Macronutrients(
                protein=row[4],
                carbohydrates=Carbohydrates(total=row[5], fiber=row[7], total_sugar=0, added_sugar=0),
                fat=Fats(total=row[6], saturated=0, trans=0),
            ),
            micronutrients=Micronutrients(
                vitamin_a=row[8],
                vitamin_c=row[9],
                vitamin_d=row[10],
                calcium=row[11],
                iron=row[12],
                potassium=row[13],
                sodium=row[14]
            ),
            conditional_nutrients=ConditionalNutrients(
                creatine=row[15]
            )
        ) for row in result
    ]

def get_all_meal_summaries(database: fh.Database):
    """
    Get the meals for a given user.
    """
    query = """
        select llm_summary, ingredients from meals 
    """
    result = database.execute(query).fetchall()
    return [row[0] for row in result]

def get_weekly_meals(database: fh.Database, week: list[datetime]):
    """
    Get the meals for a given week.
    """
    return {str(day): get_daily_meals(database, day) for day in week} #TODO: change to Sunday to Monday for key

def get_daily_cumulative_nutrition(database: fh.Database, date: datetime):
    """
    Get the cumulative daily nutrition for a given date.
    """
    query = """
        SELECT 
            SUM(calories) as calories,
            SUM(protein) as protein,
            SUM(carbohydrates) as carbohydrates, 
            SUM(fat) as fat,
            SUM(fiber) as fiber,
            SUM(vitamin_a) as vitamin_a,
            SUM(vitamin_c) as vitamin_c,
            SUM(vitamin_d) as vitamin_d,
            SUM(calcium) as calcium,
            SUM(iron) as iron,
            SUM(potassium) as potassium,
            SUM(sodium) as sodium,
            SUM(creatine) as creatine
        FROM meals 
        WHERE date_entered = ?
    """
    result = database.execute(query, (str(date),)).fetchone()
    if result is None or result[0] is None:
        return NutritionalInformation()
    
    result_info = NutritionalInformation(
        calories=result[0],
        macronutrients=Macronutrients(
            protein=result[1],
            carbohydrates=Carbohydrates(total=result[2], fiber=result[4], total_sugar=0, added_sugar=0),
            fat=Fats(total=result[3], saturated=0, trans=0),
        ),
        micronutrients=Micronutrients(
            vitamin_a=result[5],
            vitamin_c=result[6],
            vitamin_d=result[7],
            calcium=result[8],
            iron=result[9],
            potassium=result[10],
            sodium=result[11]
        ),
        conditional_nutrients=ConditionalNutrients(
            creatine=result[12]
        )
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
        llm_summary=meal.title,
        ingredients=meal.ingredients,
        calories=meal.calories,
        protein=meal.macronutrients.protein,
        carbohydrates=meal.macronutrients.carbohydrates.total,
        fat=meal.macronutrients.fat.total,  
        vitamin_a=meal.micronutrients.vitamin_a,
        vitamin_c=meal.micronutrients.vitamin_c,
        vitamin_d=meal.micronutrients.vitamin_d,
        calcium=meal.micronutrients.calcium,
        iron=meal.micronutrients.iron,
        potassium=meal.micronutrients.potassium,
        sodium=meal.micronutrients.sodium,
        fiber=meal.macronutrients.carbohydrates.fiber,
        creatine=meal.conditional_nutrients.creatine,
        is_supplement=False
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

def insert_supplement(database: fh.Database, name: str, consumption_time: str, nutritional_info: NutritionalInformation):
    """
    Insert or update a supplement definition in the database.
    """
    supplements_table = database.t.supplements
    supplements_table.insert(
        name=name,
        calories=nutritional_info.calories,
        protein=nutritional_info.macronutrients.protein,
        carbohydrates=nutritional_info.macronutrients.carbohydrates.total,
        fat=nutritional_info.macronutrients.fat.total,
        fiber=nutritional_info.macronutrients.carbohydrates.fiber,
        vitamin_a=nutritional_info.micronutrients.vitamin_a,
        vitamin_c=nutritional_info.micronutrients.vitamin_c,
        vitamin_d=nutritional_info.micronutrients.vitamin_d,
        calcium=nutritional_info.micronutrients.calcium,
        iron=nutritional_info.micronutrients.iron,
        potassium=nutritional_info.micronutrients.potassium,
        sodium=nutritional_info.micronutrients.sodium,
    )
    meals_table = database.t.meals
    meals_table.insert(
        llm_summary=name,# change column name 
        calories=nutritional_info.calories,
        protein=nutritional_info.macronutrients.protein,
        carbohydrates=nutritional_info.macronutrients.carbohydrates.total,
        fat=nutritional_info.macronutrients.fat.total,
        fiber=nutritional_info.macronutrients.carbohydrates.fiber,
        vitamin_a=nutritional_info.micronutrients.vitamin_a,
        vitamin_c=nutritional_info.micronutrients.vitamin_c,
        vitamin_d=nutritional_info.micronutrients.vitamin_d,
        calcium=nutritional_info.micronutrients.calcium,
        iron=nutritional_info.micronutrients.iron,
        potassium=nutritional_info.micronutrients.potassium,
        sodium=nutritional_info.micronutrients.sodium,
        meal_time=consumption_time,
        is_supplement=True,
    )

def log_supplement_consumption(database: fh.Database, user_id: str, supplement_name: str, servings: float, time_consumed: str):
    """
    Log a supplement consumption entry.
    """
    supplement_entries_table = database.t.supplement_entries
    supplement_entries_table.insert(
        user_id=user_id,
        supplement_name=supplement_name,
        date_consumed=datetime.date(datetime.today()),
        time_consumed=time_consumed,
        servings=servings,
    )

def get_supplement(database: fh.Database, name: str) -> NutritionalInformation | None:
    """
    Get a supplement's nutritional information by name.
    """
    query = """
        SELECT calories, protein, carbohydrates, fat, fiber, vitamin_a, vitamin_c, vitamin_d,
               calcium, iron, potassium, sodium
        FROM supplements 
        WHERE name = ?
    """
    result = database.execute(query, (name,)).fetchone()
    if result is None:
        return None
    
    return NutritionalInformation(
        calories=result[0],
        macronutrients=Macronutrients(
            protein=result[1],
            carbohydrates=Carbohydrates(total=result[2], fiber=result[4], total_sugar=0, added_sugar=0), # TODO: incorporate sub macronutrients 
            fat=Fats(total=result[3], saturated=0, trans=0),
        ),
        micronutrients=Micronutrients(
            vitamin_a=result[5],
            vitamin_c=result[6],
            vitamin_d=result[7],
            calcium=result[8],
            iron=result[9],
            potassium=result[10],
            sodium=result[11]
        )
    )

def get_supplement_names(database: fh.Database) -> list[str]:
    """
    Get all supplement names from the database.
    """
    query = """
        SELECT name FROM supplements
    """
    result = database.execute(query).fetchall()
    return [row[0] for row in result]

def get_all_supplements(database: fh.Database) -> list[tuple[str, str, NutritionalInformation]]:
    """
    Get all supplements and their nutritional information.
    Returns a list of tuples containing (name, description, nutritional_info)
    """
    query = """
        SELECT name, description, calories, protein, carbohydrates, fat, fiber, vitamin_a, 
               vitamin_c, vitamin_d, calcium, iron, potassium, sodium
        FROM supplements
    """
    results = database.execute(query).fetchall()
    return [
        (
        row[0], 
        row[1], 
        NutritionalInformation(
            calories=row[2],
            macronutrients=Macronutrients(
                protein=row[3],
                carbohydrates=Carbohydrates(total=row[4], fiber=row[6], total_sugar=0, added_sugar=0), # TODO: incorporate sub macronutrients 
                fat=Fats(total=row[5], saturated=0, trans=0),
            ),
            micronutrients=Micronutrients(
                vitamin_a=row[7],
                vitamin_c=row[8],
                vitamin_d=row[9],
                calcium=row[10],
                iron=row[11],
                potassium=row[12],
                sodium=row[13]
            )
        )
        )
        for row in results
    ]

def get_daily_supplement_entries(database: fh.Database, user_id: str, date: datetime) -> list[tuple[str, float, str]]:
    """
    Get all supplement entries for a user on a given date.
    Returns a list of tuples containing (supplement_name, servings, time_consumed)
    """
    query = """
        SELECT supplement_name, servings, time_consumed
        FROM supplement_entries
        WHERE user_id = ? AND date_consumed = ?
        ORDER BY time_consumed
    """
    results = database.execute(query, (user_id, date)).fetchall()
    return [(row[0], row[1], row[2]) for row in results]