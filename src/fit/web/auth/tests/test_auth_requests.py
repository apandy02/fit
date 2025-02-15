import unittest
from unittest.mock import MagicMock, patch

from fasthtml.common import RedirectResponse

from fit.web.auth import requests as auth_requests
from fit.web.auth.clients import fitbit_client_oauth, whoop_client_oauth


class TestAuthRequests(unittest.TestCase):
    def setUp(self):
        self.mock_request = MagicMock()
        self.mock_session = {}
        
    def test_login_localhost(self):
        """Test the login function with localhost (should use http)"""
        self.mock_request.url.hostname = "localhost"
        self.mock_request.url.netloc = "localhost:8000"
        
        with patch.object(fitbit_client_oauth, 'login_link') as mock_fitbit_login:
            with patch.object(whoop_client_oauth, 'login_link') as mock_whoop_login:
                mock_fitbit_login.return_value = "http://fitbit.com/auth"
                mock_whoop_login.return_value = "http://whoop.com/auth"
                result = auth_requests.login(self.mock_request)
                
                mock_fitbit_login.assert_called_once_with("http://localhost:8000/auth_redirect/fitbit")
                mock_whoop_login.assert_called_once_with("http://localhost:8000/auth_redirect/whoop")
                self.assertIn("Sign in with your fitness tracker", str(result))
    
    def test_login_production(self):
        self.mock_request.url.hostname = "fit.example.com"
        self.mock_request.url.netloc = "fit.example.com"
        
        with patch.object(fitbit_client_oauth, 'login_link') as mock_fitbit_login:
            with patch.object(whoop_client_oauth, 'login_link') as mock_whoop_login:
                mock_fitbit_login.return_value = "http://fitbit.com/auth"
                mock_whoop_login.return_value = "http://whoop.com/auth"
                
                result = auth_requests.login(self.mock_request)
                
                mock_fitbit_login.assert_called_once_with("https://fit.example.com/auth_redirect/fitbit")
                mock_whoop_login.assert_called_once_with("https://fit.example.com/auth_redirect/whoop")
                self.assertIn("Sign in with your fitness tracker", str(result))

    def test_fitbit_auth_redirect_new_user(self):
        mock_code = "test_auth_code"
        self.mock_request.url.hostname = "localhost"
        self.mock_request.url.netloc = "localhost:8000"
        
        mock_token_dict = {
            'access_token': 'mock_access_token',
            'refresh_token': 'mock_refresh_token',
            'expires_at': 1234567890,
            'user_id': 'fitbit_user_123'
        }
        
        mock_profile_info = {
            'user': {
                'fullName': 'John Doe',
                'gender': 'MALE',
                'dateOfBirth': '1990-01-01'
            }
        }
        
        with patch('fit.web.auth.requests.fitbit_client') as mock_client:
            mock_client.tracker_type = "fitbit"
        
            mock_client.fetch_access_token.return_value = mock_token_dict
            mock_client.get_info.return_value = mock_profile_info
            
            with patch('fit.web.auth.requests.database_service') as mock_db:
                mock_db.get_user_id.return_value = None
                mock_db.insert_new_user.return_value = {'user_id': 42}
                
                result = auth_requests.fitbit_auth_redirect(mock_code, self.mock_request, self.mock_session)
                
                mock_client.fetch_access_token.assert_called_once_with(
                    mock_code, 
                    "http://localhost:8000/auth_redirect/fitbit"
                )
                mock_db.get_user_id.assert_called_with('fitbit_user_123', 'fitbit')
                mock_db.insert_new_user.assert_called_once_with({
                    'provider_user_id': 'fitbit_user_123',
                    'provider': 'fitbit'
                })
                mock_db.insert_profile.assert_called_once_with({
                    'user_id': 42,
                    'onboarding_stage': 0,
                    'name': 'John Doe',
                    'gender': 'MALE',
                    'date_of_birth': '01-01-1990'
                })
                
                self.assertEqual(self.mock_session['user_id'], 42)
                self.assertEqual(self.mock_session['access_token'], 'mock_access_token')
                self.assertEqual(self.mock_session['access_token_expiry'], 1234567890)
                self.assertEqual(self.mock_session['refresh_token'], 'mock_refresh_token')
                self.assertEqual(self.mock_session['tracker'], 'fitbit')
                self.assertIsInstance(result, RedirectResponse)
                self.assertEqual(result.status_code, 303)
                self.assertEqual(result.headers['location'], '/onboarding/profile')

    def test_fitbit_auth_redirect_existing_user(self):
        mock_code = "test_auth_code"
        self.mock_request.url.hostname = "localhost"
        self.mock_request.url.netloc = "localhost:8000"
        
        mock_token_dict = {
            'access_token': 'mock_access_token',
            'refresh_token': 'mock_refresh_token',
            'expires_at': 1234567890,
            'user_id': 'fitbit_user_123'
        }
        
        with patch('fit.web.auth.requests.fitbit_client') as mock_client:
            mock_client.tracker_type = "fitbit"
            mock_client.fetch_access_token.return_value = mock_token_dict
            
            with patch('fit.web.auth.requests.database_service') as mock_db:
                mock_db.get_user_id.return_value = 42
                
                result = auth_requests.fitbit_auth_redirect(mock_code, self.mock_request, self.mock_session)
                
                mock_client.fetch_access_token.assert_called_once_with(
                    mock_code, 
                    "http://localhost:8000/auth_redirect/fitbit"
                )
                mock_db.get_user_id.assert_called_with('fitbit_user_123', 'fitbit')
                mock_db.insert_new_user.assert_not_called()
                mock_db.insert_profile.assert_not_called()
                
                self.assertEqual(self.mock_session['user_id'], 42)
                self.assertEqual(self.mock_session['access_token'], 'mock_access_token')
                self.assertEqual(self.mock_session['access_token_expiry'], 1234567890)
                self.assertEqual(self.mock_session['refresh_token'], 'mock_refresh_token')
                self.assertEqual(self.mock_session['tracker'], 'fitbit')
                self.assertIsInstance(result, RedirectResponse)
                self.assertEqual(result.status_code, 303)
                self.assertEqual(result.headers['location'], '/nutrition')

    def test_fitbit_auth_redirect_error_handling(self):
        mock_code = "invalid_code"
        self.mock_request.url.hostname = "localhost"
        self.mock_request.url.netloc = "localhost:8000"
        
        with patch('fit.web.auth.requests.fitbit_client') as mock_client:
            mock_client.fetch_access_token.side_effect = Exception("Invalid authorization code")
            
            with self.assertRaises(Exception) as context:
                auth_requests.fitbit_auth_redirect(mock_code, self.mock_request, self.mock_session)
            
            self.assertEqual(str(context.exception), "Invalid authorization code")
            self.assertEqual(self.mock_session, {})

    def test_whoop_auth_redirect_new_user(self):
        mock_code = "test_auth_code"
        self.mock_request.url.hostname = "localhost"
        self.mock_request.url.netloc = "localhost:8000"
        
        mock_token_dict = {
            'access_token': 'mock_access_token',
            'refresh_token': 'mock_refresh_token',
            'expires_at': 1234567890
        }
        
        mock_profile_info = {
            'user_id': 'whoop_user_123',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com'
        }
        
        with patch('fit.web.auth.requests.whoop_client') as mock_client:
            mock_client.tracker_type = "whoop"
            mock_client.fetch_access_token.return_value = mock_token_dict
            mock_client.get_info.return_value = mock_profile_info
            
            with patch('fit.web.auth.requests.database_service') as mock_db:
                mock_db.get_user_id.return_value = None
                mock_db.insert_new_user.return_value = {'user_id': 42}
                
                result = auth_requests.whoop_auth_redirect(mock_code, self.mock_request, self.mock_session)
                
                mock_client.fetch_access_token.assert_called_once_with(
                    mock_code, 
                    "http://localhost:8000/auth_redirect/whoop"
                )
                mock_db.get_user_id.assert_called_with('whoop_user_123', 'whoop')
                mock_db.insert_new_user.assert_called_once_with({
                    'provider_user_id': 'whoop_user_123',
                    'provider': 'whoop'
                })
                mock_db.insert_profile.assert_called_once_with(
                    {
                    'user_id': 42,
                    'onboarding_stage': 0,
                    'name': 'John Doe',
                    'email': 'john.doe@example.com'
                    }
                )
                
                self.assertEqual(self.mock_session['user_id'], 42)
                self.assertEqual(self.mock_session['access_token'], 'mock_access_token')
                self.assertEqual(self.mock_session['access_token_expiry'], 1234567890)
                self.assertEqual(self.mock_session['refresh_token'], 'mock_refresh_token')
                self.assertEqual(self.mock_session['tracker'], 'whoop')
                self.assertIsInstance(result, RedirectResponse)
                self.assertEqual(result.status_code, 303)
                self.assertEqual(result.headers['location'], '/onboarding/profile')

    def test_whoop_auth_redirect_existing_user(self):
        mock_code = "test_auth_code"
        self.mock_request.url.hostname = "localhost"
        self.mock_request.url.netloc = "localhost:8000"
        
        mock_token_dict = {
            'access_token': 'mock_access_token',
            'refresh_token': 'mock_refresh_token',
            'expires_at': 1234567890
        }
        
        mock_profile_info = {
            'user_id': 'whoop_user_123'
        }
        
        with patch('fit.web.auth.requests.whoop_client') as mock_client:
            mock_client.tracker_type = "whoop"
            mock_client.fetch_access_token.return_value = mock_token_dict
            mock_client.get_info.return_value = mock_profile_info
            
            with patch('fit.web.auth.requests.database_service') as mock_db:
                mock_db.get_user_id.return_value = 42
                
                result = auth_requests.whoop_auth_redirect(mock_code, self.mock_request, self.mock_session)
                
                mock_client.fetch_access_token.assert_called_once_with(
                    mock_code, 
                    "http://localhost:8000/auth_redirect/whoop"
                )
                mock_db.get_user_id.assert_called_with('whoop_user_123', 'whoop')
                mock_db.insert_new_user.assert_not_called()
                mock_db.insert_profile.assert_not_called()
                
                self.assertEqual(self.mock_session['user_id'], 42)
                self.assertEqual(self.mock_session['access_token'], 'mock_access_token')
                self.assertEqual(self.mock_session['access_token_expiry'], 1234567890)
                self.assertEqual(self.mock_session['refresh_token'], 'mock_refresh_token')
                self.assertEqual(self.mock_session['tracker'], 'whoop')
                self.assertIsInstance(result, RedirectResponse)
                self.assertEqual(result.status_code, 303)
                self.assertEqual(result.headers['location'], '/nutrition')

    def test_whoop_auth_redirect_error_handling(self):
        mock_code = "invalid_code"
        self.mock_request.url.hostname = "localhost"
        self.mock_request.url.netloc = "localhost:8000"
        
        with patch('fit.web.auth.requests.whoop_client') as mock_client:
            mock_client.fetch_access_token.side_effect = Exception("Invalid authorization code")
            
            with self.assertRaises(Exception) as context:
                auth_requests.whoop_auth_redirect(mock_code, self.mock_request, self.mock_session)
            
            self.assertEqual(str(context.exception), "Invalid authorization code")
            self.assertEqual(self.mock_session, {})

if __name__ == '__main__':
    unittest.main()
