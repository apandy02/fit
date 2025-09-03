import unittest
from unittest.mock import MagicMock, patch

from fit.backend.database.database import DatabaseService, dm
from fit.backend.database.schema import Inventory, User


class TestDatabaseService(unittest.TestCase):
    def setUp(self):
        self.db_path = "test.db"
        self.mock_db = MagicMock()
        self.mock_db.t = MagicMock()
        tables = [
            ("users", User, ["provider_user_id", "provider"], "user_id"),
            ("inventory", Inventory, ["user_id"], "rowid"),
        ]
        with patch('fasthtml.common.database', return_value=self.mock_db):
            self.db_service = DatabaseService(self.db_path, tables)
            
    def test_get_inventory_empty(self):
        """Test get_inventory when no items are present"""
        self.db_service._db.q.return_value = []
        result = self.db_service.get_inventory(user_id=1)
        self.db_service._db.q.assert_called_once_with(
            "SELECT rowid, title, quantity, unit, category FROM inventory WHERE user_id = ?",
            (1,)
        )
        self.assertEqual(len(result), len(dm.KITCHEN_ITEM_CATEGORIES))
        for category in dm.KITCHEN_ITEM_CATEGORIES:
            self.assertIn(category, result)
            self.assertEqual(result[category], [])

    def test_get_inventory_with_items(self):
        """Test get_inventory when items are present"""
        mock_items = [
            {
                "rowid": 1,
                "title": "Apples",
                "quantity": 5,
                "unit": "pieces",
                "category": "Produce"
            },
            {
                "rowid": 2,
                "title": "Chicken",
                "quantity": 500,
                "unit": "grams",
                "category": "Meats & Fish"
            },
            {
                "rowid": 3,
                "title": "Rice",
                "quantity": 1,
                "unit": "kg",
                "category": "Bread & Grains"
            }
        ]
        self.db_service._db.q.return_value = mock_items
        result = self.db_service.get_inventory(user_id=1)
        self.db_service._db.q.assert_called_once_with(
            "SELECT rowid, title, quantity, unit, category FROM inventory WHERE user_id = ?",
            (1,)
        )
        
        self.assertEqual(len(result), len(dm.KITCHEN_ITEM_CATEGORIES))
        
        self.assertEqual(len(result["Produce"]), 1)
        self.assertEqual(len(result["Meats & Fish"]), 1)
        self.assertEqual(len(result["Bread & Grains"]), 1)
        
        apple = result["Produce"][0]
        self.assertEqual(apple["rowid"], 1)
        self.assertEqual(apple["title"], "Apples")
        self.assertEqual(apple["quantity"], 5)
        self.assertEqual(apple["unit"], "pieces")
        
        chicken = result["Meats & Fish"][0]
        self.assertEqual(chicken["rowid"], 2)
        self.assertEqual(chicken["title"], "Chicken")
        self.assertEqual(chicken["quantity"], 500)
        self.assertEqual(chicken["unit"], "grams")
        
        rice = result["Bread & Grains"][0]
        self.assertEqual(rice["rowid"], 3)
        self.assertEqual(rice["title"], "Rice")
        self.assertEqual(rice["quantity"], 1)
        self.assertEqual(rice["unit"], "kg")


if __name__ == '__main__':
    unittest.main() 
