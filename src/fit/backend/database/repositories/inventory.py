from __future__ import annotations

from sqlalchemy import text

import fit.ai.nutrition.data_models as dm


class InventoryRepository:
    def __init__(self, engine):
        self._engine = engine

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

    def delete_inventory_item(self, rowid: int) -> bool:
        sql = text("DELETE FROM inventory WHERE id = :id")
        with self._engine.begin() as conn:
            res = conn.execute(sql, {"id": rowid})
            return res.rowcount > 0


