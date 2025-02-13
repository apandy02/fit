import unittest
from unittest.mock import MagicMock, patch

from fit.web.auth import requests as auth_requests
from fit.web.auth.clients import fitbit_client_oauth, whoop_client_oauth


class TestAuthRequests(unittest.TestCase):
    def setUp(self):
        self.mock_request = MagicMock()
        self.mock_session = {}
        
    def test_login_localhost(self):
        """Test the login function with localhost (should use http)"""
        # Setup mock request with localhost
        self.mock_request.url.hostname = "localhost"
        self.mock_request.url.netloc = "localhost:8000"
        
        # Mock the login_link methods
        with patch.object(fitbit_client_oauth, 'login_link') as mock_fitbit_login:
            with patch.object(whoop_client_oauth, 'login_link') as mock_whoop_login:
                mock_fitbit_login.return_value = "http://fitbit.com/auth"
                mock_whoop_login.return_value = "http://whoop.com/auth"
                
                result = auth_requests.login(self.mock_request)
                
                # Verify the login links were called with correct http URLs for localhost
                mock_fitbit_login.assert_called_once_with("http://localhost:8000/auth_redirect/fitbit")
                mock_whoop_login.assert_called_once_with("http://localhost:8000/auth_redirect/whoop")
                
                # Verify result contains login page
                self.assertIn("Sign in with your fitness tracker", str(result))
    
    def test_login_production(self):
        """Test the login function with production domain (should use https)"""
        # Setup mock request with production domain
        self.mock_request.url.hostname = "fit.example.com"
        self.mock_request.url.netloc = "fit.example.com"
        
        # Mock the login_link methods
        with patch.object(fitbit_client_oauth, 'login_link') as mock_fitbit_login:
            with patch.object(whoop_client_oauth, 'login_link') as mock_whoop_login:
                mock_fitbit_login.return_value = "http://fitbit.com/auth"
                mock_whoop_login.return_value = "http://whoop.com/auth"
                
                result = auth_requests.login(self.mock_request)
                
                # Verify the login links were called with correct https URLs for production
                mock_fitbit_login.assert_called_once_with("https://fit.example.com/auth_redirect/fitbit")
                mock_whoop_login.assert_called_once_with("https://fit.example.com/auth_redirect/whoop")
                
                # Verify result contains login page
                self.assertIn("Sign in with your fitness tracker", str(result))

    

if __name__ == '__main__':
    unittest.main()
