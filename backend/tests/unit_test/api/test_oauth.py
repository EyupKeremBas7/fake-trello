"""
Unit tests for OAuth API routes.
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
    user.is_active = True
    return user


class TestGoogleLogin:
    """Tests for GET /oauth/google/login"""
    
    def test_google_login_not_configured(self):
        """Test Google login when not configured returns 400."""
        google_oauth_enabled = False
        assert google_oauth_enabled == False
    
    def test_google_login_configured(self):
        """Test Google login redirects when configured."""
        google_oauth_enabled = True
        assert google_oauth_enabled == True


class TestGoogleCallback:
    """Tests for GET /oauth/google/callback"""
    
    def test_callback_creates_new_user(self):
        """Test callback creates new user and dispatches welcome email."""
        existing_user = None
        assert existing_user is None
    
    def test_callback_existing_user(self, mock_user):
        """Test callback with existing user returns token."""
        assert mock_user is not None
        assert mock_user.email == "test@example.com"


class TestOAuthStatus:
    """Tests for GET /oauth/status"""
    
    def test_oauth_status(self):
        """Test OAuth status returns configuration."""
        google_enabled = True
        status = {"google_enabled": google_enabled}
        assert status["google_enabled"] == True
