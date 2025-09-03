import unittest
from datetime import date, datetime, time, timedelta
from unittest.mock import MagicMock, patch

from fit.backend.trackers.implementations.whoop import Whoop
from fit.web.rest import requests as rest_requests

MOCK_SESSION = {
    "user_id": 42,
    "tracker": "whoop",
    "access_token": "mock_token"
}

MOCK_WHOOP_RECOVERY = {
    "score": {
        "recovery_score": 85,
        "resting_heart_rate": 55,
        "hrv_rmssd_milli": 45
    }
}

MOCK_SLEEP_DATA = [{
    "duration": 480,
    "quality": 85,
    "stages": {
        "deep": 120,
        "light": 240,
        "rem": 120
    },
    "nap": False
}
]

class TestRestGetRequests(unittest.TestCase):
    def setUp(self):
        self.mock_session = MOCK_SESSION.copy()

    def test_get_rest_page_whoop(self):
        """Test rest page with Whoop tracker"""
        with patch('fit.web.rest.requests.tracker_factory') as mock_factory:
            mock_tracker = MagicMock()
            mock_tracker.get_daily_recovery.return_value = MOCK_WHOOP_RECOVERY
            mock_tracker.get_daily_sleep.return_value = MOCK_SLEEP_DATA
            mock_tracker.tracker_type = "whoop"
            mock_factory.return_value = mock_tracker
            
            result = rest_requests.get(self.mock_session)
            
            mock_factory.assert_called_once_with("whoop", "mock_token")
            mock_tracker.get_daily_recovery.assert_called_once_with(date.today())
            mock_tracker.get_daily_sleep.assert_called_once_with(date.today())
            self.assertIn("sleep", str(result))
            self.assertIn("strain", str(result))
            self.assertIn("readiness", str(result))
    
    def test_get_rest_page_fitbit(self):
        """Test rest page with Fitbit tracker"""
        self.mock_session["tracker"] = "fitbit"
        mock_resting_hr = 58
        mock_hrv = 42
        
        with patch('fit.web.rest.requests.tracker_factory') as mock_factory:
            mock_tracker = MagicMock()
            mock_tracker.get_daily_resting_heart_rate.return_value = mock_resting_hr
            mock_tracker.get_daily_hrv.return_value = mock_hrv
            mock_tracker.get_daily_sleep.return_value = MOCK_SLEEP_DATA
            mock_tracker.tracker_type = "fitbit"
            mock_factory.return_value = mock_tracker
            
            result = rest_requests.get(self.mock_session)
            
            mock_factory.assert_called_once_with("fitbit", "mock_token")
            mock_tracker.get_daily_resting_heart_rate.assert_called_once_with(date.today())
            mock_tracker.get_daily_hrv.assert_called_once_with(date.today())
            mock_tracker.get_daily_sleep.assert_called_once_with(date.today())
            self.assertIn("sleep", str(result))
            self.assertIn("strain", str(result))
            self.assertIn("readiness", str(result))


class TestRestPostRequests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.mock_session = MOCK_SESSION.copy()

    async def test_generate_overview_success(self):
        """Test successful rest overview generation"""
        yesterday = date.today() - timedelta(days=1)
        mock_activities = [MagicMock(start_time=datetime.combine(yesterday, time(9, 0)), type="Running", intensity="high")]
        
        expected_analysis_data = {
            "sleep_data": MOCK_SLEEP_DATA,
            "formatted_meals": [
                (datetime.combine(yesterday, time(8, 0)), "Breakfast"),
                (datetime.combine(yesterday, time(12, 0)), "Lunch")
            ],
            "formatted_activities": [(mock_activities[0].start_time, "Running", "high")],
            "recovery_metrics": {
                "recovery_score": 85,
                "resting_heart_rate": 55,
                "hrv": 45
            }
        }
        
        with patch('fit.web.rest.requests.tracker_factory') as mock_factory, \
             patch('fit.web.rest.requests.assistants') as mock_assistants, \
             patch('fit.web.rest.requests._get_rest_analysis_data') as mock_get_data:
            
            mock_tracker = MagicMock()
            mock_tracker.tracker_type = "whoop"
            mock_factory.return_value = mock_tracker
            
            mock_get_data.return_value = expected_analysis_data
            mock_assistants.analyze_rest_patterns.return_value = "Good sleep quality and recovery"
            
            result = await rest_requests.generate_overview(self.mock_session)
            
            mock_factory.assert_called_once_with("whoop", "mock_token")
            mock_get_data.assert_called_once_with(mock_tracker, yesterday, 42)
            mock_assistants.analyze_rest_patterns.assert_called_once_with(
                sleep_data=MOCK_SLEEP_DATA,
                meals=expected_analysis_data["formatted_meals"],
                activities=expected_analysis_data["formatted_activities"],
                sleep_targets=480.0,
                recovery_metrics=expected_analysis_data["recovery_metrics"]
            )
            self.assertIn("Good sleep quality and recovery", str(result))

    async def test_generate_overview_error(self):
        """Test rest overview generation with error"""
        with patch('fit.web.rest.requests.tracker_factory') as mock_factory:
            mock_factory.side_effect = Exception("Failed to get tracker")
            
            result = await rest_requests.generate_overview(self.mock_session)
            self.assertIn("Error generating rest analysis", str(result))


class TestRestAnalysisData(unittest.TestCase):
    def setUp(self):
        self.test_date = date(2024, 1, 1)
        self.user_id = 42
        self.mock_meals = [
            {"meal_time": time(8, 0), "meal": "Breakfast"},
            {"meal_time": time(12, 0), "meal": "Lunch"}
        ]
        self.mock_activities = [
            MagicMock(
                start_time=datetime.combine(self.test_date, time(9, 0)),
                type="Running",
                intensity="high"
            )
        ]

    def test_get_rest_analysis_data_whoop_with_recovery(self):
        """Test getting rest analysis data with Whoop tracker and valid recovery data"""
        mock_tracker = MagicMock(spec=Whoop)
        mock_tracker.tracker_type = "whoop"
        mock_tracker.get_daily_sleep.return_value = MOCK_SLEEP_DATA
        mock_tracker.get_daily_workouts.return_value = self.mock_activities
        mock_tracker.get_daily_recovery.return_value = MOCK_WHOOP_RECOVERY
        
        with patch('fit.web.rest.requests.database_service') as mock_db:
            mock_db.get_daily_meals.return_value = self.mock_meals
            
            result = rest_requests._get_rest_analysis_data(mock_tracker, self.test_date, self.user_id)
            
            mock_tracker.get_daily_sleep.assert_called_once_with(self.test_date)
            mock_tracker.get_daily_workouts.assert_called_once_with(self.test_date)
            mock_tracker.get_daily_recovery.assert_called_once_with(self.test_date)
            mock_db.get_daily_meals.assert_called_once_with(self.test_date, self.user_id)
            
            self.assertEqual(result["sleep_data"], MOCK_SLEEP_DATA)
            self.assertEqual(
                result["formatted_meals"],
                [(datetime.combine(self.test_date, time(8, 0)), "Breakfast"),
                 (datetime.combine(self.test_date, time(12, 0)), "Lunch")]
            )
            self.assertEqual(
                result["formatted_activities"],
                [(self.mock_activities[0].start_time, "Running", "high")]
            )
            self.assertEqual(
                result["recovery_metrics"],
                {
                    "recovery_score": 85,
                    "resting_heart_rate": 55,
                    "hrv": 45
                }
            )

    def test_get_rest_analysis_data_whoop_no_recovery(self):
        """Test getting rest analysis data with Whoop tracker but no recovery data"""
        mock_tracker = MagicMock(spec=Whoop)
        mock_tracker.tracker_type = "whoop"
        mock_tracker.get_daily_sleep.return_value = MOCK_SLEEP_DATA
        mock_tracker.get_daily_workouts.return_value = self.mock_activities
        mock_tracker.get_daily_recovery.return_value = None
        
        with patch('fit.web.rest.requests.database_service') as mock_db:
            mock_db.get_daily_meals.return_value = self.mock_meals
            
            result = rest_requests._get_rest_analysis_data(mock_tracker, self.test_date, self.user_id)
            
            self.assertEqual(
                result["recovery_metrics"],
                {
                    "recovery_score": None,
                    "resting_heart_rate": None,
                    "hrv": None
                }
            )

    def test_get_rest_analysis_data_fitbit(self):
        """Test getting rest analysis data with Fitbit tracker"""
        mock_tracker = MagicMock()
        mock_tracker.tracker_type = "fitbit"
        mock_tracker.get_daily_sleep.return_value = MOCK_SLEEP_DATA
        mock_tracker.get_daily_workouts.return_value = self.mock_activities
        mock_tracker.get_daily_resting_heart_rate.return_value = 58
        mock_tracker.get_daily_hrv.return_value = 42
        
        with patch('fit.web.rest.requests.database_service') as mock_db:
            mock_db.get_daily_meals.return_value = self.mock_meals
            
            result = rest_requests._get_rest_analysis_data(mock_tracker, self.test_date, self.user_id)
            
            mock_tracker.get_daily_sleep.assert_called_once_with(self.test_date)
            mock_tracker.get_daily_workouts.assert_called_once_with(self.test_date)
            mock_tracker.get_daily_resting_heart_rate.assert_called_once_with(self.test_date)
            mock_tracker.get_daily_hrv.assert_called_once_with(self.test_date)
            mock_db.get_daily_meals.assert_called_once_with(self.test_date, self.user_id)
            
            self.assertEqual(
                result["recovery_metrics"],
                {
                    "resting_heart_rate": 58,
                    "hrv": 42,
                    "recovery_score": None
                }
            )


if __name__ == '__main__':
    unittest.main() 
