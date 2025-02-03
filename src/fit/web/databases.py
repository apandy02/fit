import json
from datetime import datetime

import fasthtml.common as fh

from fit.nutrition.data_models import (KITCHEN_ITEM_CATEGORIES, Carbohydrates,
                                       ConditionalNutrients, Fats,
                                       Macronutrients, MealBreakdown,
                                       Micronutrients, NutritionalInformation)


def init_db(database_path: str):
    """
    Initialize the database and create tables if they don't exist.
    """
    db = fh.database(database_path)

    users_table = db.t.users
    if users_table not in db.t:
        users_table.create(user_id=int, email=str, provider=str, provider_user_id=str, pk='user_id')

    meals_table = db.t.meals
    if meals_table not in db.t:
        meals_table.create(
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
            user_id=int, # foreign key
            pk="rowid",
            not_null= ["user_id"]
        )

    # Table for storing supplement definitions
    supplements_table = db.t.supplements
    if supplements_table not in db.t:
        supplements_table.create(
            user_id=int, # foreign key
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
            pk='name',
            not_null= ["user_id"]
        )

    measurements_table = db.t.measurements  
    if measurements_table not in db.t:
        measurements_table.create(
            datetime=str,
            height=float,
            weight=float,
            user_id=int, # foreign key
            pk='uuid',
            not_null= ["user_id"]
        )
    
    water_table = db.t.water
    if water_table not in db.t:
        water_table.create(
            date=str,
            user_id=int, # foreign key
            time=str,
            water_consumed_ml=float,
            pk='uuid',
            not_null= ["user_id"]
        )

    profile_table = db.t.profile
    if profile_table not in db.t:
        profile_table.create(
            user_id=int, # foreign key
            name=str,
            email=str,
            gender=str,
            date_of_birth=str,
            units=str,
            dietary_restrictions=str,
            activity_level=str,
            pk='user_id',
            not_null= ["user_id"]
        )
    
    inventory_table = db.t.inventory
    if inventory_table not in db.t:
        inventory_table.create(
            user_id=int, # foreign key
            title=str,
            quantity=float,
            unit=str,
            category=str,
            pk='rowid',
            not_null= ["user_id"]
        )

    return db

def get_user_id(database: fh.Database, provider_user_id: str, provider: str) -> int | None:
    """Get the user id for a given provider user id and provider"""
    query = """
        SELECT user_id FROM users WHERE provider_user_id = ? AND provider = ?
    """
    result = database.execute(query, (provider_user_id, provider)).fetchone()
    return result

def insert_new_user(database: fh.Database, user_dict: dict) -> int:
    """Insert a new user into the database"""
    row = database.t.users.insert(user_dict)
    return row

def get_daily_meals(database: fh.Database, date: datetime, user_id: int) -> list[dict]:
    """Get all meals for a given date
    
    Returns a list of dictionaries, each containing:
    - meal: MealBreakdown object with the meal's nutritional information
    - meal_time: datetime.time object representing when the meal was consumed
    - rowid: integer representing the meal's unique identifier in the database
    """
    query = """
        SELECT rowid, llm_summary, ingredients, meal_time, calories, protein, carbohydrates, fat, fiber,
               vitamin_a, vitamin_c, vitamin_d, calcium, iron, potassium, sodium, creatine
        FROM meals 
        WHERE date_entered = ? AND is_supplement = 0 AND user_id = ?
        ORDER BY meal_time ASC
    """
    results = database.execute(query, (str(date), user_id)).fetchall()
    meals = []
    for row in results:
        rowid = row[0]
        meal = MealBreakdown(
            title=row[1],
            ingredients=row[2],
            calories=row[4],
            macronutrients=Macronutrients(
                protein=row[5],
                carbohydrates=Carbohydrates(
                    total=row[6],
                    fiber=row[8],
                    total_sugar=0,
                    added_sugar=0
                ),
                fat=Fats(
                    total=row[7],
                    saturated=0,
                    trans=0
                )
            ),
            micronutrients=Micronutrients(
                vitamin_a=row[9],
                vitamin_c=row[10],
                vitamin_d=row[11],
                calcium=row[12],
                iron=row[13],
                potassium=row[14],
                sodium=row[15]
            ),
            conditional_nutrients=ConditionalNutrients(
                creatine=row[16]
            )
        )
        meal_time = datetime.strptime(row[3], "%H:%M:%S").time()
        meals.append({
            "meal": meal,
            "meal_time": meal_time,
            "rowid": rowid
        })
    
    return meals

def get_all_meal_summaries(database: fh.Database, user_id: int):
    """
    Get the meals for a given user.
    """
    query = """
        select llm_summary, ingredients from meals where user_id = ?
    """
    result = database.execute(query, (user_id,)).fetchall()
    return [row[0] for row in result]

def get_weekly_meals(database: fh.Database, week: list[datetime], user_id: int):
    """
    Get the meals for a given week.
    """
    return {str(day): get_daily_meals(database, day, user_id) for day in week} #TODO: change to Sunday to Monday for key

def get_daily_cumulative_nutrition(database: fh.Database, date: datetime, user_id: int):
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
        WHERE date_entered = ? AND user_id = ?
    """
    result = database.execute(query, (str(date), user_id)).fetchone()
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

def insert_meal(database: fh.Database, meal_description: str, meal: MealBreakdown, meal_date: str, meal_time: str, user_id: int):
    """
    Insert a meal into the database.
    """
    meals_table = database.t.meals
    try:
        meals_table.insert(
            date_entered=meal_date,
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
            is_supplement=False,
            user_id=user_id
        )
    except Exception as e:
        print(e)
        print(f"Error inserting meal: {e}")
        raise e


def get_visible_metrics(database: fh.Database, user_id: int):
    """
    Get the visible metrics from the database.
    """
    query = """
        select metrics from visible_metrics where user_id = ?
    """
    result = database.execute(query, (user_id,)).fetchone()
    return json.loads(result[0])

def set_visible_metrics(database: fh.Database, metrics: list[str], user_id: int):
    """
    Set the visible metrics in the database.
    """
    query = """
        update visible_metrics set metrics = ? where user_id = ?
    """
    metrics = json.dumps(metrics)
    database.execute(query, (metrics, user_id))

def get_profile_data(database: fh.Database, user_id: int):
    """Get user data from the database"""
    query = """
        SELECT name, email, date_of_birth, units, gender, dietary_restrictions, activity_level FROM profile WHERE user_id = ?
    """
    result = database.execute(query, (user_id,)).fetchone()
    if result:
        return {
            "name": result[0],
            "email": result[1],
            "date_of_birth": result[2],
            "units": result[3],
            "gender": result[4],
            "dietary_restrictions": result[5],
            "activity_level": result[6]
        }
    return {}


def get_dietary_restrictions(database: fh.Database, user_id: int):
    """Get the dietary restrictions from the database"""
    query = """
        select dietary_restrictions from profile where user_id = ?
    """
    result = database.execute(query, (user_id,)).fetchone()
    if result:
        return result[0]
    return None

def insert_supplement(database: fh.Database, name: str, consumption_time: str, nutritional_info: NutritionalInformation, date: str, user_id: int):
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
        user_id=user_id
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
        date_entered=date,
        is_supplement=True,
        user_id=user_id
    )

def log_supplement_consumption(database: fh.Database, user_id: int, supplement_name: str, servings: float, time_consumed: str):
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

def get_supplement(database: fh.Database, name: str, user_id: int) -> NutritionalInformation | None:
    """
    Get a supplement's nutritional information by name.
    """
    query = """
        SELECT calories, protein, carbohydrates, fat, fiber, vitamin_a, vitamin_c, vitamin_d,
               calcium, iron, potassium, sodium
        FROM supplements 
        WHERE name = ? AND user_id = ?
    """
    result = database.execute(query, (name, user_id)).fetchone()
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

def get_supplement_names(database: fh.Database, user_id: int) -> list[str]:
    """
    Get all supplement names from the database.
    """
    query = """
        SELECT name FROM supplements WHERE user_id = ?
    """
    result = database.execute(query, (user_id,)).fetchall()
    return [row[0] for row in result]

def get_all_supplements(database: fh.Database, user_id: int) -> list[tuple[str, str, NutritionalInformation]]:
    """
    Get all supplements and their nutritional information.
    Returns a list of tuples containing (name, description, nutritional_info)
    """
    query = """
        SELECT name, description, calories, protein, carbohydrates, fat, fiber, vitamin_a, 
               vitamin_c, vitamin_d, calcium, iron, potassium, sodium
        FROM supplements
        WHERE user_id = ?
    """
    results = database.execute(query, (user_id,)).fetchall()
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

def get_daily_supplement_entries(database: fh.Database, user_id: int, date: datetime) -> list[tuple[str, float, str]]:
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


def insert_water_consumption(database: fh.Database, water_consumed_ml: float, date_consumed: datetime, time_consumed: str, user_id: int):
    """
    Insert a water consumption entry into the database.
    """
    water_table = database.t.water
    water_table.insert(
        date=date_consumed,
        time=time_consumed,
        water_consumed_ml=water_consumed_ml,
        user_id=user_id
    )

def get_daily_water_consumption(database: fh.Database, date: datetime, user_id: int) -> float:
    """
    Get the daily water consumption for a given date.
    """
    query = """
        SELECT SUM(water_consumed_ml) as water_consumed_ml FROM water WHERE date = ? AND user_id = ?
    """
    result = database.execute(query, (str(date), user_id)).fetchone()
    return result[0]

def get_user_measurements(database: fh.Database, user_id: int) -> dict:
    """Get user measurements from the database"""
    query = """
        SELECT datetime, weight, height FROM measurements WHERE user_id = ?
    """
    result = database.execute(query, (user_id,)).fetchall()
    return result

def get_latest_user_measurements(database: fh.Database, user_id: int) -> dict:
    """Get the latest user measurements from the database"""
    query = """
        SELECT weight, height FROM measurements WHERE user_id = ? ORDER BY datetime DESC LIMIT 1
    """
   
    result = database.execute(query, (user_id,)).fetchone()
     # TODO: change to error raised
    if result is None:
        return None 
    
    return {
        "weight": result[0],
        "height": result[1]
    }

def insert_user_measurements(database: fh.Database, height: float, weight: float, datetime: datetime, user_id: int):
    """Insert user measurements into the database"""
    query = """
        INSERT INTO measurements (datetime, height, weight, user_id) VALUES (?, ?, ?, ?)
    """
    database.execute(query, (str(datetime.isoformat()), height, weight, user_id))

def delete_meal(database: fh.Database, meal_id: int, user_id: int):
    """Delete a meal from the database by its rowid."""
    try:
        database.t.meals.delete(meal_id, user_id)
        return True
    except Exception as e:
        print(f"Error deleting meal: {e}")
        return False

def insert_inventory_item(database: fh.Database, title: str, quantity: float, unit: str, category: str, user_id: int):
    """Insert an inventory item into the database"""
    database.t.inventory.insert(
        title=title,
        quantity=quantity,
        unit=unit,
        category=category,
        user_id=user_id
    )

def get_inventory(database: fh.Database, user_id: int) -> list[tuple[str, float, str, str]]:
    """Get the inventory from the database"""
    query = """
        SELECT rowid, title, quantity, unit, category FROM inventory WHERE user_id = ?
    """
    result = database.execute(query, (user_id,)).fetchall()
    results = {
        category: [] for category in KITCHEN_ITEM_CATEGORIES
    }

    for row in result:
        results[row[4]].append({
            "rowid": row[0],
            "title": row[1],
            "quantity": row[2],
            "unit": row[3], 
        })
    
    return results
