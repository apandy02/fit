import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

import fasthtml.common as fh
from fasthtml.common import RedirectResponse

from fit.web.onboarding import requests as onboarding_requests

MOCK_SESSION = {"user_id": 42}
MOCK_PROFILE_DATA = {
    "user_id": 42,
    "name": "Test User",
    "onboarding_stage": 0
}



class TestOnboardingGetRequests(unittest.TestCase):
    def setUp(self):
        self.mock_session = MOCK_SESSION
        self.mock_profile_data = MOCK_PROFILE_DATA
        self.mock_request = MagicMock()

    def test_get_profile_page_new_user(self):
        """Test profile page for new user"""
        with patch('fit.web.onboarding.requests.database_service') as mock_db:
            mock_db.get_profile_data.return_value = self.mock_profile_data
            
            result = onboarding_requests.get_profile_page(self.mock_session)
            
            self.assertEqual(mock_db.get_profile_data.call_count, 2)
            mock_db.get_profile_data.assert_has_calls([
                unittest.mock.call(42),
                unittest.mock.call(42)
            ])
            self.assertIn("Profile", str(result))
            self.assertIn("form", str(result).lower())

    def test_get_profile_page_completed_onboarding(self):
        """Test profile page redirects if user completed onboarding"""
        completed_profile = self.mock_profile_data.copy()
        completed_profile["onboarding_stage"] = 5
        
        with patch('fit.web.onboarding.requests.database_service') as mock_db:
            mock_db.get_profile_data.return_value = completed_profile
            
            result = onboarding_requests.get_profile_page(self.mock_session)
            
            self.assertIsInstance(result, RedirectResponse)
            self.assertEqual(result.status_code, 303)
            self.assertEqual(result.headers["location"], "/nutrition")

    def test_get_activity_page_new_user(self):
        """Test activity page for new user"""
        with patch('fit.web.onboarding.requests.database_service') as mock_db:
            mock_db.get_profile_data.return_value = self.mock_profile_data
            
            result = onboarding_requests.get_activity_page(self.mock_session)
            
            mock_db.get_profile_data.assert_called_once_with(42)
            self.assertIn("How Active Are You?", str(result))
            self.assertIn("form", str(result).lower())

    def test_get_activity_page_completed_onboarding(self):
        """Test activity page redirects if user completed onboarding"""
        completed_profile = self.mock_profile_data.copy()
        completed_profile["onboarding_stage"] = 5
        
        with patch('fit.web.onboarding.requests.database_service') as mock_db:
            mock_db.get_profile_data.return_value = completed_profile
            
            result = onboarding_requests.get_activity_page(self.mock_session)
            
            self.assertIsInstance(result, RedirectResponse)
            self.assertEqual(result.status_code, 303)
            self.assertEqual(result.headers["location"], "/nutrition")

    def test_get_dietary_page_new_user(self):
        """Test dietary page for new user"""
        with patch('fit.web.onboarding.requests.database_service') as mock_db:
            mock_db.get_profile_data.return_value = self.mock_profile_data
            
            result = onboarding_requests.get_dietary_page(self.mock_session)
            
            mock_db.get_profile_data.assert_called_once_with(42)
            self.assertIn("Dietary Restrictions", str(result))
            self.assertIn("form", str(result).lower())

    def test_get_dietary_page_completed_onboarding(self):
        """Test dietary page redirects if user completed onboarding"""
        completed_profile = self.mock_profile_data.copy()
        completed_profile["onboarding_stage"] = 5
        
        with patch('fit.web.onboarding.requests.database_service') as mock_db:
            mock_db.get_profile_data.return_value = completed_profile
            
            result = onboarding_requests.get_dietary_page(self.mock_session)
            
            self.assertIsInstance(result, RedirectResponse)
            self.assertEqual(result.status_code, 303)
            self.assertEqual(result.headers["location"], "/nutrition")

    def test_get_goals_page_new_user(self):
        """Test goals page for new user"""
        with patch('fit.web.onboarding.requests.database_service') as mock_db:
            mock_db.get_profile_data.return_value = self.mock_profile_data
            
            result = onboarding_requests.get_goals_page(self.mock_session)
            
            mock_db.get_profile_data.assert_called_once_with(42)
            self.assertIn("What are your weight goals?", str(result))
            self.assertIn("form", str(result).lower())

    def test_get_goals_page_completed_onboarding(self):
        """Test goals page redirects if user completed onboarding"""
        completed_profile = self.mock_profile_data.copy()
        completed_profile["onboarding_stage"] = 5
        
        with patch('fit.web.onboarding.requests.database_service') as mock_db:
            mock_db.get_profile_data.return_value = completed_profile
            
            result = onboarding_requests.get_goals_page(self.mock_session)
            
            self.assertIsInstance(result, RedirectResponse)
            self.assertEqual(result.status_code, 303)
            self.assertEqual(result.headers["location"], "/nutrition")

    def test_get_measurements_page_new_user(self):
        """Test measurements page for new user"""
        with patch('fit.web.onboarding.requests.database_service') as mock_db:
            mock_db.get_profile_data.return_value = self.mock_profile_data
            
            result = onboarding_requests.get_measurements_page(self.mock_session)
            
            mock_db.get_profile_data.assert_called_once_with(42)
            self.assertIn("Body Measurements", str(result))
            self.assertIn("form", str(result).lower())

    def test_get_measurements_page_completed_onboarding(self):
        """Test measurements page redirects if user completed onboarding"""
        completed_profile = self.mock_profile_data.copy()
        completed_profile["onboarding_stage"] = 5
        
        with patch('fit.web.onboarding.requests.database_service') as mock_db:
            mock_db.get_profile_data.return_value = completed_profile
            
            result = onboarding_requests.get_measurements_page(self.mock_session)
            
            self.assertIsInstance(result, RedirectResponse)
            self.assertEqual(result.status_code, 303)
            self.assertEqual(result.headers["location"], "/nutrition")

    
class TestOnboardingPostRequests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.mock_session = MOCK_SESSION
        self.mock_request = MagicMock()

    async def test_handle_profile_completion_success(self):
        """Test successful profile completion"""
        mock_form_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "gender": "MALE",
            "date_of_birth": "1990-01-01"
        }
        
        async def mock_form():
            return mock_form_data
            
        self.mock_request.form = mock_form
        
        with patch('fit.web.onboarding.requests.database_service') as mock_db:
            result = await onboarding_requests.handle_profile_completion(self.mock_session, self.mock_request)
            
            expected_db_data = mock_form_data.copy()
            expected_db_data["user_id"] = 42
            expected_db_data["onboarding_stage"] = 1
            
            mock_db.update_profile.assert_called_once_with(expected_db_data)
            self.assertIsInstance(result, fh.Response)
            self.assertEqual(result.headers["HX-Redirect"], "/onboarding/measurements")

    async def test_handle_profile_completion_error(self):
        """Test profile completion with database error"""
        mock_form_data = {"name": "John Doe"}
        
        async def mock_form():
            return mock_form_data
            
        self.mock_request.form = mock_form
        
        with patch('fit.web.onboarding.requests.database_service') as mock_db:
            mock_db.update_profile.side_effect = Exception("Database error")
            
            result = await onboarding_requests.handle_profile_completion(self.mock_session, self.mock_request)
            
            self.assertIn("Error updating profile", str(result))

    async def test_handle_measurements_completion_success(self):
        """Test successful measurements submission"""
        mock_form_data = {
            "weight": "170.5",
            "height_feet": "5",
            "height_inches": "11"
        }
        
        async def mock_form():
            return mock_form_data
            
        self.mock_request.form = mock_form
        
        with patch('fit.web.onboarding.requests.database_service') as mock_db:
            result = await onboarding_requests.handle_measurements_completion(self.mock_session, self.mock_request)
            
            mock_db.update_profile.assert_called_once_with({
                "user_id": 42,
                "onboarding_stage": 2
            })
            mock_db.insert_measurement.assert_called_once_with(
                user_id=42,
                weight=170.5,
                height=71, 
                date=datetime.today().date()
            )
            
            self.assertIsInstance(result, fh.Response)
            self.assertEqual(result.headers["HX-Redirect"], "/onboarding/dietary")


    async def test_handle_measurements_completion_error_database(self):
        """Test measurements submission with database error"""
        mock_form_data = {
            "weight": "170.5",
            "height_feet": "5",
            "height_inches": "11"
        }
        
        async def mock_form():
            return mock_form_data
            
        self.mock_request.form = mock_form
        
        with patch('fit.web.onboarding.requests.database_service') as mock_db:
            mock_db.update_profile.side_effect = Exception("Database error")
            
            result = await onboarding_requests.handle_measurements_completion(self.mock_session, self.mock_request)
            self.assertIn("Error updating measurements", str(result))

    async def test_handle_dietary_completion_success(self):
        """Test successful dietary restrictions submission"""
        mock_form_data = MagicMock()
        mock_form_data.getlist.return_value = ["vegetarian", "gluten-free"]
        
        async def mock_form():
            return mock_form_data
            
        self.mock_request.form = mock_form
        
        with patch('fit.web.onboarding.requests.database_service') as mock_db:
            result = await onboarding_requests.handle_dietary_completion(self.mock_session, self.mock_request)
            
            mock_db.update_profile.assert_called_once_with({
                "user_id": 42,
                "dietary_restrictions": "vegetarian,gluten-free",
                "onboarding_stage": 3
            })
            
            self.assertIsInstance(result, fh.Response)
            self.assertEqual(result.headers["HX-Redirect"], "/onboarding/activity")

    async def test_handle_dietary_completion_no_restrictions(self):
        """Test dietary restrictions submission with no restrictions"""
        mock_form_data = MagicMock()
        mock_form_data.getlist.return_value = []
        
        async def mock_form():
            return mock_form_data
            
        self.mock_request.form = mock_form
        
        with patch('fit.web.onboarding.requests.database_service') as mock_db:
            result = await onboarding_requests.handle_dietary_completion(self.mock_session, self.mock_request)
            
            mock_db.update_profile.assert_called_once_with({
                "user_id": 42,
                "dietary_restrictions": "",
                "onboarding_stage": 3
            })
            
            self.assertIsInstance(result, fh.Response)
            self.assertEqual(result.headers["HX-Redirect"], "/onboarding/activity")

    async def test_handle_dietary_completion_error(self):
        """Test dietary restrictions submission with error"""
        mock_form_data = MagicMock()
        mock_form_data.getlist.return_value = ["vegetarian"]
        
        async def mock_form():
            return mock_form_data
            
        self.mock_request.form = mock_form
        
        with patch('fit.web.onboarding.requests.database_service') as mock_db:
            mock_db.update_profile.side_effect = Exception("Error occurred")
            
            result = await onboarding_requests.handle_dietary_completion(self.mock_session, self.mock_request)
            self.assertIn("Error updating dietary restrictions", str(result))

    async def test_handle_activity_selection_success(self):
        """Test successful activity level selection"""
        mock_form_data = {
            "activity_level": "active"
        }
        
        async def mock_form():
            return mock_form_data
            
        self.mock_request.form = mock_form
        
        with patch('fit.web.onboarding.requests.database_service') as mock_db:
            result = await onboarding_requests.handle_activity_selection(self.mock_session, self.mock_request)
            
            mock_db.update_profile.assert_called_once_with({
                "user_id": 42,
                "activity_level": "active",
                "onboarding_stage": 4
            })
            
            self.assertIsInstance(result, fh.Response)
            self.assertEqual(result.headers["HX-Redirect"], "/onboarding/goals")

    async def test_handle_activity_selection_error(self):
        """Test activity level selection with error"""
        mock_form_data = {
            "activity_level": "active"
        }
        
        async def mock_form():
            return mock_form_data
            
        self.mock_request.form = mock_form
        
        with patch('fit.web.onboarding.requests.database_service') as mock_db:
            mock_db.update_profile.side_effect = Exception("Error occurred")
            
            result = await onboarding_requests.handle_activity_selection(self.mock_session, self.mock_request)
            self.assertIn("Error updating activity level", str(result))

    async def test_handle_goals_selection_success(self):
        """Test successful goals selection"""
        mock_form_data = {
            "weight_goal": "lose",
        }
        
        async def mock_form():
            return mock_form_data
            
        self.mock_request.form = mock_form
        
        with patch('fit.web.onboarding.requests.database_service') as mock_db:
            result = await onboarding_requests.handle_goals_selection(self.mock_session, self.mock_request)
            
            mock_db.update_profile.assert_called_once_with({
                "user_id": 42,
                "weight_goal": "lose",
                "onboarding_stage": 5
            })
            
            self.assertIsInstance(result, fh.Response)
            self.assertEqual(result.headers["HX-Redirect"], "/nutrition")

    async def test_handle_goals_selection_error(self):
        """Test goals selection with error"""
        mock_form_data = {
            "weight_goal": "lose",
        }
        
        async def mock_form():
            return mock_form_data
            
        self.mock_request.form = mock_form
        
        with patch('fit.web.onboarding.requests.database_service') as mock_db:
            mock_db.update_profile.side_effect = Exception("Error occurred")
            
            result = await onboarding_requests.handle_goals_selection(self.mock_session, self.mock_request)
            self.assertIn("Error updating goals", str(result))


if __name__ == '__main__':
    unittest.main()
