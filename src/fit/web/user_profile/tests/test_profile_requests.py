import unittest
from unittest.mock import MagicMock, patch

from fit.web.user_profile import requests as profile_requests

MOCK_SESSION = {
    "user_id": 42,
    "tracker": "whoop",
    "access_token": "mock_token"
}

MOCK_PROFILE_DATA = {
    "user_id": 42,
    "name": "John Doe",
    "email": "john@example.com",
    "activity_level": "active",
    "weight_goal": "maintain",
    "dietary_restrictions": "vegetarian,gluten-free"
}

class TestProfileGetRequests(unittest.TestCase):
    def setUp(self):
        self.mock_session = MOCK_SESSION.copy()

    def test_get_profile_page_with_restrictions(self):
        """Test getting profile page with existing dietary restrictions"""
        with patch('fit.web.user_profile.requests.database_service') as mock_db:
            mock_db.get_profile_data.return_value = MOCK_PROFILE_DATA
            
            result = profile_requests.get(self.mock_session)
            
            mock_db.get_profile_data.assert_called_once_with(42)
            self.assertIn("John Doe", str(result))
            self.assertIn("vegetarian", str(result))
            self.assertIn("gluten-free", str(result))

    def test_get_profile_page_no_restrictions(self):
        """Test getting profile page with no dietary restrictions"""
        profile_no_restrictions = MOCK_PROFILE_DATA.copy()
        profile_no_restrictions["dietary_restrictions"] = ""
        
        with patch('fit.web.user_profile.requests.database_service') as mock_db:
            mock_db.get_profile_data.return_value = profile_no_restrictions
            
            result = profile_requests.get(self.mock_session)
            
            mock_db.get_profile_data.assert_called_once_with(42)
            self.assertIn("John Doe", str(result))

    def test_get_profile_page_null_restrictions(self):
        """Test getting profile page with null dietary restrictions"""
        profile_null_restrictions = MOCK_PROFILE_DATA.copy()
        profile_null_restrictions["dietary_restrictions"] = None
        
        with patch('fit.web.user_profile.requests.database_service') as mock_db:
            mock_db.get_profile_data.return_value = profile_null_restrictions
            
            result = profile_requests.get(self.mock_session)
        
            mock_db.get_profile_data.assert_called_once_with(42)
            self.assertIn("John Doe", str(result))

class TestProfilePostRequests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.mock_session = MOCK_SESSION.copy()
        self.mock_request = MagicMock()

    async def test_update_profile_success(self):
        """Test successful profile update with dietary restrictions"""
        mock_form_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "activity_level": "active",
            "weight_goal": "maintain",
            "existing_restrictions[]": ["vegetarian", "gluten-free"]
        }
        
        async def mock_form():
            return MagicMock(
                get=lambda x: mock_form_data.get(x),
                getlist=lambda x: mock_form_data.get(x, [])
            )
            
        self.mock_request.form = mock_form
        
        with patch('fit.web.user_profile.requests.database_service') as mock_db:
            result = await profile_requests.update_profile(self.mock_session, self.mock_request)
            
            expected_data = {
                "dietary_restrictions": "vegetarian,gluten-free",
                "user_id": 42
            }
            
            mock_db.update_profile.assert_called_once_with(expected_data)
            self.assertIn("Profile updated successfully", str(result))

    async def test_update_profile_no_restrictions(self):
        """Test profile update with no dietary restrictions"""
        mock_form_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "activity_level": "active",
            "weight_goal": "maintain",
            "existing_restrictions[]": []
        }
        
        async def mock_form():
            return MagicMock(
                get=lambda x: mock_form_data.get(x),
                getlist=lambda x: mock_form_data.get(x, [])
            )
            
        self.mock_request.form = mock_form
        
        with patch('fit.web.user_profile.requests.database_service') as mock_db:
            result = await profile_requests.update_profile(self.mock_session, self.mock_request)
            
            expected_data = {
                "dietary_restrictions": "",
                "user_id": 42
            }
            
            mock_db.update_profile.assert_called_once_with(expected_data)
            self.assertIn("Profile updated successfully", str(result))

    async def test_update_profile_error(self):
        """Test profile update with database error"""
        mock_form_data = {
            "name": "John Doe",
            "existing_restrictions[]": ["vegetarian"]
        }
        
        async def mock_form():
            return mock_form_data
            
        self.mock_request.form = mock_form
        
        with patch('fit.web.user_profile.requests.database_service') as mock_db:
            mock_db.update_profile.side_effect = Exception("Database error")
            
            result = await profile_requests.update_profile(self.mock_session, self.mock_request)
            self.assertIn("Error updating profile", str(result))

    async def test_add_restriction_success(self):
        """Test successfully adding a new dietary restriction"""
        mock_form_data = {
            "dietary_restrictions": "vegan",
            "existing_restrictions[]": ["vegetarian"]
        }
        
        async def mock_form():
            return MagicMock(
                get=lambda x: mock_form_data.get(x),
                getlist=lambda x: mock_form_data.get(x, [])
            )
            
        self.mock_request.form = mock_form
        
        result = await profile_requests.add_restriction(self.mock_request)
        print(f"Result: {str(result)}")
        self.assertIn("vegan", str(result))
        self.assertIn("vegetarian", str(result))

    async def test_add_restriction_duplicate(self):
        """Test adding a duplicate dietary restriction"""
        mock_form_data = {
            "dietary_restrictions": "vegetarian",
            "existing_restrictions[]": ["vegetarian"]
        }
        
        async def mock_form():
            return MagicMock(
                get=lambda x: mock_form_data.get(x),
                getlist=lambda x: mock_form_data.get(x, [])
            )
            
        self.mock_request.form = mock_form
        
        result = await profile_requests.add_restriction(self.mock_request)
        self.assertEqual(str(result).count("vegetarian"), 2)

    async def test_add_restriction_error(self):
        """Test adding a restriction with an error"""
        self.mock_request.form.side_effect = Exception("Form error")
        
        result = await profile_requests.add_restriction(self.mock_request)
        self.assertIn("Error adding restriction", str(result))

    async def test_remove_restriction_success(self):
        """Test successfully removing a dietary restriction"""
        mock_form_data = {
            "restriction": "vegetarian",
            "existing_restrictions[]": ["vegetarian", "gluten-free"]
        }
        
        async def mock_form():
            return MagicMock(
                get=lambda x: mock_form_data.get(x),
                getlist=lambda x: mock_form_data.get(x, [])
            )
            
        self.mock_request.form = mock_form
        
        result = await profile_requests.remove_restriction(self.mock_request)
        
        self.assertNotIn("vegetarian", str(result))
        self.assertIn("gluten-free", str(result))

    async def test_remove_restriction_not_found(self):
        """Test removing a restriction that doesn't exist"""
        mock_form_data = {
            "restriction": "vegan",
            "existing_restrictions[]": ["vegetarian", "gluten-free"]
        }
        
        async def mock_form():
            return MagicMock(
                get=lambda x: mock_form_data.get(x),
                getlist=lambda x: mock_form_data.get(x, [])
            )
            
        self.mock_request.form = mock_form
        
        result = await profile_requests.remove_restriction(self.mock_request)
        
        self.assertIn("vegetarian", str(result))
        self.assertIn("gluten-free", str(result))

    async def test_remove_restriction_error(self):
        """Test removing a restriction with an error"""
        self.mock_request.form.side_effect = Exception("Form error")
        
        result = await profile_requests.remove_restriction(self.mock_request)
        self.assertIn("Error removing restriction", str(result))


if __name__ == '__main__':
    unittest.main() 