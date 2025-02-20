import unittest
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch

import fasthtml.common as fh
from PIL import Image

from fit.nutrition.data_models import (ConditionalNutrients, Macronutrients,
                                       MealBreakdown, MealRecommendation,
                                       Micronutrients, Recommendations)
from fit.web.nutrition import requests as nutrition_requests

MOCK_SESSION = {
    "user_id": 42,
    "tracker": "whoop",
    "access_token": "mock_token"
}

MOCK_DAILY_NUTRITION = {
    "calories": {"consumed": [2000], "goal": [2500], "burned": [2300]},
    "protein": {"consumed": [150], "goal": [180]},
    "carbohydrates": {"consumed": [200], "goal": [250]},
    "fat": {"consumed": [70], "goal": [80]},
    "vitamin_a": {"consumed": [5000], "goal": [5000]},
    "vitamin_c": {"consumed": [60], "goal": [90]},
    "iron": {"consumed": [18], "goal": [18]},
    "calcium": {"consumed": [1000], "goal": [1000]},
    "water": {"consumed": [2000], "goal": [3000]},
    "creatine": {"consumed": [2.0], "goal": [5.0]}
}

MOCK_MEAL = MealBreakdown(
    title="Test Meal",
    ingredients="Test ingredients",
    calories=500,
    macronutrients=Macronutrients(
        protein=30,
        carbohydrates={"total": 50, "fiber": 5, "total_sugar": 10, "added_sugar": 5},
        fat={"total": 20, "saturated": 5, "trans": 0}
    ),
    micronutrients=Micronutrients(
        vitamin_a=1000,
        vitamin_c=30,
        vitamin_d=400,
        calcium=200,
        iron=3,
        potassium=300,
        sodium=400
    ),
    conditional_nutrients=ConditionalNutrients(
        creatine=0.5
    )
)

class TestNutritionGetRequests(unittest.TestCase):
    def setUp(self):
        self.mock_session = MOCK_SESSION.copy()
        self.today = date.today()

    def test_get_daily_overview_today(self):
        """Test getting daily overview for today"""
        with patch('fit.web.nutrition.requests.tracker_factory') as mock_factory, \
             patch('fit.web.nutrition.requests._get_daily_nutrition_data') as mock_get_data, \
             patch('fit.web.nutrition.requests.database_service') as mock_db:
            
            mock_tracker = MagicMock()
            mock_factory.return_value = mock_tracker
            mock_get_data.return_value = MOCK_DAILY_NUTRITION
            mock_db.get_daily_meals.return_value = [
                {"meal": MOCK_MEAL, "meal_time": datetime.now().time(), "rowid": 1}
            ]
            
            result = nutrition_requests.get_daily_overview(self.mock_session)
            
            mock_factory.assert_called_once_with("whoop", "mock_token")
            mock_get_data.assert_called_once_with(self.today, mock_tracker, 42)
            self.assertIn("Nutrition Center", str(result))
            self.assertIn("Macronutrients", str(result))
            self.assertIn("Micronutrients", str(result))

    def test_get_daily_overview_specific_date(self):
        """Test getting daily overview for a specific date"""
        specific_date = "2024-01-01"
        expected_date = date(2024, 1, 1)
        
        with patch('fit.web.nutrition.requests.tracker_factory') as mock_factory, \
             patch('fit.web.nutrition.requests._get_daily_nutrition_data') as mock_get_data, \
             patch('fit.web.nutrition.requests.database_service') as mock_db:
            
            mock_tracker = MagicMock()
            mock_factory.return_value = mock_tracker
            mock_get_data.return_value = MOCK_DAILY_NUTRITION
            mock_db.get_daily_meals.return_value = [
                {"meal": MOCK_MEAL, "meal_time": datetime.now().time(), "rowid": 1}
            ]
            
            result = nutrition_requests.get_daily_overview(self.mock_session, specific_date)
            
            mock_get_data.assert_called_once_with(expected_date, mock_tracker, 42)
            self.assertIn("January 01, 2024", str(result))

    def test_get_daily_overview_invalid_date(self):
        """Test getting daily overview with invalid date format"""
        invalid_date = "not-a-date"
        
        with patch('fit.web.nutrition.requests.tracker_factory') as mock_factory, \
             patch('fit.web.nutrition.requests._get_daily_nutrition_data') as mock_get_data:
            
            mock_tracker = MagicMock()
            mock_factory.return_value = mock_tracker
            mock_get_data.return_value = MOCK_DAILY_NUTRITION
            
            nutrition_requests.get_daily_overview(self.mock_session, invalid_date)
            
            mock_get_data.assert_called_once_with(self.today, mock_tracker, 42)

    def test_get_weekly_overview(self):
        """Test getting weekly overview"""
        week_dates = [self.today - timedelta(days=i) for i in range(7)]
        
        with patch('fit.web.nutrition.requests.tracker_factory') as mock_factory, \
             patch('fit.web.nutrition.requests._get_weekly_nutrition_data') as mock_get_data, \
             patch('fit.web.nutrition.requests.get_current_week_dates') as mock_get_week:
            
            mock_tracker = MagicMock()
            mock_factory.return_value = mock_tracker
            mock_get_data.return_value = MOCK_DAILY_NUTRITION
            mock_get_week.return_value = week_dates
            
            result = nutrition_requests.get_weekly_overview(self.mock_session)
            
            mock_factory.assert_called_once_with("whoop", "mock_token")
            mock_get_data.assert_called_once_with(week_dates, mock_tracker, 42)
            mock_get_week.assert_called_once()
            self.assertIn("Nutrition Center", str(result))
            self.assertIn("weekly", str(result).lower())

class TestNutritionPostRequests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.mock_session = MOCK_SESSION.copy()
        self.mock_request = MagicMock()
        self.mock_meal_time = "12:00"
        self.mock_meal_description = "Grilled chicken sandwich with lettuce and tomato"

    async def test_analyze_text_success(self):
        """Test successful meal text analysis"""
        mock_form_data = {
            "meal_description": self.mock_meal_description,
            "meal_time": self.mock_meal_time
        }
        
        async def mock_form():
            return mock_form_data
            
        self.mock_request.form = mock_form
        
        with patch('fit.web.nutrition.requests.assistants') as mock_assistants:
            mock_assistants.natural_language_nutritional_breakdown.return_value.content = [
                MagicMock(parsed=MOCK_MEAL)
            ]
            
            result = await nutrition_requests.analyze_text(self.mock_request)
            
            mock_assistants.natural_language_nutritional_breakdown.assert_called_once_with(
                self.mock_meal_description
            )
            self.assertIn("Test ingredients", str(result))
            self.assertIn("Nutrition Information", str(result))

    async def test_analyze_text_with_date(self):
        """Test meal text analysis with specific date"""
        specific_date = "2024-01-01"
        mock_form_data = {
            "meal_description": self.mock_meal_description,
            "meal_time": self.mock_meal_time
        }
        
        async def mock_form():
            return mock_form_data
            
        self.mock_request.form = mock_form
        
        with patch('fit.web.nutrition.requests.assistants') as mock_assistants:
            mock_assistants.natural_language_nutritional_breakdown.return_value.content = [
                MagicMock(parsed=MOCK_MEAL)
            ]
            
            await nutrition_requests.analyze_text(self.mock_request, specific_date)
            

    async def test_analyze_image_success(self):
        """Test successful food image analysis"""
        mock_image = MagicMock(spec=Image.Image)
        mock_image_file = MagicMock(spec=fh.UploadFile)
        mock_image_bytes = b"mock_image_bytes"
        
        async def mock_read():
            return mock_image_bytes
            
        mock_image_file.read = mock_read
        
        with patch('fit.web.nutrition.requests.Image') as mock_pil, \
             patch('fit.web.nutrition.requests.assistants') as mock_assistants, \
             patch('fit.web.nutrition.requests.io.BytesIO') as mock_bytesio:
            
            mock_pil.open.return_value = mock_image
            mock_assistants.vision_nutritional_breakdown.return_value.content = [
                MagicMock(parsed=MOCK_MEAL)
            ]
            
            result = await nutrition_requests.analyze_image(
                mock_image_file,
                "This is a chicken sandwich",
                self.mock_meal_time
            )
            
            mock_pil.open.assert_called_once_with(mock_bytesio())
            mock_assistants.vision_nutritional_breakdown.assert_called_once_with(
                mock_image,
                "This is a chicken sandwich"
            )
            self.assertIn("Test Meal", str(result))
            self.assertIn("Test ingredients", str(result))
            self.assertIn("Nutrition Information", str(result))

    async def test_analyze_image_with_date(self):
        """Test food image analysis with specific date"""
        specific_date = "2024-01-01"
        mock_image = MagicMock(spec=Image.Image)
        mock_image_file = MagicMock(spec=fh.UploadFile)
        mock_image_bytes = b"mock_image_bytes"
        
        async def mock_read():
            return mock_image_bytes
            
        mock_image_file.read = mock_read
        
        with patch('fit.web.nutrition.requests.Image') as mock_pil, \
             patch('fit.web.nutrition.requests.assistants') as mock_assistants:
            mock_pil.open.return_value = mock_image
            mock_assistants.vision_nutritional_breakdown.return_value.content = [
                MagicMock(parsed=MOCK_MEAL)
            ]
            
            await nutrition_requests.analyze_image(
                mock_image_file,
                "This is a chicken sandwich",
                self.mock_meal_time,
                specific_date
            )
            

    async def test_analyze_image_error_handling(self):
        """Test error handling in image analysis"""
        mock_image_file = MagicMock(spec=fh.UploadFile)
        
        async def mock_read():
            raise Exception("Failed to read image")
            
        mock_image_file.read = mock_read
        
        with self.assertRaises(Exception) as context:
            await nutrition_requests.analyze_image(
                mock_image_file,
                "This is a chicken sandwich",
                self.mock_meal_time
            )
        
        self.assertEqual(str(context.exception), "Failed to read image")

    async def test_save_meal_success(self):
        """Test successful meal saving"""
        mock_form_data = {
            "title": "Test Meal",
            "ingredients": "Test ingredients",
            "meal_time": "12:00",
            "calories": "500",
            "protein": "30",
            "carbohydrates": "50",
            "fat": "20",
            "fiber": "5",
            "vitamin_a": "1000",
            "vitamin_c": "30",
            "vitamin_d": "400",
            "calcium": "200",
            "iron": "3",
            "potassium": "300",
            "sodium": "400",
            "creatine": "0.5"
        }
        
        async def mock_form():
            return mock_form_data
            
        self.mock_request.form = mock_form
        
        with patch('fit.web.nutrition.requests.database_service') as mock_db:
            result = await nutrition_requests.save_meal(self.mock_session, self.mock_request)
            
            mock_db.insert_meal.assert_called_once()
            self.assertIsInstance(result, fh.Response)
            self.assertEqual(result.status_code, 200)
            self.assertEqual(result.headers["HX-Redirect"], "/nutrition")

    async def test_save_meal_with_date(self):
        """Test saving meal with specific date"""
        specific_date = "2024-01-01"
        mock_form_data = {
            "title": "Test Meal",
            "ingredients": "Test ingredients",
            "meal_time": "12:00",
            "calories": "500",
            "protein": "30",
            "carbohydrates": "50",
            "fat": "20",
            "fiber": "5",
            "vitamin_a": "1000",
            "vitamin_c": "30",
            "vitamin_d": "400",
            "calcium": "200",
            "iron": "3",
            "potassium": "300",
            "sodium": "400",
            "creatine": "0.5"
        }
        
        async def mock_form():
            return mock_form_data
            
        self.mock_request.form = mock_form
        
        with patch('fit.web.nutrition.requests.database_service') as mock_db:
            result = await nutrition_requests.save_meal(self.mock_session, self.mock_request, specific_date)
            
            mock_db.insert_meal.assert_called_once()
            self.assertIsInstance(result, fh.Response)
            self.assertEqual(result.status_code, 200)

    async def test_save_meal_error(self):
        """Test meal saving with database error"""
        mock_form_data = {
            "title": "Test Meal",
            "ingredients": "Test ingredients",
            "meal_time": "12:00",
            "calories": "invalid"  # This should cause an error
        }
        
        async def mock_form():
            return mock_form_data
            
        self.mock_request.form = mock_form
        
        result = await nutrition_requests.save_meal(self.mock_session, self.mock_request)
        
        self.assertIn("Error saving meal", str(result))
        self.assertIn("text-red-500", str(result))

    async def test_delete_meal_success(self):
        """Test successful meal deletion"""
        meal_id = 1
        
        with patch('fit.web.nutrition.requests.database_service') as mock_db:
            mock_db.delete_meal.return_value = True
            
            result = await nutrition_requests.delete_meal(meal_id)
            
            mock_db.delete_meal.assert_called_once_with(meal_id)
            self.assertIsNone(result)

    async def test_delete_meal_failure(self):
        """Test meal deletion when database returns False"""
        meal_id = 1
        
        with patch('fit.web.nutrition.requests.database_service') as mock_db:
            mock_db.delete_meal.return_value = False
            
            result = await nutrition_requests.delete_meal(meal_id)
            
            mock_db.delete_meal.assert_called_once_with(meal_id)
            self.assertIn("Error deleting meal", str(result))
            self.assertIn("text-red-500", str(result))

    async def test_delete_meal_error(self):
        """Test meal deletion with database error"""
        meal_id = 1
        
        with patch('fit.web.nutrition.requests.database_service') as mock_db:
            mock_db.delete_meal.side_effect = Exception("Database error")
            
            result = await nutrition_requests.delete_meal(meal_id)
            
            mock_db.delete_meal.assert_called_once_with(meal_id)
            self.assertIn("Error deleting meal", str(result))
            self.assertIn("Database error", str(result))

    async def test_save_supplement_success(self):
        """Test successful supplement saving"""
        mock_form_data = {
            "title": "Test Supplement",
            "time_consumed": "12:00",
            "calories": "100",
            "protein": "20",
            "carbohydrates": "5",
            "fat": "2",
            "fiber": "0",
            "vitamin_a": "5000",
            "vitamin_c": "500",
            "vitamin_d": "1000",
            "calcium": "500",
            "iron": "18",
            "potassium": "200",
            "sodium": "100"
        }
        
        async def mock_form():
            return mock_form_data
            
        self.mock_request.form = mock_form
        
        with patch('fit.web.nutrition.requests.database_service') as mock_db:
            result = await nutrition_requests.save_supplement(self.mock_session, self.mock_request)
            
            mock_db.insert_supplement.assert_called_once()
            self.assertIn("Supplement saved successfully", str(result))
            self.assertIn("closeSupplementModal", str(result))
            self.assertIn("window.location.href", str(result))

    async def test_save_supplement_error(self):
        """Test supplement saving with database error"""
        mock_form_data = {
            "title": "Test Supplement",
            "time_consumed": "12:00",
            "calories": "invalid"  # This should cause an error
        }
        
        async def mock_form():
            return mock_form_data
            
        self.mock_request.form = mock_form
        
        result = await nutrition_requests.save_supplement(self.mock_session, self.mock_request)
        
        self.assertIn("Error saving supplement", str(result))
        self.assertIn("text-red-500", str(result))

    async def test_get_supplements(self):
        """Test getting supplements for dropdown"""
        mock_supplements = ["Vitamin D", "Protein Powder", "Creatine"]
        
        with patch('fit.web.nutrition.requests.database_service') as mock_db:
            mock_db.get_supplement_names.return_value = mock_supplements
            
            result = await nutrition_requests.get_supplements(self.mock_session)
            
            mock_db.get_supplement_names.assert_called_once_with(42)
            for supplement in mock_supplements:
                self.assertIn(supplement, str(result))

    async def test_log_supplement_consumption_success(self):
        """Test successful supplement consumption logging"""
        mock_form_data = {
            "supplement_name": "Protein Powder",
            "time_consumed": "12:00"
        }
        
        mock_supplement_info = {
            "calories": 120,
            "protein": 24,
            "carbohydrates": 3,
            "fat": 2
        }
        
        async def mock_form():
            return mock_form_data
            
        self.mock_request.form = mock_form
        
        with patch('fit.web.nutrition.requests.database_service') as mock_db:
            mock_db.get_supplement.return_value = mock_supplement_info
            
            result = await nutrition_requests.log_supplement_consumption(self.mock_session, self.mock_request)
            
            mock_db.get_supplement.assert_called_once_with("Protein Powder")
            mock_db.insert_supplement.assert_called_once()
            self.assertIn("Supplement logged successfully", str(result))
            self.assertIn("closeSupplementModal", str(result))
            self.assertIn("window.location.href", str(result))

    async def test_log_supplement_consumption_with_date(self):
        """Test supplement consumption logging with specific date"""
        specific_date = "2024-01-01"
        mock_form_data = {
            "supplement_name": "Protein Powder",
            "time_consumed": "12:00"
        }
        
        mock_supplement_info = {
            "calories": 120,
            "protein": 24,
            "carbohydrates": 3,
            "fat": 2
        }
        
        async def mock_form():
            return mock_form_data
            
        self.mock_request.form = mock_form
        
        with patch('fit.web.nutrition.requests.database_service') as mock_db:
            mock_db.get_supplement.return_value = mock_supplement_info
            
            result = await nutrition_requests.log_supplement_consumption(self.mock_session, self.mock_request, specific_date)
            
            mock_db.get_supplement.assert_called_once_with("Protein Powder")
            mock_db.insert_supplement.assert_called_once()
            self.assertIn("Supplement logged successfully", str(result))

    async def test_log_supplement_consumption_error(self):
        """Test supplement consumption logging with error"""
        mock_form_data = {
            "supplement_name": "Nonexistent Supplement",
            "time_consumed": "12:00"
        }
        
        async def mock_form():
            return mock_form_data
            
        self.mock_request.form = mock_form
        
        with patch('fit.web.nutrition.requests.database_service') as mock_db:
            mock_db.get_supplement.side_effect = Exception("Supplement not found")
            
            result = await nutrition_requests.log_supplement_consumption(self.mock_session, self.mock_request)
            
            self.assertIn("Error logging supplement", str(result))
            self.assertIn("text-red-500", str(result))

    async def test_regenerate_analysis_success(self):
        """Test successful analysis regeneration with feedback"""
        mock_form_data = {
            "feedback": "Add more protein content",
            "original_description": "Chicken sandwich",
            "original_breakdown": MOCK_MEAL.model_dump_json(),
            "date": "2024-01-01"
        }
        
        async def mock_form():
            return mock_form_data
            
        self.mock_request.form = mock_form
        
        improved_meal = MOCK_MEAL.copy()
        
        with patch('fit.web.nutrition.requests.assistants') as mock_assistants:
            mock_assistants.improve_breakdown.return_value.content = [
                MagicMock(parsed=improved_meal)
            ]
            
            result = await nutrition_requests.regenerate_analysis(
                self.mock_request,
                "Add more protein content",
                "Chicken sandwich",
                MOCK_MEAL.model_dump_json()
            )
            
            mock_assistants.improve_breakdown.assert_called_once_with(
                MOCK_MEAL.model_dump_json(),
                "Add more protein content"
            )
            self.assertIn("40", str(result))  # Check for increased protein value

    async def test_regenerate_analysis_with_date(self):
        """Test analysis regeneration with specific date"""
        specific_date = "2024-01-01"
        mock_form_data = {
            "feedback": "Add more protein content",
            "original_description": "Chicken sandwich",
            "original_breakdown": MOCK_MEAL.model_dump_json(),
            "date": specific_date
        }
        
        async def mock_form():
            return mock_form_data
            
        self.mock_request.form = mock_form
        
        with patch('fit.web.nutrition.requests.assistants') as mock_assistants:
            mock_assistants.improve_breakdown.return_value.content = [
                MagicMock(parsed=MOCK_MEAL)
            ]
            
            await nutrition_requests.regenerate_analysis(
                self.mock_request,
                "Add more protein content",
                "Chicken sandwich",
                MOCK_MEAL.model_dump_json()
            )
            

    async def test_regenerate_analysis_error(self):
        """Test analysis regeneration with error"""
        mock_form_data = {
            "feedback": "Invalid feedback",
            "original_description": "Chicken sandwich",
            "original_breakdown": "invalid_json",  # This should cause an error
            "date": "2024-01-01"
        }
        
        async def mock_form():
            return mock_form_data
            
        self.mock_request.form = mock_form
        
        with patch('fit.web.nutrition.requests.assistants') as mock_assistants:
            mock_assistants.improve_breakdown.side_effect = Exception("Error improving breakdown")
            
            with self.assertRaises(Exception) as context:
                await nutrition_requests.regenerate_analysis(
                    self.mock_request,
                    "Invalid feedback",
                    "Chicken sandwich",
                    "invalid_json"
                )
            
            self.assertEqual(str(context.exception), "Error improving breakdown")

    async def test_regenerate_analysis_response_format(self):
        """Test response format of regenerated analysis"""
        mock_form_data = {
            "feedback": "Add more details",
            "original_description": "Chicken sandwich",
            "original_breakdown": MOCK_MEAL.model_dump_json(),
            "date": "2024-01-01"
        }
        
        async def mock_form():
            return mock_form_data
            
        self.mock_request.form = mock_form
        
        with patch('fit.web.nutrition.requests.assistants') as mock_assistants:
            mock_assistants.improve_breakdown.return_value.content = [
                MagicMock(parsed=MOCK_MEAL)
            ]
            
            _ = await nutrition_requests.regenerate_analysis(
                self.mock_request,
                "Add more details",
                "Chicken sandwich",
                MOCK_MEAL.model_dump_json()
            )
            

    async def test_generate_daily_overview_success(self):
        """Test successful daily overview generation"""
        with patch('fit.web.nutrition.requests.generate_overview') as mock_generate:
            mock_generate.return_value = MagicMock(
                summary="Good nutrition today",
                macronutrients="Good macro balance",
                micronutrients="Good micro intake",
                suggestions="Consider more protein"
            )
            
            result = await nutrition_requests.generate_daily_overview(self.mock_session)
            
            mock_generate.assert_called_once_with(self.mock_session, None, weekly=False)
            self.assertIn("Good nutrition today", str(result))
            self.assertIn("Good macro balance", str(result))

    async def test_generate_daily_overview_no_meals(self):
        """Test daily overview generation with no meals"""
        with patch('fit.web.nutrition.requests.generate_overview') as mock_generate:
            mock_generate.side_effect = nutrition_requests.assistants.NoMealsLoggedError("No meals logged today")
            
            result = await nutrition_requests.generate_daily_overview(self.mock_session)
            
            self.assertIn("No meals logged today", str(result))
            self.assertIn("text-base-content", str(result))

    async def test_generate_weekly_overview_success(self):
        """Test successful weekly overview generation"""
        with patch('fit.web.nutrition.requests.generate_overview') as mock_generate:
            mock_generate.return_value = MagicMock(
                summary="Good week overall",
                macronutrients="Consistent macro intake",
                micronutrients="Varied micro intake",
                suggestions="Keep up the good work"
            )
            
            result = await nutrition_requests.generate_weekly_overview(self.mock_session)
            
            mock_generate.assert_called_once_with(self.mock_session, None, weekly=True)
            self.assertIn("Good week overall", str(result))
            self.assertIn("Consistent macro intake", str(result))

    async def test_generate_weekly_overview_error(self):
        """Test weekly overview generation with error"""
        with patch('fit.web.nutrition.requests.generate_overview') as mock_generate:
            mock_generate.return_value = "Error analyzing weekly data"
            
            result = await nutrition_requests.generate_weekly_overview(self.mock_session)
            
            self.assertIn("Error analyzing weekly data", str(result))
            self.assertIn("text-base-content", str(result))

    def test_generate_overview_daily(self):
        """Test generate_overview function for daily view"""
        mock_date = "2024-01-01"
        expected_date = datetime(2024, 1, 1).date()
        mock_meals = [MOCK_MEAL]
        mock_nutritional_data = {
            "targets": [{
                "calories": 2500,
                "protein": 180,
                "carbohydrates": 250,
                "fat": 80
            }],
            "restrictions": ["vegetarian"]
        }
        
        with patch('fit.web.nutrition.requests.database_service') as mock_db, \
             patch('fit.web.nutrition.requests._get_user_nutritional_data_for_dates') as mock_get_data, \
             patch('fit.web.nutrition.requests.assistants') as mock_assistants:
            
            mock_db.get_daily_meals.return_value = mock_meals
            mock_get_data.return_value = mock_nutritional_data
            mock_assistants.daily_io_analysis.return_value.content = [
                MagicMock(parsed=MagicMock(
                    summary="Daily summary",
                    macronutrients="Daily macros",
                    micronutrients="Daily micros",
                    suggestions="Daily suggestions"
                ))
            ]
            
            result = nutrition_requests.generate_overview(self.mock_session, mock_date, weekly=False)
            
            mock_db.get_daily_meals.assert_called_once_with(expected_date, 42)
            mock_get_data.assert_called_once_with(self.mock_session, [expected_date])
            mock_assistants.daily_io_analysis.assert_called_once_with(
                mock_meals,
                mock_nutritional_data["targets"][0],
                mock_nutritional_data["restrictions"]
            )
            self.assertEqual(result.summary, "Daily summary")
            self.assertEqual(result.macronutrients, "Daily macros")

    def test_generate_overview_weekly(self):
        """Test generate_overview function for weekly view"""
        week_dates = [datetime.today().date() - timedelta(days=i) for i in range(7)]
        mock_meals = {str(date): [MOCK_MEAL] for date in week_dates}
        mock_nutritional_data = {
            "targets": [{
                "calories": 2500,
                "protein": 180,
                "carbohydrates": 250,
                "fat": 80
            } for _ in range(7)],
            "restrictions": ["vegetarian"]
        }
        
        with patch('fit.web.nutrition.requests.get_current_week_dates') as mock_get_week, \
             patch('fit.web.nutrition.requests.get_weekly_meals') as mock_get_meals, \
             patch('fit.web.nutrition.requests._get_user_nutritional_data_for_dates') as mock_get_data, \
             patch('fit.web.nutrition.requests.assistants') as mock_assistants:
            
            mock_get_week.return_value = week_dates
            mock_get_meals.return_value = mock_meals
            mock_get_data.return_value = mock_nutritional_data
            mock_assistants.weekly_io_analysis.return_value.content = [
                MagicMock(parsed=MagicMock(
                    summary="Weekly summary",
                    macronutrients="Weekly macros",
                    micronutrients="Weekly micros",
                    suggestions="Weekly suggestions"
                ))
            ]
            
            result = nutrition_requests.generate_overview(self.mock_session, None, weekly=True)
            
            mock_get_week.assert_called_once()
            mock_get_meals.assert_called_once_with(week_dates, 42)
            mock_get_data.assert_called_once_with(self.mock_session, week_dates)
            mock_assistants.weekly_io_analysis.assert_called_once_with(
                mock_meals,
                mock_nutritional_data["targets"],
                mock_nutritional_data["restrictions"]
            )
            self.assertEqual(result.summary, "Weekly summary")
            self.assertEqual(result.macronutrients, "Weekly macros")

    def test_generate_overview_invalid_date(self):
        """Test generate_overview function with invalid date"""
        invalid_date = "not-a-date"
        today = datetime.today().date()
        mock_meals = [MOCK_MEAL]
        mock_nutritional_data = {
            "targets": [{
                "calories": 2500,
                "protein": 180,
                "carbohydrates": 250,
                "fat": 80
            }],
            "restrictions": ["vegetarian"]
        }
        
        with patch('fit.web.nutrition.requests.database_service') as mock_db, \
             patch('fit.web.nutrition.requests._get_user_nutritional_data_for_dates') as mock_get_data, \
             patch('fit.web.nutrition.requests.assistants') as mock_assistants:
            
            mock_db.get_daily_meals.return_value = mock_meals
            mock_get_data.return_value = mock_nutritional_data
            mock_assistants.daily_io_analysis.return_value.content = [MagicMock(parsed=MagicMock())]
            
            nutrition_requests.generate_overview(self.mock_session, invalid_date, weekly=False)
            
            mock_db.get_daily_meals.assert_called_once_with(today, 42)
            mock_get_data.assert_called_once_with(self.mock_session, [today])

    async def test_get_nutrient_suggestions_success(self):
        """Test successful nutrient suggestions generation"""
        nutrient = "protein"
        mock_daily_nutrition = MagicMock()
        mock_nutritional_data = {
            "targets": [{
                "calories": 2500,
                "protein": 180,
                "carbohydrates": 250,
                "fat": 80
            }],
            "restrictions": ["vegetarian"]
        }
        mock_preferences = "Prefers high-protein vegetarian meals"
        mock_inventory = ["chickpeas", "tofu", "quinoa"]
        mock_recommendations = Recommendations(meals=[
            MealRecommendation(
                title="Grilled tofu with quinoa",
                ingredients="tofu 200g, quinoa 100g, vegetables 150g",
                is_explorative=False
            ),
            MealRecommendation(
                title="Chickpea curry",
                ingredients="chickpeas 200g, coconut milk 200ml, spices",
                is_explorative=True
            ),
            MealRecommendation(
                title="Protein smoothie",
                ingredients="protein powder 30g, banana 1, milk 250ml",
                is_explorative=False
            )
        ])
        
        with patch('fit.web.nutrition.requests.database_service') as mock_db, \
             patch('fit.web.nutrition.requests._get_user_nutritional_data_for_dates') as mock_get_data, \
             patch('fit.web.nutrition.requests.assistants') as mock_assistants:
            
            mock_db.get_daily_cumulative_nutrition.return_value = mock_daily_nutrition
            mock_get_data.return_value = mock_nutritional_data
            mock_db.get_all_meal_summaries.return_value = ["Past meal 1", "Past meal 2"]
            mock_db.get_inventory.return_value = mock_inventory
            mock_assistants.summarize_user_preferences.return_value = mock_preferences
            mock_assistants.make_recommendations.return_value.content = [
                MagicMock(parsed=mock_recommendations)
            ]
            
            result = await nutrition_requests.get_nutrient_suggestions(self.mock_session, nutrient)
            
            mock_db.get_daily_cumulative_nutrition.assert_called_once_with(
                datetime.today().date(),
                42
            )
            mock_get_data.assert_called_once_with(
                self.mock_session,
                [datetime.today().date()]
            )
            mock_db.get_all_meal_summaries.assert_called_once_with(42)
            mock_db.get_inventory.assert_called_once_with(42)
            mock_assistants.summarize_user_preferences.assert_called_once_with(
                ["Past meal 1", "Past meal 2"]
            )
            mock_assistants.make_recommendations.assert_called_once_with(
                consumption=mock_daily_nutrition,
                targets=mock_nutritional_data["targets"][0],
                target_nutrient=nutrient,
                restrictions=mock_nutritional_data["restrictions"],
                user_preferences=mock_preferences,
                kitchen_inventory=mock_inventory
            )
            
            for meal in mock_recommendations.meals:
                self.assertIn(meal.title, str(result))
                self.assertIn(meal.ingredients, str(result))

    async def test_get_nutrient_suggestions_no_inventory(self):
        """Test nutrient suggestions generation with empty inventory"""
        nutrient = "protein"
        mock_daily_nutrition = MagicMock()
        mock_nutritional_data = {
            "targets": [{
                "calories": 2500,
                "protein": 180,
                "carbohydrates": 250,
                "fat": 80
            }],
            "restrictions": ["vegetarian"]
        }
        mock_preferences = "Prefers high-protein vegetarian meals"
        mock_inventory = []  # Empty inventory
        mock_recommendations = Recommendations(meals=[
            MealRecommendation(
                title="Protein smoothie",
                ingredients="protein powder 30g, banana 1, milk 250ml",
                is_explorative=False
            ),
            MealRecommendation(
                title="Tofu stir-fry",
                ingredients="tofu 200g, mixed vegetables 300g, soy sauce",
                is_explorative=False
            ),
            MealRecommendation(
                title="Lentil soup",
                ingredients="red lentils 200g, vegetables 200g, spices",
                is_explorative=True
            )
        ])
        
        with patch('fit.web.nutrition.requests.database_service') as mock_db, \
             patch('fit.web.nutrition.requests._get_user_nutritional_data_for_dates') as mock_get_data, \
             patch('fit.web.nutrition.requests.assistants') as mock_assistants:
            
            mock_db.get_daily_cumulative_nutrition.return_value = mock_daily_nutrition
            mock_get_data.return_value = mock_nutritional_data
            mock_db.get_all_meal_summaries.return_value = ["Past meal 1", "Past meal 2"]
            mock_db.get_inventory.return_value = mock_inventory
            mock_assistants.summarize_user_preferences.return_value = mock_preferences
            mock_assistants.make_recommendations.return_value.content = [
                MagicMock(parsed=mock_recommendations)
            ]
            
            result = await nutrition_requests.get_nutrient_suggestions(self.mock_session, nutrient)
            
            mock_assistants.make_recommendations.assert_called_once_with(
                consumption=mock_daily_nutrition,
                targets=mock_nutritional_data["targets"][0],
                target_nutrient=nutrient,
                restrictions=mock_nutritional_data["restrictions"],
                user_preferences=mock_preferences,
                kitchen_inventory=mock_inventory
            )
            
            for meal in mock_recommendations.meals:
                self.assertIn(meal.title, str(result))
                self.assertIn(meal.ingredients, str(result))

    async def test_get_nutrient_suggestions_no_preferences(self):
        """Test nutrient suggestions generation with no meal history"""
        nutrient = "protein"
        mock_daily_nutrition = MagicMock()
        mock_nutritional_data = {
            "targets": [{
                "calories": 2500,
                "protein": 180,
                "carbohydrates": 250,
                "fat": 80
            }],
            "restrictions": ["vegetarian"]
        }
        mock_inventory = ["chickpeas", "tofu", "quinoa"]
        mock_recommendations = Recommendations(meals=[
            MealRecommendation(
                title="Grilled tofu with quinoa",
                ingredients="tofu 200g, quinoa 100g, vegetables 150g",
                is_explorative=True
            ),
            MealRecommendation(
                title="Chickpea curry",
                ingredients="chickpeas 200g, coconut milk 200ml, spices",
                is_explorative=True
            ),
            MealRecommendation(
                title="Protein smoothie",
                ingredients="protein powder 30g, banana 1, milk 250ml",
                is_explorative=True
            )
        ])
        
        with patch('fit.web.nutrition.requests.database_service') as mock_db, \
             patch('fit.web.nutrition.requests._get_user_nutritional_data_for_dates') as mock_get_data, \
             patch('fit.web.nutrition.requests.assistants') as mock_assistants:
            
            mock_db.get_daily_cumulative_nutrition.return_value = mock_daily_nutrition
            mock_get_data.return_value = mock_nutritional_data
            mock_db.get_all_meal_summaries.return_value = []  # No meal history
            mock_db.get_inventory.return_value = mock_inventory
            mock_assistants.summarize_user_preferences.return_value = ""  # No preferences
            mock_assistants.make_recommendations.return_value.content = [
                MagicMock(parsed=mock_recommendations)
            ]
            
            result = await nutrition_requests.get_nutrient_suggestions(self.mock_session, nutrient)
            
            mock_assistants.make_recommendations.assert_called_once_with(
                consumption=mock_daily_nutrition,
                targets=mock_nutritional_data["targets"][0],
                target_nutrient=nutrient,
                restrictions=mock_nutritional_data["restrictions"],
                user_preferences="",
                kitchen_inventory=mock_inventory
            )
            
            for meal in mock_recommendations.meals:
                self.assertIn(meal.title, str(result))
                self.assertIn(meal.ingredients, str(result))

    async def test_get_nutrient_suggestions_different_nutrients(self):
        """Test nutrient suggestions for different nutrients"""
        nutrients = ["protein", "iron", "vitamin_c"]
        mock_daily_nutrition = MagicMock()
        mock_nutritional_data = {
            "targets": [{
                "calories": 2500,
                "protein": 180,
                "carbohydrates": 250,
                "fat": 80
            }],
            "restrictions": ["vegetarian"]
        }
        mock_preferences = "Prefers balanced meals"
        mock_inventory = ["vegetables", "fruits", "grains"]
        
        with patch('fit.web.nutrition.requests.database_service') as mock_db, \
             patch('fit.web.nutrition.requests._get_user_nutritional_data_for_dates') as mock_get_data, \
             patch('fit.web.nutrition.requests.assistants') as mock_assistants:
            
            mock_db.get_daily_cumulative_nutrition.return_value = mock_daily_nutrition
            mock_get_data.return_value = mock_nutritional_data
            mock_db.get_all_meal_summaries.return_value = ["Past meal 1", "Past meal 2"]
            mock_db.get_inventory.return_value = mock_inventory
            mock_assistants.summarize_user_preferences.return_value = mock_preferences
            
            for nutrient in nutrients:
                mock_recommendations = Recommendations(meals=[
                    MealRecommendation(
                        title=f"{nutrient.capitalize()} rich meal {i}",
                        ingredients="ingredient 1 100g, ingredient 2 150g",
                        is_explorative=bool(i % 2)
                    ) for i in range(1, 4)
                ])
                mock_assistants.make_recommendations.return_value.content = [
                    MagicMock(parsed=mock_recommendations)
                ]
                
                result = await nutrition_requests.get_nutrient_suggestions(self.mock_session, nutrient)
                
                mock_assistants.make_recommendations.assert_called_with(
                    consumption=mock_daily_nutrition,
                    targets=mock_nutritional_data["targets"][0],
                    target_nutrient=nutrient,
                    restrictions=mock_nutritional_data["restrictions"],
                    user_preferences=mock_preferences,
                    kitchen_inventory=mock_inventory
                )
                
                for meal in mock_recommendations.meals:
                    self.assertIn(meal.title, str(result))
                    self.assertIn(meal.ingredients, str(result))

    async def test_log_water_success(self):
        """Test successful water logging"""
        mock_form_data = {
            "amount": "500",
            "time_consumed": "12:00"
        }
        
        async def mock_form():
            return mock_form_data
            
        self.mock_request.form = mock_form
        
        with patch('fit.web.nutrition.requests.database_service') as mock_db:
            result = await nutrition_requests.log_water(self.mock_session, self.mock_request)
            
            mock_db.insert_water_consumption.assert_called_once_with(
                water_consumed_ml=mock_form_data["amount"],
                date_consumed=datetime.today().date(),
                time_consumed=datetime.strptime(mock_form_data["time_consumed"], "%H:%M").time(),
                user_id=42
            )
            
            self.assertIn("Water logged successfully", str(result))
            self.assertIn("text-green-500", str(result))
            self.assertIn("closeWaterModal", str(result))
            self.assertIn("window.location.reload", str(result))

    async def test_log_water_with_date(self):
        """Test water logging with specific date"""
        specific_date = date(2024, 1, 1)
        mock_form_data = {
            "amount": "500",
            "time_consumed": "12:00"
        }
        
        async def mock_form():
            return mock_form_data
            
        self.mock_request.form = mock_form
        
        with patch('fit.web.nutrition.requests.database_service') as mock_db:
            result = await nutrition_requests.log_water(self.mock_session, self.mock_request, str(specific_date))
            
            mock_db.insert_water_consumption.assert_called_once_with(
                water_consumed_ml=mock_form_data["amount"],
                date_consumed=str(specific_date),
                time_consumed=datetime.strptime(mock_form_data["time_consumed"], "%H:%M").time(),
                user_id=42
            )
            
            self.assertIn("Water logged successfully", str(result))

    async def test_log_water_error(self):
        """Test water logging with database error"""
        mock_form_data = {
            "amount": "500",
            "time_consumed": "12:00"
        }
        
        async def mock_form():
            return mock_form_data
            
        self.mock_request.form = mock_form
        
        with patch('fit.web.nutrition.requests.database_service') as mock_db:
            mock_db.insert_water_consumption.side_effect = Exception("Database error")
            
            result = await nutrition_requests.log_water(self.mock_session, self.mock_request)
            
            self.assertIn("Error logging water", str(result))
            self.assertIn("Database error", str(result))
            self.assertIn("text-red-500", str(result))

    async def test_log_water_invalid_time_format(self):
        """Test water logging with invalid time format"""
        mock_form_data = {
            "amount": "500",
            "time_consumed": "invalid_time"
        }
        
        async def mock_form():
            return mock_form_data
            
        self.mock_request.form = mock_form
        
        result = await nutrition_requests.log_water(self.mock_session, self.mock_request)
        
        self.assertIn("Error logging water", str(result))
        self.assertIn("text-red-500", str(result))

    async def test_nutrition_redirect_daily(self):
        """Test nutrition redirect to daily view"""
        mock_form_data = {
            "time_filter": "daily"
        }
        
        async def mock_form():
            return mock_form_data
            
        self.mock_request.form = mock_form
        
        result = await nutrition_requests.nutrition_redirect(self.mock_request)

        self.assertIsInstance(result, fh.Response)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.headers["HX-Redirect"], "/nutrition")

    async def test_nutrition_redirect_weekly(self):
        """Test nutrition redirect to weekly view"""
        mock_form_data = {
            "time_filter": "weekly"
        }
        
        async def mock_form():
            return mock_form_data
            
        self.mock_request.form = mock_form
        
        result = await nutrition_requests.nutrition_redirect(self.mock_request)
        print(f"Result weekly: {result}")
        self.assertIsInstance(result, fh.Response)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.headers["HX-Redirect"], "/nutrition/weekly")

    async def test_nutrition_redirect_invalid_filter(self):
        """Test nutrition redirect with invalid time filter"""
        mock_form_data = {
            "time_filter": "invalid_filter"
        }
        
        async def mock_form():
            return mock_form_data
            
        self.mock_request.form = mock_form
        
        result = await nutrition_requests.nutrition_redirect(self.mock_request)
        
        # Should default to daily view
        self.assertIsInstance(result, fh.Response)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.headers["HX-Redirect"], "/nutrition")


if __name__ == '__main__':
    unittest.main() 