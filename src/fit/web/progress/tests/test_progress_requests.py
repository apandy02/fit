import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from fit.web.progress import requests as progress_requests

MOCK_SESSION = {
    "user_id": 42,
    "tracker": "whoop",
    "access_token": "mock_token"
}

MOCK_MEASUREMENTS = [
    {
        "datetime": str(datetime(2024, 1, 1)),
        "weight": 170.5,
        "height": 71,
    },
    {
        "datetime": str(datetime(2024, 1, 15)),
        "weight": 168.0,
        "height": 71,
    }
]

class TestProgressGetRequests(unittest.TestCase):
    def setUp(self):
        self.mock_session = MOCK_SESSION.copy()

    def test_get_progress_page(self):
        """Test getting the progress page with measurements"""
        with patch('fit.web.progress.requests.database_service') as mock_db:
            mock_db.get_user_measurements.return_value = MOCK_MEASUREMENTS
            
            result = progress_requests.get(self.mock_session)
            
            mock_db.get_user_measurements.assert_called_once_with(42)
            self.assertIn("progress", str(result).lower())

    def test_get_latest_measurements_with_data(self):
        """Test getting latest measurements when data exists"""
        mock_latest = {
            "weight": 168.0,
            "height": 71
        }
        
        with patch('fit.web.progress.requests.database_service') as mock_db:
            mock_db.get_latest_user_measurements.return_value = mock_latest
            
            weight, feet, inches = progress_requests.get_latest_measurements(42)
            
            mock_db.get_latest_user_measurements.assert_called_once_with(42)
            self.assertEqual(weight, 168.0)
            self.assertEqual(feet, 5)
            self.assertEqual(inches, 11)

    def test_get_latest_measurements_no_data(self):
        """Test getting latest measurements when no data exists"""
        with patch('fit.web.progress.requests.database_service') as mock_db:
            mock_db.get_latest_user_measurements.return_value = None
            
            weight, feet, inches = progress_requests.get_latest_measurements(42)
            
            mock_db.get_latest_user_measurements.assert_called_once_with(42)
            self.assertEqual(weight, 0)
            self.assertEqual(feet, 0)
            self.assertEqual(inches, 0)

    def test_get_latest_measurements_null_values(self):
        """Test getting latest measurements with null values in database"""
        mock_latest = {
            "weight": None,
            "height": None
        }
        
        with patch('fit.web.progress.requests.database_service') as mock_db:
            mock_db.get_latest_user_measurements.return_value = mock_latest
            
            weight, feet, inches = progress_requests.get_latest_measurements(42)
            
            mock_db.get_latest_user_measurements.assert_called_once_with(42)
            self.assertEqual(weight, 0)
            self.assertEqual(feet, 0)
            self.assertEqual(inches, 0)


class TestProgressPostRequests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.mock_session = MOCK_SESSION.copy()
        self.mock_request = MagicMock()

    async def test_update_measurements_success(self):
        """Test successful measurements update"""
        mock_form_data = {
            "weight": "170.5",
            "height_feet": "5",
            "height_inches": "11"
        }
        
        async def mock_form():
            return mock_form_data
            
        self.mock_request.form = mock_form
        
        with patch('fit.web.progress.requests.database_service') as mock_db, \
             patch('fit.web.progress.requests.datetime') as mock_datetime:
            
            mock_now = datetime(2024, 1, 1, 12, 0)
            mock_datetime.now.return_value = mock_now
            
            result = await progress_requests.update_measurements(self.mock_session, self.mock_request)
            
            mock_db.insert_user_measurements.assert_called_once_with(71,170.5,mock_now,42)
            
            self.assertIn("Measurements updated successfully", str(result))
            self.assertIn("closeMeasurementsModal", str(result))
            self.assertIn("window.location.reload", str(result))


if __name__ == '__main__':
    unittest.main() 