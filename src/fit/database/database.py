import logging
from datetime import datetime

import fasthtml.common as fh

import fit.nutrition.data_models as dm


class DatabaseService:
    """
    A high-level service class that encapsulates all database operations.
    The raw database handle is kept private; only explicit methods are exposed.
    """
    def __init__(self, db_path: str, tables: list[tuple[str, type, list[str], str]]):
        self._db = fh.database(db_path)
        self.init_db(tables)
    
    def init_db(self, tables: list[tuple[str, type, list[str], str]]):
        for table_name, schema, not_null_columns, pk in tables:
            if table_name not in self._db.t:
                self._db.create(cls=schema, pk=pk, not_null=not_null_columns, name=table_name)

    @property
    def tables(self):
        return self._db.t

    def get_user_id(self, provider_user_id: str, provider: str) -> int | None:
        query = "SELECT user_id FROM users WHERE provider_user_id = ? AND provider = ? limit 1"
        result = self._db.q(query, (provider_user_id, provider))
        return None if result is None or len(result) == 0 else result[0]["user_id"] # TODO: error handling (for all these queries tbh)

    def insert_new_user(self, user_dict: dict) -> int:
        """Insert a new user into the database."""
        row = self._db.t.users.insert(user_dict)
        return row

    def get_daily_meals(self, date: datetime, user_id: int) -> list[dict]:
        """
        Returns a list of dictionaries, each containing:
        - meal: MealBreakdown object with the meal's nutritional information
        - meal_time: datetime.time object representing when the meal was consumed
        - rowid: integer representing the meal's unique identifier in the database
        """
        query = """
            SELECT rowid, llm_summary, ingredients, meal_time, calories, protein, carbohydrates,
            fat, fiber, vitamin_a, vitamin_c, vitamin_d, calcium, iron, potassium, sodium, creatine
            FROM meals WHERE date_entered = ? AND is_supplement = 0 AND user_id = ? ORDER BY meal_time ASC
        """
        results = self._db.q(query, (str(date), user_id))
        meals = []
        for row in results:
            rowid = row["rowid"]
            nutritional_info = self.__nutritional_info_from_row(row)
            meal = dm.MealBreakdown(
                title=row["llm_summary"],
                ingredients=row["ingredients"],
                calories=row["calories"],
                macronutrients=nutritional_info.macronutrients,
                micronutrients=nutritional_info.micronutrients,
                conditional_nutrients=nutritional_info.conditional_nutrients
            )
            try:
                meal_time = datetime.strptime(row["meal_time"], "%H:%M:%S").time()
            except ValueError:
                try:
                    meal_time = datetime.strptime(row["meal_time"], "%H:%M").time()
                except ValueError:
                    meal_time = datetime.fromisoformat(row["meal_time"]).time()
                
            meals.append({
                "meal": meal,
                "meal_time": meal_time,
                "rowid": rowid
            })

        return meals

    def get_all_meal_summaries(self, user_id: int):
        result = self._db.q("SELECT llm_summary, ingredients FROM meals WHERE user_id = ?", (user_id,))
        return [row["llm_summary"] for row in result]

    def get_daily_cumulative_nutrition(self, date: datetime, user_id: int) -> dm.NutritionalInformation:
        query = """
            SELECT 
            SUM(calories) as calories, SUM(protein) as protein, SUM(carbohydrates) as carbohydrates, 
            SUM(fat) as fat, SUM(fiber) as fiber, SUM(vitamin_a) as vitamin_a, SUM(vitamin_c) as vitamin_c,
            SUM(vitamin_d) as vitamin_d, SUM(calcium) as calcium, SUM(iron) as iron, SUM(potassium) as potassium, 
            SUM(sodium) as sodium, SUM(creatine) as creatine FROM meals WHERE date_entered = ? AND user_id = ?
        """
        result = self._db.q(query, (str(date), user_id))
        return self.__nutritional_info_from_row(result[0])

    def insert_meal(
        self,
        meal_description: str,
        meal: dm.MealBreakdown | dm.NutritionalInformation,
        meal_date: str,
        meal_time: str,
        user_id: int,
        summary: str = None,
        ingredients: str = None,
        is_supplement: bool = False
    ):
        try:
            self._db.t.meals.insert(
                date_entered=meal_date,
                meal_time=meal_time,
                user_description=meal_description,
                llm_summary=summary,
                ingredients=ingredients,
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
                is_supplement=is_supplement,
                user_id=user_id
            )
        except Exception as e:
            logging.error(f"Error inserting meal: {e}")
            raise e

    def get_profile_data(self, user_id: int) -> dict:
        query = """
            SELECT name, email, date_of_birth, units, gender, dietary_restrictions, 
                   activity_level, onboarding_stage
            FROM profile
            WHERE user_id = ?
        """
        result = self._db.q(query, (user_id,))
        if result:
            result = result[0]
            return {
                "name": result["name"],
                "email": result["email"],
                "date_of_birth": result["date_of_birth"],
                "units": result["units"],
                "gender": result["gender"],
                "dietary_restrictions": result["dietary_restrictions"],
                "activity_level": result["activity_level"],
                "onboarding_stage": result["onboarding_stage"]
            }
        return {}

    def get_dietary_restrictions(self, user_id: int):
        query = "SELECT dietary_restrictions FROM profile WHERE user_id = ?"
        result = self._db.q(query, (user_id,))
        return result[0]["dietary_restrictions"] if result else None

    def insert_supplement(
        self,
        name: str,
        consumption_time: str,
        nutritional_info: dm.NutritionalInformation,
        date: str,
        user_id: int
    ):
        self._db.t.supplements.insert(
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
        self.insert_meal(
            meal_description=name,
            meal=nutritional_info,
            meal_date=date,
            meal_time=consumption_time,
            user_id=user_id,
            is_supplement=True
        )

    def log_supplement_consumption(
        self,
        user_id: int,
        supplement_name: str,
        servings: float,
        time_consumed: str
    ):
        self._db.t.supplement_entries.insert(
            user_id=user_id,
            supplement_name=supplement_name,
            date_consumed=datetime.date(datetime.today()),
            time_consumed=time_consumed,
            servings=servings,
        )

    def get_supplement(self, name: str, user_id: int) -> dm.NutritionalInformation | None:
        query = """
            SELECT calories, protein, carbohydrates, fat, fiber, vitamin_a, vitamin_c, vitamin_d,
                   calcium, iron, potassium, sodium
            FROM supplements WHERE name = ? AND user_id = ?
        """

        result = self._db.q(query, (name, user_id))
        return self.__nutritional_info_from_row(result)

    def get_supplement_names(self, user_id: int) -> list[str]:
        """
        Get all supplement names from the database.
        """
        result = self._db.q("SELECT name FROM supplements WHERE user_id = ?", (user_id,))
        return [row["name"] for row in result]

    def get_all_supplements(self, user_id: int) -> list[tuple[str, str, dm.NutritionalInformation]]:
        """
        Get all supplements and their nutritional information.
        Returns a list of tuples: (name, description, NutritionalInformation).
        """
        query = """
        SELECT name, description, calories, protein, carbohydrates, fat, fiber, vitamin_a,
        vitamin_c, vitamin_d, calcium, iron, potassium, sodium FROM supplements WHERE user_id = ?
        """
        results = self._db.q(query, (user_id,))
        return [(row["name"], row["description"], self.__nutritional_info_from_row(row)) for row in results]

    def get_daily_supplement_entries(
        self,
        user_id: int,
        date: datetime
    ) -> list[tuple[str, float, str]]:
        query = """
            SELECT supplement_name, servings, time_consumed FROM supplement_entries
            WHERE user_id = ? AND date_consumed = ? ORDER BY time_consumed
        """
        results = self._db.q(query, (user_id, date))
        return [(row["supplement_name"], row["servings"], row["time_consumed"]) for row in results]

    def insert_water_consumption(
        self,
        water_consumed_ml: float,
        date_consumed: datetime,
        time_consumed: str,
        user_id: int
    ):
        self._db.t.water.insert(
            date=date_consumed, time=time_consumed, water_consumed_ml=water_consumed_ml, user_id=user_id
        )

    def get_daily_water_consumption(self, date: datetime, user_id: int) -> float:
        query = "SELECT SUM(water_consumed_ml) FROM water WHERE date = ? AND user_id = ?"
        result = self._db.q(query, (str(date), user_id))
        return result[0]["SUM(water_consumed_ml)"]

    def get_user_measurements(self, user_id: int) -> list[tuple[str, float, float]]:
        query = "SELECT datetime, weight, height FROM measurements WHERE user_id = ? ORDER BY datetime DESC"
        return self._db.q(query, (user_id,))

    def get_latest_user_measurements(self, user_id: int) -> dict | None:
        query = "SELECT weight, height FROM measurements WHERE user_id = ? ORDER BY datetime DESC LIMIT 1"
        result = self._db.q(query, (user_id,))
        return None if not result else {"weight": result[0]["weight"], "height": result[0]["height"]}

    def insert_user_measurements(self, height: float, weight: float, dt: datetime, user_id: int):
        try:
            self._db.t.measurements.insert(datetime=dt.isoformat(), height=height, weight=weight, user_id=user_id)
        except Exception as e:
            logging.error(f"Error inserting user measurements: {e}")
            raise e

    def delete_meal(self, meal_id: int) -> bool:
        try:
            self._db.t.meals.delete(meal_id)
            return True
        except Exception as e:
            logging.error(f"Error deleting meal: {e}")
            return False

    def insert_inventory_item(
        self, title: str, quantity: float,unit: str, category: str, user_id: int
    ):
        self._db.t.inventory.insert(
            title=title, quantity=quantity, unit=unit, category=category, user_id=user_id
        )

    def get_inventory(self, user_id: int) -> dict:
        query = "SELECT rowid, title, quantity, unit, category FROM inventory WHERE user_id = ?"
        result = self._db.q(query, (user_id,))
        results = {category: [] for category in dm.KITCHEN_ITEM_CATEGORIES}
        for row in result:
            results[row["category"]].append({
                "rowid": row["rowid"],
                "title": row["title"],
                "quantity": row["quantity"],
                "unit": row["unit"],
            })
        return results

    def get_weight_goal(self, user_id: int) -> float:
        result = self._db.q("SELECT weight_goal FROM profile WHERE user_id = ?", (user_id,))
        return result[0]["weight_goal"]

    def delete_inventory_item(self, rowid: int) -> bool:
        try:
            self._db.t.inventory.delete(rowid)
            return True
        except Exception as e:
            logging.error(f"Error deleting inventory item: {e}")
            return False
    
    def insert_profile(self, form_data: dict) -> bool:
        try:
            self._db.t.profile.insert(form_data)
            return True
        except Exception as e:
            logging.error(f"Error inserting profile: {e}")
            return False

    def update_profile(self, form_data: dict) -> bool:
        try:
            self._db.t.profile.update(form_data)
            return True
        except Exception as e:
            logging.error(f"Error updating profile: {e}")

    def insert_measurement(self, user_id: int, weight: float, date: datetime, height: float) -> bool:
        try:
            self._db.t.measurements.insert(user_id=user_id, weight=weight, datetime=date.isoformat(), height=height)
            return True
        except Exception as e:
            logging.error(f"Error inserting measurement: {e}")
            return False

    def __nutritional_info_from_row(self, result: dict) -> dm.NutritionalInformation:
        if result.get("calories") is None:
            for key in result:
                result[key] = 0

        return dm.NutritionalInformation(
            calories=result["calories"],
            macronutrients=dm.Macronutrients(
                protein=result["protein"],
                carbohydrates=dm.Carbohydrates(
                    total=result["carbohydrates"], fiber=result["fiber"], total_sugar=0, added_sugar=0
                ),
                fat=dm.Fats(total=result["fat"], saturated=0, trans=0),
            ),
            micronutrients=dm.Micronutrients(
                vitamin_a=result["vitamin_a"], vitamin_c=result["vitamin_c"], vitamin_d=result["vitamin_d"],
                calcium=result["calcium"], iron=result["iron"], potassium=result["potassium"], sodium=result["sodium"]
            ),
            conditional_nutrients=dm.ConditionalNutrients(creatine=result["creatine"])
        )
