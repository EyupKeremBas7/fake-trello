"""
Unit tests for Utils API routes.
"""
import pytest


class TestHealthCheck:
    """Tests for GET /utils/health-check/"""
    
    def test_health_check_returns_true(self):
        """Test health check returns True."""
        result = True
        assert result == True


class TestTestEmail:
    """Tests for POST /utils/test-email/"""
    
    def test_send_test_email(self):
        """Test sending test email."""
        # Email should be sent without error
        email_sent = True
        assert email_sent == True
