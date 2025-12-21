"""
Unit tests for Core Security module.
Tests password hashing and JWT token functions.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch


class TestPasswordHashing:
    """Tests for password hashing functions."""

    def test_get_password_hash(self):
        """Test password hashing returns different value."""
        from app.core.security import get_password_hash

        password = "testpassword123"
        hashed = get_password_hash(password)

        assert hashed != password
        assert len(hashed) > 0

    def test_get_password_hash_different_each_time(self):
        """Test that same password produces different hashes (due to salt)."""
        from app.core.security import get_password_hash

        password = "testpassword123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        # Bcrypt uses random salt, so hashes should be different
        assert hash1 != hash2

    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        from app.core.security import get_password_hash, verify_password

        password = "correctpassword"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test password verification with wrong password."""
        from app.core.security import get_password_hash, verify_password

        password = "correctpassword"
        hashed = get_password_hash(password)

        assert verify_password("wrongpassword", hashed) is False

    def test_verify_password_empty(self):
        """Test password verification with empty password."""
        from app.core.security import get_password_hash, verify_password

        password = "somepassword"
        hashed = get_password_hash(password)

        assert verify_password("", hashed) is False


class TestJWTToken:
    """Tests for JWT token creation."""

    def test_create_access_token(self):
        """Test creating access token."""
        from app.core.security import create_access_token
        import jwt

        subject = "user123"
        expires_delta = timedelta(minutes=30)
        token = create_access_token(subject, expires_delta)

        assert token is not None
        assert len(token) > 0

    def test_create_access_token_with_expiry(self):
        """Test token has expiry claim."""
        from app.core.security import create_access_token
        from app.core.config import settings
        import jwt

        subject = "user123"
        expires_delta = timedelta(minutes=30)
        token = create_access_token(subject, expires_delta)

        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        assert "exp" in decoded
        assert "sub" in decoded
        assert decoded["sub"] == subject

    def test_create_access_token_custom_expiry(self):
        """Test token with custom expiry time."""
        from app.core.security import create_access_token
        from app.core.config import settings
        import jwt

        subject = "user123"
        expires_delta = timedelta(minutes=60)
        token = create_access_token(subject, expires_delta=expires_delta)

        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        assert decoded["sub"] == subject
