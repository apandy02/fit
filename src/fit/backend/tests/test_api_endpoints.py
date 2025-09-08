import unittest
from datetime import date, datetime
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

import fit.ai.nutrition.data_models as dm
from fit.backend.main import app as api_app


def _make_breakdown() -> dm.MealBreakdown:
    return dm.MealBreakdown(
        title="Chicken Bowl",
        ingredients="chicken, rice, veggies",
        calories=600.0,
        macronutrients=dm.Macronutrients(
            protein=45.0,
            carbohydrates=dm.Carbohydrates(total=60.0, fiber=5.0, total_sugar=0.0, added_sugar=0.0),
            fat=dm.Fats(total=18.0, saturated=0.0, trans=0.0),
        ),
        micronutrients=dm.Micronutrients(
            vitamin_a=10.0,
            vitamin_c=20.0,
            vitamin_d=1.0,
            calcium=100.0,
            iron=5.0,
            potassium=300.0,
            sodium=700.0,
        ),
        conditional_nutrients=dm.ConditionalNutrients(creatine=0.0),
    )


class TestApiEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(api_app)
        # Login to get auth header
        resp = self.client.post("/auth/login", json={"user_id": 42})
        self.assertEqual(resp.status_code, 200)
        tok = resp.json()["access_token"]
        self.auth = {"Authorization": f"Bearer {tok}"}

    def test_login_and_refresh(self):
        resp = self.client.post("/auth/login", json={"user_id": 1})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("access_token", data)
        self.assertIn("refresh_token", data)
        r2 = self.client.post("/auth/refresh", json={"refresh_token": data["refresh_token"]})
        self.assertEqual(r2.status_code, 200)
        self.assertIn("access_token", r2.json())

    @patch("fit.api.app.database_service")
    def test_get_me(self, mock_db):
        mock_db.get_profile_data.return_value = {"email": "john@example.com", "name": "John"}
        resp = self.client.get("/me", headers=self.auth)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["email"], "john@example.com")
        self.assertEqual(resp.json()["name"], "John")

    @patch("fit.api.app.assistants")
    def test_analyze(self, mock_assistants):
        # Stub analyze to return a shape similar to ell response: .content[0].parsed
        breakdown = _make_breakdown()
        parsed_holder = MagicMock()
        parsed_holder.parsed = breakdown
        mock_assistants.natural_language_nutritional_breakdown.return_value = MagicMock(content=[parsed_holder])
        resp = self.client.post("/nutrition/analyze", headers=self.auth, json={"text": "chicken and rice"})
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["title"], "Chicken Bowl")
        self.assertEqual(body["protein"], 45.0)

    @patch("fit.api.app.database_service")
    def test_meals_crud(self, mock_db):
        day = date(2024, 10, 1)
        records = []

        def fake_get_daily_meals(d, uid):
            result = []
            for idx, r in enumerate(records, 1):
                result.append({
                    "meal": r["meal"],
                    "meal_time": r["meal_time"],
                    "rowid": idx,
                })
            return result

        def fake_insert_meal(meal_description, meal, meal_date, meal_time, user_id, summary=None, ingredients=None, is_supplement=False):
            records.append({
                "meal": meal,
                "meal_time": datetime.strptime(meal_time, "%H:%M").time(),
            })

        mock_db.get_daily_meals.side_effect = fake_get_daily_meals
        mock_db.insert_meal.side_effect = fake_insert_meal
        mock_db.delete_meal.return_value = True

        payload = {
            "title": "Chicken Bowl",
            "ingredients": "chicken, rice, veggies",
            "calories": 600.0,
            "protein": 45.0,
            "carbohydrates": 60.0,
            "fat": 18.0,
            "fiber": 5.0,
            "vitamin_a": 10.0,
            "vitamin_c": 20.0,
            "vitamin_d": 1.0,
            "calcium": 100.0,
            "iron": 5.0,
            "potassium": 300.0,
            "sodium": 700.0,
            "creatine": 0.0,
            "meal_time": "12:30",
            "date_entered": str(day),
        }
        r = self.client.post("/meals", headers=self.auth, json=payload)
        self.assertEqual(r.status_code, 201)
        created = r.json()
        self.assertIn("id", created)

        r2 = self.client.get(f"/meals?date_str={day.isoformat()}", headers=self.auth)
        self.assertEqual(r2.status_code, 200)
        meals = r2.json()
        self.assertEqual(len(meals), 1)
        self.assertEqual(meals[0]["item"]["title"], "Chicken Bowl")

        rid = meals[0]["id"]
        r3 = self.client.delete(f"/meals/{rid}", headers=self.auth)
        self.assertEqual(r3.status_code, 204)


if __name__ == "__main__":
    unittest.main()


