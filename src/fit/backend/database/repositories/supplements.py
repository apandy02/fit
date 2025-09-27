from __future__ import annotations

from datetime import datetime

from sqlalchemy import text

import fit.ai.nutrition.data_models as dm
from fit.backend.database.mappers import nutritional_info_from_row


class SupplementsRepository:
    def __init__(self, engine):
        self._engine = engine

    def insert_supplement(
        self, name: str, nutritional_info: dm.NutritionalInformation, user_id: int
    ):
        sql = text(
            """
            INSERT INTO supplements (
              user_id, name, calories, protein, carbohydrates, fat, fiber,
              vitamin_a, vitamin_c, vitamin_d, calcium, iron, potassium, sodium,
              calories_unit, protein_unit, carbohydrates_unit, fat_unit, fiber_unit,
              vitamin_a_unit, vitamin_c_unit, vitamin_d_unit, calcium_unit, iron_unit,
              potassium_unit, sodium_unit
            ) VALUES (
              :user_id, :name, :calories, :protein, :carbohydrates, :fat, :fiber,
              :vitamin_a, :vitamin_c, :vitamin_d, :calcium, :iron, :potassium, :sodium,
              :calories_unit, :protein_unit, :carbohydrates_unit, :fat_unit, :fiber_unit,
              :vitamin_a_unit, :vitamin_c_unit, :vitamin_d_unit, :calcium_unit, :iron_unit,
              :potassium_unit, :sodium_unit
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
        }
        with self._engine.begin() as conn:
            conn.execute(sql, params)

    def get_supplement(
        self, name: str, user_id: int
    ) -> dm.NutritionalInformation | None:
        sql = text(
            """
            SELECT calories, protein, carbohydrates, fat, fiber, vitamin_a, vitamin_c, vitamin_d,
                   calcium, iron, potassium, sodium,
                   calories_unit, protein_unit, carbohydrates_unit, fat_unit, fiber_unit,
                   vitamin_a_unit, vitamin_c_unit, vitamin_d_unit, calcium_unit, iron_unit,
                   potassium_unit, sodium_unit
            FROM supplements WHERE name = :n AND user_id = :u
            LIMIT 1
            """
        )
        with self._engine.connect() as conn:
            row = conn.execute(sql, {"n": name, "u": user_id}).fetchone()
            return None if not row else nutritional_info_from_row(dict(row._mapping))

    def get_supplement_names(self, user_id: int) -> list[str]:
        sql = text("SELECT name FROM supplements WHERE user_id = :u")
        with self._engine.connect() as conn:
            return [r[0] for r in conn.execute(sql, {"u": user_id}).fetchall()]

    def log_supplement_consumption(
        self, user_id: int, supplement_name: str, servings: float, time_consumed: str
    ):
        sql_id = text(
            "SELECT id FROM supplements WHERE user_id = :u AND name = :n LIMIT 1"
        )
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
            conn.execute(
                sql,
                {
                    "u": user_id,
                    "sid": supp_id,
                    "d": datetime.today().date(),
                    "t": time_consumed,
                    "s": servings,
                },
            )

    def get_all_supplements(
        self, user_id: int
    ) -> list[tuple[str, str, dm.NutritionalInformation]]:
        sql = text(
            """
            SELECT name, description, calories, protein, carbohydrates, fat, fiber, vitamin_a, vitamin_c, vitamin_d, calcium, iron, potassium, sodium,
                   calories_unit, protein_unit, carbohydrates_unit, fat_unit, fiber_unit,
                   vitamin_a_unit, vitamin_c_unit, vitamin_d_unit, calcium_unit, iron_unit,
                   potassium_unit, sodium_unit
            FROM supplements WHERE user_id = :u
            """
        )
        with self._engine.connect() as conn:
            rows = conn.execute(sql, {"u": user_id}).fetchall()
        return [
            (r.name, r.description, nutritional_info_from_row(dict(r._mapping)))
            for r in rows
        ]

    def get_daily_supplement_entries(
        self, user_id: int, date: datetime
    ) -> list[tuple[str, float, str]]:
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
