from __future__ import annotations

from datetime import datetime
from sqlalchemy import text


class MeasurementsRepository:
    def __init__(self, engine):
        self._engine = engine

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


