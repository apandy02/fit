from __future__ import annotations

from typing import Any

from sqlalchemy import text


class ProfileRepository:
    def __init__(self, engine):
        self._engine = engine

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

    def get_weight_goal(self, user_id: int):
        from decimal import Decimal

        sql = text("SELECT weight_goal FROM profile WHERE user_id = :u")
        with self._engine.connect() as conn:
            row = conn.execute(sql, {"u": user_id}).fetchone()
        if not row or row[0] is None:
            return "maintain"
        val = row[0]
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
        return "maintain"


