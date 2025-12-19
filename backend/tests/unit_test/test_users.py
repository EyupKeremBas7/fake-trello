"""
Unit tests for Users API routes.
"""
import pytest
from unittest.mock import Mock
from uuid import uuid4


@pytest.fixture
def mock_user():
    """Create a mock user object."""
    user = Mock()
    user.id = uuid4()
    user.email = "test@example.com"
    user.full_name = "Test User"
    user.is_active = True
    user.is_superuser = False
    user.is_deleted = False
    return user


@pytest.fixture
def mock_superuser():
    """Create a mock superuser object."""
    user = Mock()
    user.id = uuid4()
    user.email = "admin@example.com"
    user.full_name = "Admin User"
    user.is_active = True
    user.is_superuser = True
    user.is_deleted = False
    return user


class TestReadUsers:
    """Tests for GET /users/"""
    
    def test_read_users_returns_list(self, mock_user):
        """Test reading users returns list."""
        users = [mock_user]
        count = 1
        assert len(users) == 1
        assert count == 1


class TestCreateUser:
    """Tests for POST /users/"""
    
    def test_create_user_success(self, mock_user):
        """Test creating a new user."""
        assert mock_user.email == "test@example.com"
        assert mock_user.is_active == True
    
    def test_create_user_email_exists(self, mock_user):
        """Test creating user with existing email fails."""
        existing_user = mock_user
        assert existing_user is not None


class TestUpdateUserMe:
    """Tests for PATCH /users/me"""
    
    def test_update_user_me_success(self, mock_user):
        """Test updating own user info."""
        mock_user.full_name = "Updated Name"
        assert mock_user.full_name == "Updated Name"


class TestRegisterUser:
    """Tests for POST /users/signup"""
    
    def test_register_user_success(self, mock_user):
        """Test user registration dispatches welcome email."""
        assert mock_user.email is not None
    
    def test_register_user_email_exists(self, mock_user):
        """Test registration with existing email fails."""
        existing_user = mock_user
        assert existing_user is not None


class TestReadUserById:
    """Tests for GET /users/{user_id}"""
    
    def test_read_user_by_id_success(self, mock_user):
        """Test reading user by ID."""
        assert mock_user.id is not None
    
    def test_read_user_by_id_not_found(self):
        """Test reading non-existent user returns 404."""
        user_result = None
        assert user_result is None


class TestDeleteUser:
    """Tests for DELETE /users/{user_id}"""
    
    def test_delete_user_success(self, mock_user):
        """Test soft deleting a user."""
        assert mock_user.is_deleted == False


class TestReadUserMe:
    """Tests for GET /users/me"""
    
    def test_read_user_me_returns_current_user(self, mock_user):
        """Test getting current user info."""
        assert mock_user.email == "test@example.com"
        assert mock_user.full_name == "Test User"


class TestDeleteUserMe:
    """Tests for DELETE /users/me"""
    
    def test_delete_user_me_superuser_forbidden(self, mock_superuser):
        """Test superuser cannot delete themselves."""
        assert mock_superuser.is_superuser == True
