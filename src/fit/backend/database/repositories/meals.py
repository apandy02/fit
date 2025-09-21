from __future__ import annotations

from datetime import datetime
from sqlalchemy import text

import fit.ai.nutrition.data_models as dm
from fit.backend.database.mappers import nutritional_info_from_row


class MealsRepository:
    def __init__(self, engine):
        self._engine = engine

    def get_daily_meals(self, date: datetime, user_id: int) -> list[dict]:
        sql = text(
            """
            SELECT id, llm_summary, ingredients, meal_time, calories, protein, carbohydrates,
                   fat, fiber, vitamin_a, vitamin_c, vitamin_d, calcium, iron, potassium, sodium, creatine,
                   calories_unit, protein_unit, carbohydrates_unit, fat_unit, fiber_unit,
                   vitamin_a_unit, vitamin_c_unit, vitamin_d_unit, calcium_unit, iron_unit,
                   potassium_unit, sodium_unit, creatine_unit
            FROM meals
            WHERE date_entered = :d AND is_supplement = false AND user_id = :u
            ORDER BY meal_time ASC
            """
        )
        with self._engine.connect() as conn:
            rows = conn.execute(sql, {"d": str(date), "u": user_id}).fetchall()
        meals: list[dict] = []
        for row in rows:
            nutritional_info = nutritional_info_from_row(dict(row._mapping))
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

    def get_daily_cumulative_nutrition(
        self, date: datetime, user_id: int
    ) -> dm.NutritionalInformation:
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
        return nutritional_info_from_row(dict(row._mapping))

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
              calcium, iron, potassium, sodium, creatine, is_supplement,
              calories_unit, protein_unit, carbohydrates_unit, fat_unit, fiber_unit,
              vitamin_a_unit, vitamin_c_unit, vitamin_d_unit, calcium_unit, iron_unit,
              potassium_unit, sodium_unit, creatine_unit
            ) VALUES (
              :user_id, :date_entered, :meal_time, :user_description, :llm_summary, :ingredients,
              :calories, :protein, :carbohydrates, :fat, :fiber, :vitamin_a, :vitamin_c, :vitamin_d,
              :calcium, :iron, :potassium, :sodium, :creatine, :is_supplement,
              :calories_unit, :protein_unit, :carbohydrates_unit, :fat_unit, :fiber_unit,
              :vitamin_a_unit, :vitamin_c_unit, :vitamin_d_unit, :calcium_unit, :iron_unit,
              :potassium_unit, :sodium_unit, :creatine_unit
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
            # canonical units
            "calories_unit": "kcal",
            "protein_unit": "g",
            "carbohydrates_unit": "g",
            "fat_unit": "g",
            "fiber_unit": "g",
            "vitamin_a_unit": "ug",
            "vitamin_c_unit": "mg",
            "vitamin_d_unit": "ug",
            "calcium_unit": "mg",
            "iron_unit": "mg",
            "potassium_unit": "mg",
            "sodium_unit": "mg",
            "creatine_unit": "g",
        }
        with self._engine.begin() as conn:
            conn.execute(sql, params).scalar_one()

    def delete_meal(self, meal_id: int) -> bool:
        sql = text("DELETE FROM meals WHERE id = :id")
        with self._engine.begin() as conn:
            res = conn.execute(sql, {"id": meal_id})
            return res.rowcount > 0
