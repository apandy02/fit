from __future__ import annotations

from datetime import datetime

from sqlalchemy import text


class WaterRepository:
    def __init__(self, engine):
        self._engine = engine

    def insert_water_consumption(
        self,
        water_consumed_ml: float,
        date_consumed: datetime,
        time_consumed: str,
        user_id: int,
    ):
        sql = text(
            "INSERT INTO water (date, time, water_consumed_ml, user_id) VALUES (:d, :t, :m, :u)"
        )
        with self._engine.begin() as conn:
            conn.execute(
                sql,
                {
                    "d": date_consumed,
                    "t": time_consumed,
                    "m": water_consumed_ml,
                    "u": user_id,
                },
            )

    def get_daily_water_consumption(self, date: datetime, user_id: int) -> float:
        sql = text(
            "SELECT COALESCE(SUM(water_consumed_ml), 0) FROM water WHERE date = :d AND user_id = :u"
        )
        with self._engine.connect() as conn:
            row = conn.execute(sql, {"d": str(date), "u": user_id}).fetchone()
        return float(row[0] or 0)
