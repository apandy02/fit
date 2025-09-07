from __future__ import annotations

from datetime import datetime
from typing import Any
from decimal import Decimal

from sqlalchemy import text

import fit.ai.nutrition.data_models as dm
from .pg import get_engine


class PostgresDatabaseService:
    def __init__(self):
        self._engine = get_engine()

    def ensure_local_user(self, user_id: int) -> None:
        """Ensure a user row exists for local/dev logins.

        Creates a user with primary key equal to user_id and provider 'local'.
        Safe to call repeatedly.
        """
        sql = text(
            """
            INSERT INTO users (id, email, provider, provider_user_id)
            VALUES (:id, NULL, 'local', :puid)
            ON CONFLICT (id) DO NOTHING
            """
        )
        with self._engine.begin() as conn:
            conn.execute(sql, {"id": user_id, "puid": str(user_id)})

    def get_user_id(self, provider_user_id: str, provider: str) -> int | None:
        sql = text(
            """
            SELECT id FROM users
            WHERE provider_user_id = :puid AND provider = :prov
            LIMIT 1
            """
        )
        with self._engine.connect() as conn:
            row = conn.execute(sql, {"puid": provider_user_id, "prov": provider}).fetchone()
            return row[0] if row else None

    def insert_new_user(self, user_dict: dict) -> int:
        cols = ", ".join(user_dict.keys())
        params = {f"p_{k}": v for k, v in user_dict.items()}
        values = ", ".join(f":p_{k}" for k in user_dict.keys())
        sql = text(f"INSERT INTO users ({cols}) VALUES ({values}) RETURNING id")
        with self._engine.begin() as conn:
            return conn.execute(sql, params).scalar_one()

    def get_profile_data(self, user_id: int) -> dict:
        sql = text(
            """
            SELECT name, email, date_of_birth, units, gender, dietary_restrictions,
                   activity_level, onboarding_stage, weight_goal, fitness_goal
            FROM profile WHERE user_id = :uid
            """
        )
        with self._engine.connect() as conn:
            row = conn.execute(sql, {"uid": user_id}).fetchone()
            if not row:
                return {}
            keys = [
                "name",
                "email",
                "date_of_birth",
                "units",
                "gender",
                "dietary_restrictions",
                "activity_level",
                "onboarding_stage",
                "weight_goal",
                "fitness_goal",
            ]
            return {k: row[i] for i, k in enumerate(keys)}

    def get_dietary_restrictions(self, user_id: int):
        sql = text("SELECT dietary_restrictions FROM profile WHERE user_id = :uid")
        with self._engine.connect() as conn:
            row = conn.execute(sql, {"uid": user_id}).fetchone()
            return row[0] if row else None

    def insert_profile(self, form_data: dict) -> bool:
        cols = ", ".join(form_data.keys())
        params = {f"p_{k}": v for k, v in form_data.items()}
        values = ", ".join(f":p_{k}" for k in form_data.keys())
        sql = text(f"INSERT INTO profile ({cols}) VALUES ({values})")
        with self._engine.begin() as conn:
            conn.execute(sql, params)
        return True

    def update_profile(self, form_data: dict) -> bool:
        if "user_id" not in form_data:
            return False
        uid = form_data["user_id"]
        # Normalize weight_goal strings to numeric codes for storage (schema uses NUMERIC)
        normalized: dict[str, Any] = {}
        for key, value in form_data.items():
            if key == "user_id":
                continue
            if key == "weight_goal" and isinstance(value, str):
                v = value.strip().lower()
                mapping = {"lose": -1, "maintain": 0, "gain": 1}
                normalized[key] = mapping.get(v, 0)
            else:
                normalized[key] = value
        sets = ", ".join(f"{k} = :p_{k}" for k in normalized.keys())
        params = {f"p_{k}": v for k, v in normalized.items()}
        params["uid"] = uid
        sql = text(f"UPDATE profile SET {sets} WHERE user_id = :uid")
        with self._engine.begin() as conn:
            conn.execute(sql, params)
        return True

    def __nutritional_info_from_row(self, result: dict[str, Any]) -> dm.NutritionalInformation:
        defaults = {
            "calories": 0,
            "protein": 0,
            "carbohydrates": 0,
            "fat": 0,
            "fiber": 0,
            "vitamin_a": 0,
            "vitamin_c": 0,
            "vitamin_d": 0,
            "calcium": 0,
            "iron": 0,
            "potassium": 0,
            "sodium": 0,
            "creatine": 0,
        }
        data = {**defaults, **{k: result[k] for k in defaults if k in result}}
        return dm.NutritionalInformation(
            calories=data["calories"],
            macronutrients=dm.Macronutrients(
                protein=data["protein"],
                carbohydrates=dm.Carbohydrates(
                    total=data["carbohydrates"], fiber=data["fiber"], total_sugar=0, added_sugar=0
                ),
                fat=dm.Fats(total=data["fat"], saturated=0, trans=0),
            ),
            micronutrients=dm.Micronutrients(
                vitamin_a=data["vitamin_a"],
                vitamin_c=data["vitamin_c"],
                vitamin_d=data["vitamin_d"],
                calcium=data["calcium"],
                iron=data["iron"],
                potassium=data["potassium"],
                sodium=data["sodium"],
            ),
            conditional_nutrients=dm.ConditionalNutrients(creatine=data.get("creatine", 0)),
        )

    def get_daily_meals(self, date: datetime, user_id: int) -> list[dict]:
        sql = text(
            """
            SELECT id, llm_summary, ingredients, meal_time, calories, protein, carbohydrates,
                   fat, fiber, vitamin_a, vitamin_c, vitamin_d, calcium, iron, potassium, sodium, creatine
            FROM meals
            WHERE date_entered = :d AND is_supplement = false AND user_id = :u
            ORDER BY meal_time ASC
            """
        )
        with self._engine.connect() as conn:
            rows = conn.execute(sql, {"d": str(date), "u": user_id}).fetchall()
        meals: list[dict] = []
        for row in rows:
            nutritional_info = self.__nutritional_info_from_row(dict(row._mapping))
            meal = dm.MealBreakdown(
                title=row.llm_summary,
                ingredients=row.ingredients,
                calories=row.calories,
                macronutrients=nutritional_info.macronutrients,
                micronutrients=nutritional_info.micronutrients,
                conditional_nutrients=nutritional_info.conditional_nutrients,
            )
            meal_time = row.meal_time
            if isinstance(meal_time, str):
                try:
                    meal_time = datetime.strptime(meal_time, "%H:%M:%S").time()
                except ValueError:
                    try:
                        meal_time = datetime.strptime(meal_time, "%H:%M").time()
                    except ValueError:
                        meal_time = datetime.fromisoformat(meal_time).time()
            meals.append({"meal": meal, "meal_time": meal_time, "rowid": row.id})
        return meals

    def get_all_meal_summaries(self, user_id: int):
        sql = text("SELECT llm_summary FROM meals WHERE user_id = :u")
        with self._engine.connect() as conn:
            return [r[0] for r in conn.execute(sql, {"u": user_id}).fetchall()]

    def get_daily_cumulative_nutrition(self, date: datetime, user_id: int) -> dm.NutritionalInformation:
        sql = text(
            """
            SELECT 
              COALESCE(SUM(calories), 0) as calories,
              COALESCE(SUM(protein), 0) as protein,
              COALESCE(SUM(carbohydrates), 0) as carbohydrates,
              COALESCE(SUM(fat), 0) as fat,
              COALESCE(SUM(fiber), 0) as fiber,
              COALESCE(SUM(vitamin_a), 0) as vitamin_a,
              COALESCE(SUM(vitamin_c), 0) as vitamin_c,
              COALESCE(SUM(vitamin_d), 0) as vitamin_d,
              COALESCE(SUM(calcium), 0) as calcium,
              COALESCE(SUM(iron), 0) as iron,
              COALESCE(SUM(potassium), 0) as potassium,
              COALESCE(SUM(sodium), 0) as sodium,
              COALESCE(SUM(creatine), 0) as creatine
            FROM meals
            WHERE date_entered = :d AND user_id = :u
            """
        )
        with self._engine.connect() as conn:
            row = conn.execute(sql, {"d": str(date), "u": user_id}).fetchone()
        return self.__nutritional_info_from_row(dict(row._mapping))

    def insert_meal(
        self,
        meal_description: str,
        meal: dm.MealBreakdown | dm.NutritionalInformation,
        meal_date: str,
        meal_time: str,
        user_id: int,
        summary: str | None = None,
        ingredients: str | None = None,
        is_supplement: bool = False,
    ):
        sql = text(
            """
            INSERT INTO meals (
              user_id, date_entered, meal_time, user_description, llm_summary, ingredients,
              calories, protein, carbohydrates, fat, fiber, vitamin_a, vitamin_c, vitamin_d,
              calcium, iron, potassium, sodium, creatine, is_supplement
            ) VALUES (
              :user_id, :date_entered, :meal_time, :user_description, :llm_summary, :ingredients,
              :calories, :protein, :carbohydrates, :fat, :fiber, :vitamin_a, :vitamin_c, :vitamin_d,
              :calcium, :iron, :potassium, :sodium, :creatine, :is_supplement
            ) RETURNING id
            """
        )
        params = {
            "user_id": user_id,
            "date_entered": meal_date,
            "meal_time": meal_time,
            "user_description": meal_description,
            "llm_summary": summary,
            "ingredients": ingredients,
            "calories": meal.calories,
            "protein": meal.macronutrients.protein,
            "carbohydrates": meal.macronutrients.carbohydrates.total,
            "fat": meal.macronutrients.fat.total,
            "fiber": meal.macronutrients.carbohydrates.fiber,
            "vitamin_a": meal.micronutrients.vitamin_a,
            "vitamin_c": meal.micronutrients.vitamin_c,
            "vitamin_d": meal.micronutrients.vitamin_d,
            "calcium": meal.micronutrients.calcium,
            "iron": meal.micronutrients.iron,
            "potassium": meal.micronutrients.potassium,
            "sodium": meal.micronutrients.sodium,
            "creatine": getattr(meal.conditional_nutrients, "creatine", 0),
            "is_supplement": is_supplement,
        }
        with self._engine.begin() as conn:
            conn.execute(sql, params).scalar_one()

    def delete_meal(self, meal_id: int) -> bool:
        sql = text("DELETE FROM meals WHERE id = :id")
        with self._engine.begin() as conn:
            res = conn.execute(sql, {"id": meal_id})
            return res.rowcount > 0

    def insert_supplement(self, name: str, consumption_time: str, nutritional_info: dm.NutritionalInformation, date: str, user_id: int):
        sql = text(
            """
            INSERT INTO supplements (
              user_id, name, calories, protein, carbohydrates, fat, fiber,
              vitamin_a, vitamin_c, vitamin_d, calcium, iron, potassium, sodium
            ) VALUES (
              :user_id, :name, :calories, :protein, :carbohydrates, :fat, :fiber,
              :vitamin_a, :vitamin_c, :vitamin_d, :calcium, :iron, :potassium, :sodium
            ) ON CONFLICT (user_id, name) DO NOTHING
            """
        )
        params = {
            "user_id": user_id,
            "name": name,
            "calories": nutritional_info.calories,
            "protein": nutritional_info.macronutrients.protein,
            "carbohydrates": nutritional_info.macronutrients.carbohydrates.total,
            "fat": nutritional_info.macronutrients.fat.total,
            "fiber": nutritional_info.macronutrients.carbohydrates.fiber,
            "vitamin_a": nutritional_info.micronutrients.vitamin_a,
            "vitamin_c": nutritional_info.micronutrients.vitamin_c,
            "vitamin_d": nutritional_info.micronutrients.vitamin_d,
            "calcium": nutritional_info.micronutrients.calcium,
            "iron": nutritional_info.micronutrients.iron,
            "potassium": nutritional_info.micronutrients.potassium,
            "sodium": nutritional_info.micronutrients.sodium,
        }
        with self._engine.begin() as conn:
            conn.execute(sql, params)
        # also log as a meal for now
        self.insert_meal(name, nutritional_info, date, consumption_time, user_id, is_supplement=True)

    def get_supplement(self, name: str, user_id: int) -> dm.NutritionalInformation | None:
        sql = text(
            """
            SELECT calories, protein, carbohydrates, fat, fiber, vitamin_a, vitamin_c, vitamin_d,
                   calcium, iron, potassium, sodium
            FROM supplements WHERE name = :n AND user_id = :u
            LIMIT 1
            """
        )
        with self._engine.connect() as conn:
            row = conn.execute(sql, {"n": name, "u": user_id}).fetchone()
            return None if not row else self.__nutritional_info_from_row(dict(row._mapping))

    def get_supplement_names(self, user_id: int) -> list[str]:
        sql = text("SELECT name FROM supplements WHERE user_id = :u")
        with self._engine.connect() as conn:
            return [r[0] for r in conn.execute(sql, {"u": user_id}).fetchall()]

    def log_supplement_consumption(self, user_id: int, supplement_name: str, servings: float, time_consumed: str):
        # Resolve supplement id
        sql_id = text("SELECT id FROM supplements WHERE user_id = :u AND name = :n LIMIT 1")
        with self._engine.connect() as conn:
            row = conn.execute(sql_id, {"u": user_id, "n": supplement_name}).fetchone()
        if not row:
            raise ValueError("Supplement not found")
        supp_id = row[0]

        sql = text(
            """
            INSERT INTO supplement_entries (user_id, supplement_id, date_consumed, time_consumed, servings)
            VALUES (:u, :sid, :d, :t, :s)
            """
        )
        with self._engine.begin() as conn:
            conn.execute(sql, {"u": user_id, "sid": supp_id, "d": datetime.today().date(), "t": time_consumed, "s": servings})

    def get_all_supplements(self, user_id: int) -> list[tuple[str, str, dm.NutritionalInformation]]:
        sql = text(
            """
            SELECT name, description, calories, protein, carbohydrates, fat, fiber, vitamin_a, vitamin_c, vitamin_d, calcium, iron, potassium, sodium
            FROM supplements WHERE user_id = :u
            """
        )
        with self._engine.connect() as conn:
            rows = conn.execute(sql, {"u": user_id}).fetchall()
        return [(r.name, r.description, self.__nutritional_info_from_row(dict(r._mapping))) for r in rows]

    def get_daily_supplement_entries(self, user_id: int, date: datetime) -> list[tuple[str, float, str]]:
        sql = text(
            """
            SELECT s.name AS supplement_name, e.servings, e.time_consumed
            FROM supplement_entries e
            JOIN supplements s ON e.supplement_id = s.id
            WHERE e.user_id = :u AND e.date_consumed = :d
            ORDER BY e.time_consumed
            """
        )
        with self._engine.connect() as conn:
            rows = conn.execute(sql, {"u": user_id, "d": date}).fetchall()
        return [(r.supplement_name, r.servings, r.time_consumed) for r in rows]

    def insert_water_consumption(self, water_consumed_ml: float, date_consumed: datetime, time_consumed: str, user_id: int):
        sql = text("INSERT INTO water (date, time, water_consumed_ml, user_id) VALUES (:d, :t, :m, :u)")
        with self._engine.begin() as conn:
            conn.execute(sql, {"d": date_consumed, "t": time_consumed, "m": water_consumed_ml, "u": user_id})

    def get_daily_water_consumption(self, date: datetime, user_id: int) -> float:
        sql = text("SELECT COALESCE(SUM(water_consumed_ml), 0) FROM water WHERE date = :d AND user_id = :u")
        with self._engine.connect() as conn:
            row = conn.execute(sql, {"d": str(date), "u": user_id}).fetchone()
        return float(row[0] or 0)

    def get_user_measurements(self, user_id: int):
        sql = text("SELECT datetime, weight, height FROM measurements WHERE user_id = :u ORDER BY datetime DESC")
        with self._engine.connect() as conn:
            return [dict(r._mapping) for r in conn.execute(sql, {"u": user_id}).fetchall()]

    def get_latest_user_measurements(self, user_id: int) -> dict | None:
        sql = text("SELECT weight, height FROM measurements WHERE user_id = :u ORDER BY datetime DESC LIMIT 1")
        with self._engine.connect() as conn:
            row = conn.execute(sql, {"u": user_id}).fetchone()
        return None if not row else {"weight": row[0], "height": row[1]}

    def insert_user_measurements(self, height: float, weight: float, dt: datetime, user_id: int):
        sql = text("INSERT INTO measurements (datetime, height, weight, user_id) VALUES (:dt, :h, :w, :u)")
        with self._engine.begin() as conn:
            conn.execute(sql, {"dt": dt.isoformat(), "h": height, "w": weight, "u": user_id})

    def insert_measurement(self, user_id: int, weight: float, date: datetime, height: float) -> bool:
        self.insert_user_measurements(height=height, weight=weight, dt=date, user_id=user_id)
        return True

    def insert_inventory_item(self, title: str, quantity: float, unit: str, category: str, user_id: int):
        sql = text("INSERT INTO inventory (title, quantity, unit, category, user_id) VALUES (:t, :q, :u, :c, :uid)")
        with self._engine.begin() as conn:
            conn.execute(sql, {"t": title, "q": quantity, "u": unit, "c": category, "uid": user_id})

    def get_inventory(self, user_id: int) -> dict:
        sql = text("SELECT id, title, quantity, unit, category FROM inventory WHERE user_id = :u")
        with self._engine.connect() as conn:
            rows = conn.execute(sql, {"u": user_id}).fetchall()
        results: dict[str, list[dict]] = {category: [] for category in dm.KITCHEN_ITEM_CATEGORIES}
        for r in rows:
            results[r.category].append({"rowid": r.id, "title": r.title, "quantity": r.quantity, "unit": r.unit})
        return results

    def get_weight_goal(self, user_id: int) -> str:
        """Return the user's weight goal as a string understood by WeightGoal enum.

        Falls back to "maintain" if not set or no profile row exists.
        """
        sql = text("SELECT weight_goal FROM profile WHERE user_id = :u")
        with self._engine.connect() as conn:
            row = conn.execute(sql, {"u": user_id}).fetchone()
        if not row or row[0] is None:
            return "maintain"
        val = row[0]

        # If stored as numeric, map codes back to strings
        if isinstance(val, (int, float, Decimal)):
            try:
                num = float(val)
            except Exception:
                return "maintain"
            if num <= -0.5:
                return "lose"
            if num >= 0.5:
                return "gain"
            return "maintain"
        return "maintain"  # TODO: make clearner with enum

    def delete_inventory_item(self, rowid: int) -> bool:
        sql = text("DELETE FROM inventory WHERE id = :id")
        with self._engine.begin() as conn:
            res = conn.execute(sql, {"id": rowid})
            return res.rowcount > 0

    def create_oauth_state(self, state: str, code_verifier: str, provider: str, user_id: int | None, redirect_to: str | None, created_at: str, expires_at: str):
        sql = text(
            """
            INSERT INTO oauth_state (state, code_verifier, provider, user_id, redirect_to, created_at, expires_at)
            VALUES (:s, :cv, :p, :u, :r, :c, :e)
            """
        )
        with self._engine.begin() as conn:
            conn.execute(sql, {"s": state, "cv": code_verifier, "p": provider, "u": user_id, "r": redirect_to, "c": created_at, "e": expires_at})

    def consume_oauth_state(self, state: str) -> dict | None:
        with self._engine.begin() as conn:
            row = conn.execute(text("SELECT * FROM oauth_state WHERE state = :s"), {"s": state}).fetchone()
            if not row:
                return None
            conn.execute(text("DELETE FROM oauth_state WHERE state = :s"), {"s": state})
            return dict(row._mapping)

    def upsert_tracker_account(self, user_id: int, provider: str, provider_user_id: str, access_token: str, refresh_token: str | None, expires_at: str | None, scopes: str | None, primary: bool = False):
        with self._engine.begin() as conn:
            existing = conn.execute(text("SELECT id FROM tracker_accounts WHERE user_id = :u AND provider = :p AND provider_user_id = :puid"), {"u": user_id, "p": provider, "puid": provider_user_id}).fetchone()
            if existing:
                conn.execute(text("UPDATE tracker_accounts SET access_token = :a, refresh_token = :r, expires_at = :e, scopes = :s WHERE id = :id"), {"a": access_token, "r": refresh_token, "e": expires_at, "s": scopes, "id": existing[0]})
            else:
                conn.execute(text("""
                    INSERT INTO tracker_accounts (user_id, provider, provider_user_id, access_token, refresh_token, expires_at, scopes, primary, linked_at)
                    VALUES (:u, :p, :puid, :a, :r, :e, :s, :pri, :lnk)
                """), {"u": user_id, "p": provider, "puid": provider_user_id, "a": access_token, "r": refresh_token, "e": expires_at, "s": scopes, "pri": primary, "lnk": datetime.now().isoformat()})
            if primary:
                conn.execute(text("UPDATE tracker_accounts SET primary = false WHERE user_id = :u AND provider != :p"), {"u": user_id, "p": provider})

    def get_tracker_account(self, user_id: int, provider: str | None = None, primary_only: bool = True) -> dict | None:
        with self._engine.connect() as conn:
            if provider:
                row = conn.execute(text("SELECT * FROM tracker_accounts WHERE user_id = :u AND provider = :p ORDER BY primary DESC LIMIT 1"), {"u": user_id, "p": provider}).fetchone()
            elif primary_only:
                row = conn.execute(text("SELECT * FROM tracker_accounts WHERE user_id = :u AND primary = true LIMIT 1"), {"u": user_id}).fetchone()
            else:
                row = conn.execute(text("SELECT * FROM tracker_accounts WHERE user_id = :u ORDER BY linked_at DESC LIMIT 1"), {"u": user_id}).fetchone()
            return None if not row else dict(row._mapping)

    def list_tracker_accounts(self, user_id: int) -> list[dict]:
        with self._engine.connect() as conn:
            rows = conn.execute(text("SELECT provider, provider_user_id, expires_at, scopes, primary, linked_at FROM tracker_accounts WHERE user_id = :u"), {"u": user_id}).fetchall()
            return [dict(r._mapping) for r in rows]

    def set_primary_tracker(self, user_id: int, provider: str):
        with self._engine.begin() as conn:
            conn.execute(text("UPDATE tracker_accounts SET primary = false WHERE user_id = :u"), {"u": user_id})
            conn.execute(text("UPDATE tracker_accounts SET primary = true WHERE user_id = :u AND provider = :p"), {"u": user_id, "p": provider})

    def update_tracker_tokens(self, user_id: int, provider: str, access_token: str, refresh_token: str | None, expires_at: str | None):
        with self._engine.begin() as conn:
            conn.execute(text("UPDATE tracker_accounts SET access_token = :a, refresh_token = :r, expires_at = :e WHERE user_id = :u AND provider = :p"), {"a": access_token, "r": refresh_token, "e": expires_at, "u": user_id, "p": provider})


