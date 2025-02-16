import unittest
from datetime import date
from unittest.mock import MagicMock, patch

from fit.web.performance import requests as performance_requests

MOCK_SESSION = {
    "user_id": 42,
    "tracker": "whoop",
    "access_token": "mock_token"
}

MOCK_WHOOP_STATS = {
    "score": {
        "kilojoule": 8374.2,
        "calories": 2000,
        "average_heart_rate": 65,
        "max_heart_rate": 180
    }
}

class TestPerformanceGetRequests(unittest.TestCase):
    def setUp(self):
        self.mock_session = MOCK_SESSION.copy()

    def test_get_performance_page_whoop(self):
        """Test performance page with Whoop tracker"""
        mock_cycle = {
            "score": {
                "kilojoule": 8374.2,
                "average_heart_rate": 65,
                "max_heart_rate": 180
            }
        }
        mock_workouts = [
            {"sport": "Running", "duration": 3600}
        ]
        
        with patch('fit.web.performance.requests.tracker_factory') as mock_factory:
            mock_tracker = MagicMock()
            mock_tracker.get_cycle_for_day.return_value = mock_cycle
            mock_tracker.tracker_type = "whoop"
            mock_tracker.get_daily_workouts.return_value = mock_workouts
            mock_factory.return_value = mock_tracker
            
            result = performance_requests.get(self.mock_session)
            
            mock_factory.assert_called_once_with("whoop", "mock_token")
            mock_tracker.get_cycle_for_day.assert_called_once_with(date.today())
            mock_tracker.get_daily_workouts.assert_called_once_with(date.today())
            self.assertIn("activity", str(result))
            self.assertIn("workout", str(result))
            self.assertIn("stats", str(result))

    def test_get_performance_page_fitbit(self):
        """Test performance page with Fitbit tracker"""
        self.mock_session["tracker"] = "fitbit"
        mock_calories = 2500
        mock_workouts = [
            {"sport": "Running", "duration": 3600}
        ]
        mock_heart_rate = {
            "average_heart_rate": 65,
            "max_heart_rate": 180
        }
        
        with patch('fit.web.performance.requests.tracker_factory') as mock_factory:
            mock_tracker = MagicMock()
            mock_tracker.get_intraday_heart_rate.return_value = mock_heart_rate
            mock_tracker.get_daily_calories_burned.return_value = mock_calories
            mock_tracker.get_daily_workouts.return_value = mock_workouts
            mock_factory.return_value = mock_tracker
            
            result = performance_requests.get(self.mock_session)
            
            mock_factory.assert_called_once_with("fitbit", "mock_token")
            mock_tracker.get_intraday_heart_rate.assert_called_once_with(date.today())
            mock_tracker.get_daily_calories_burned.assert_called_once_with(date.today())
            mock_tracker.get_daily_workouts.assert_called_once_with(date.today())
            self.assertIn("activity", str(result))
            self.assertIn("workout", str(result))
            self.assertIn("stats", str(result))


class TestPerformancePostRequests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.mock_session = MOCK_SESSION.copy()

    async def test_generate_overview_success(self):
        """Test successful performance overview generation"""
        mock_cycle = {
            "score": {
                "kilojoule": 8374.2,
                "average_heart_rate": 65,
                "max_heart_rate": 180
            }
        }
        mock_workouts = [
            {"sport": "Running", "duration": 3600}
        ]
        mock_nutrition = MagicMock()
        mock_nutrition.calories = 2000
        
        with patch('fit.web.performance.requests.tracker_factory') as mock_factory, \
             patch('fit.web.performance.requests.database_service') as mock_db, \
             patch('fit.web.performance.requests.assistants') as mock_assistants:
            
            mock_tracker = MagicMock()
            mock_tracker.get_cycle_for_day.return_value = mock_cycle
            mock_tracker.tracker_type = "whoop"
            mock_tracker.get_daily_workouts.return_value = mock_workouts
            mock_factory.return_value = mock_tracker
            
            mock_db.get_daily_cumulative_nutrition.return_value = mock_nutrition
            mock_assistants.summarize_workout_trends.return_value = "Regular running pattern"
            mock_assistants.early_daily_performance_overview.return_value = "Great progress today!"
            
            result = await performance_requests.generate_overview(self.mock_session)
            
            mock_factory.assert_called_once_with("whoop", "mock_token")
            mock_db.get_daily_cumulative_nutrition.assert_called_once_with(date.today(), 42)
            mock_assistants.summarize_workout_trends.assert_called_once_with(mock_workouts)
            mock_assistants.early_daily_performance_overview.assert_called_once()
            self.assertIn("Great progress today!", str(result))

    async def test_generate_overview_error(self):
        """Test performance overview generation with error"""
        with patch('fit.web.performance.requests.tracker_factory') as mock_factory:
            mock_factory.side_effect = Exception("Failed to get tracker")
            
            result = await performance_requests.generate_overview(self.mock_session)
            self.assertIn("Error generating performance analysis", str(result))


if __name__ == '__main__':
    unittest.main()
