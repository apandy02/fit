import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from fasthtml.common import RedirectResponse

from fit.web.bw import (auth_before, onboarding_before,
                        onboarding_complete_before)

MOCK_SESSION = {
    "user_id": 42,
    "access_token": "mock_token",
    "access_token_expiry": datetime.now().timestamp() + 3600 
}

class TestAuthBeforeware(unittest.TestCase):
    def setUp(self):
        self.mock_request = MagicMock()
        self.mock_request.scope = {}
        self.mock_session = MOCK_SESSION.copy()

    def test_auth_valid_token(self):
        """Test auth beforeware with valid token"""
        result = auth_before(self.mock_request, self.mock_session)
        
        self.assertIsNone(result)
        self.assertEqual(
            self.mock_request.scope["auth"],
            self.mock_session["access_token_expiry"]
        )

    def test_auth_expired_token(self):
        """Test auth beforeware with expired token"""
        self.mock_session["access_token_expiry"] = datetime.now().timestamp() - 3600  # 1 hour ago
        
        result = auth_before(self.mock_request, self.mock_session)
        
        self.assertIsInstance(result, RedirectResponse)
        self.assertEqual(result.status_code, 303)
        self.assertEqual(result.headers["location"], "/login")

    def test_auth_no_token(self):
        """Test auth beforeware with no token"""
        self.mock_session = {}
        
        result = auth_before(self.mock_request, self.mock_session)
        
        self.assertIsInstance(result, RedirectResponse)
        self.assertEqual(result.status_code, 303)
        self.assertEqual(result.headers["location"], "/login")


class TestOnboardingBeforeware(unittest.TestCase):
    def setUp(self):
        self.mock_request = MagicMock()
        self.mock_session = MOCK_SESSION.copy()

    def test_onboarding_stage_0(self):
        """Test onboarding beforeware at stage 0 (profile)"""
        with patch('fit.web.bw.database_service') as mock_db:
            mock_db.get_profile_data.return_value = {"onboarding_stage": 0}
            
            result = onboarding_before(self.mock_request, self.mock_session)
            
            mock_db.get_profile_data.assert_called_once_with(42)
            self.assertIsInstance(result, RedirectResponse)
            self.assertEqual(result.status_code, 303)
            self.assertEqual(result.headers["location"], "/onboarding/profile")

    def test_onboarding_stage_1(self):
        """Test onboarding beforeware at stage 1 (measurements)"""
        with patch('fit.web.bw.database_service') as mock_db:
            mock_db.get_profile_data.return_value = {"onboarding_stage": 1}
            
            result = onboarding_before(self.mock_request, self.mock_session)
            
            self.assertIsInstance(result, RedirectResponse)
            self.assertEqual(result.headers["location"], "/onboarding/measurements")

    def test_onboarding_stage_2(self):
        """Test onboarding beforeware at stage 2 (dietary)"""
        with patch('fit.web.bw.database_service') as mock_db:
            mock_db.get_profile_data.return_value = {"onboarding_stage": 2}
            
            result = onboarding_before(self.mock_request, self.mock_session)
            
            self.assertIsInstance(result, RedirectResponse)
            self.assertEqual(result.headers["location"], "/onboarding/dietary")

    def test_onboarding_stage_3(self):
        """Test onboarding beforeware at stage 3 (activity)"""
        with patch('fit.web.bw.database_service') as mock_db:
            mock_db.get_profile_data.return_value = {"onboarding_stage": 3}
            
            result = onboarding_before(self.mock_request, self.mock_session)
            
            self.assertIsInstance(result, RedirectResponse)
            self.assertEqual(result.headers["location"], "/onboarding/activity")

    def test_onboarding_stage_4(self):
        """Test onboarding beforeware at stage 4 (goals)"""
        with patch('fit.web.bw.database_service') as mock_db:
            mock_db.get_profile_data.return_value = {"onboarding_stage": 4}
            
            result = onboarding_before(self.mock_request, self.mock_session)
            
            self.assertIsInstance(result, RedirectResponse)
            self.assertEqual(result.headers["location"], "/onboarding/goals")

    def test_onboarding_completed(self):
        """Test onboarding beforeware when onboarding is complete"""
        with patch('fit.web.bw.database_service') as mock_db:
            mock_db.get_profile_data.return_value = {"onboarding_stage": 5}
            
            result = onboarding_before(self.mock_request, self.mock_session)
            
            self.assertIsNone(result)


class TestOnboardingCompleteBeforeware(unittest.TestCase):
    def setUp(self):
        self.mock_request = MagicMock()
        self.mock_session = MOCK_SESSION.copy()

    def test_block_completed_user(self):
        """Test blocking onboarding pages for completed users"""
        with patch('fit.web.bw.database_service') as mock_db:
            mock_db.get_profile_data.return_value = {"onboarding_stage": 5}
            
            result = onboarding_complete_before(self.mock_request, self.mock_session)
            
            mock_db.get_profile_data.assert_called_once_with(42)
            self.assertIsInstance(result, RedirectResponse)
            self.assertEqual(result.status_code, 303)
            self.assertEqual(result.headers["location"], "/nutrition")

    def test_allow_incomplete_user(self):
        """Test allowing incomplete users to access onboarding pages"""
        with patch('fit.web.bw.database_service') as mock_db:
            mock_db.get_profile_data.return_value = {"onboarding_stage": 2}
            
            result = onboarding_complete_before(self.mock_request, self.mock_session)
            
            self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main() 