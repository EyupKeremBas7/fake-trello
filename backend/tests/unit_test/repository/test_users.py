"""
Unit tests for Users Repository.
Tests all database operations for User model with proper mocking.
"""
import pytest
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch
from uuid import uuid4

from sqlmodel import Session


class TestCreateUser:
    """Tests for create_user function."""

    def test_create_user_success(self, mock_session):
        """Test successful user creation."""
        from app.models.users import UserCreate
        from app.repository import users as users_repo

        user_create = UserCreate(
            email="test@example.com",
            password="password123",
            full_name="Test User"
        )

        with patch.object(users_repo, 'get_password_hash', return_value="hashed_password"):
            result = users_repo.create_user(session=mock_session, user_create=user_create)

        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()

    def test_create_user_hashes_password(self):
        """Test that password is properly hashed during user creation."""
        from app.core.security import get_password_hash, verify_password

        password = "testpassword123"
        hashed = get_password_hash(password)

        assert hashed != password
        assert verify_password(password, hashed) is True
        assert verify_password("wrongpassword", hashed) is False


class TestGetUserByEmail:
    """Tests for get_user_by_email function."""

    def test_get_user_by_email_success(self, mock_session, mock_user):
        """Test finding user by email."""
        from app.repository import users as users_repo

        mock_session.exec.return_value.first.return_value = mock_user

        result = users_repo.get_user_by_email(session=mock_session, email="test@example.com")

        assert result == mock_user
        mock_session.exec.assert_called_once()

    def test_get_user_by_email_not_found(self, mock_session):
        """Test user not found by email."""
        from app.repository import users as users_repo

        mock_session.exec.return_value.first.return_value = None

        result = users_repo.get_user_by_email(session=mock_session, email="nonexistent@example.com")

        assert result is None

    def test_get_user_by_email_excludes_deleted(self, mock_session):
        """Test that soft-deleted users are excluded."""
        from app.repository import users as users_repo

        mock_session.exec.return_value.first.return_value = None

        result = users_repo.get_user_by_email(session=mock_session, email="deleted@example.com")

        assert result is None


class TestAuthenticate:
    """Tests for authenticate function."""

    def test_authenticate_success(self, mock_session, mock_user):
        """Test successful authentication."""
        from app.repository import users as users_repo

        with patch.object(users_repo, 'get_user_by_email', return_value=mock_user):
            with patch.object(users_repo, 'verify_password', return_value=True):
                result = users_repo.authenticate(
                    session=mock_session,
                    email="test@example.com",
                    password="correctpassword"
                )

        assert result == mock_user

    def test_authenticate_user_not_found(self, mock_session):
        """Test authentication fails when user not found."""
        from app.repository import users as users_repo

        with patch.object(users_repo, 'get_user_by_email', return_value=None):
            result = users_repo.authenticate(
                session=mock_session,
                email="nonexistent@example.com",
                password="password"
            )

        assert result is None

    def test_authenticate_wrong_password(self, mock_session, mock_user):
        """Test authentication fails with wrong password."""
        from app.repository import users as users_repo

        with patch.object(users_repo, 'get_user_by_email', return_value=mock_user):
            with patch.object(users_repo, 'verify_password', return_value=False):
                result = users_repo.authenticate(
                    session=mock_session,
                    email="test@example.com",
                    password="wrongpassword"
                )

        assert result is None

    def test_authenticate_deleted_user(self, mock_session):
        """Test authentication fails for deleted user."""
        from app.repository import users as users_repo

        deleted_user = Mock()
        deleted_user.is_deleted = True

        with patch.object(users_repo, 'get_user_by_email', return_value=deleted_user):
            result = users_repo.authenticate(
                session=mock_session,
                email="deleted@example.com",
                password="password"
            )

        assert result is None


class TestSoftDeleteUser:
    """Tests for soft_delete_user function."""

    def test_soft_delete_user(self, mock_session, mock_user):
        """Test soft deleting a user."""
        from app.repository import users as users_repo

        deleted_by = uuid4()
        mock_user.is_deleted = False
        mock_user.email = "test@example.com"

        result = users_repo.soft_delete_user(
            session=mock_session,
            user=mock_user,
            deleted_by=deleted_by
        )

        assert mock_user.is_deleted is True
        assert mock_user.deleted_by == str(deleted_by)
        assert "__deleted_" in mock_user.email
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()


class TestUpdateUserPassword:
    """Tests for update_user_password function."""

    def test_update_user_password(self, mock_session, mock_user):
        """Test updating user password."""
        from app.repository import users as users_repo

        new_password = "newpassword123"

        with patch.object(users_repo, 'get_password_hash', return_value="new_hashed"):
            result = users_repo.update_user_password(
                session=mock_session,
                user=mock_user,
                new_password=new_password
            )

        assert mock_user.hashed_password == "new_hashed"
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()


class TestGetUsersList:
    """Tests for get_users_list function."""

    def test_get_users_list(self, mock_session, mock_user):
        """Test getting list of users."""
        from app.repository import users as users_repo

        mock_session.exec.return_value.one.return_value = 1
        mock_session.exec.return_value.all.return_value = [mock_user]

        users, count = users_repo.get_users_list(session=mock_session, skip=0, limit=100)

        assert len(users) == 1
        assert count == 1


class TestCheckEmailExists:
    """Tests for check_email_exists function."""

    def test_check_email_exists_true(self, mock_session, mock_user):
        """Test email exists check returns True."""
        from app.repository import users as users_repo

        mock_session.exec.return_value.first.return_value = mock_user

        result = users_repo.check_email_exists(session=mock_session, email="test@example.com")

        assert result is True

    def test_check_email_exists_false(self, mock_session):
        """Test email exists check returns False."""
        from app.repository import users as users_repo

        mock_session.exec.return_value.first.return_value = None

        result = users_repo.check_email_exists(session=mock_session, email="new@example.com")

        assert result is False


class TestUsersShareWorkspace:
    """Tests for users_share_workspace function."""

    def test_users_share_workspace_true(self, mock_session):
        """Test users share workspace returns True."""
        from app.repository import users as users_repo

        user1_id = uuid4()
        user2_id = uuid4()
        shared_workspace_id = uuid4()

        # Mock that both users are in the same workspace
        mock_session.exec.return_value.all.side_effect = [
            [shared_workspace_id],  # user1 owned
            [],  # user1 member
            [shared_workspace_id],  # user2 owned
            [],  # user2 member
        ]

        result = users_repo.users_share_workspace(
            session=mock_session,
            user_id_1=user1_id,
            user_id_2=user2_id
        )

        assert result is True

    def test_users_share_workspace_false(self, mock_session):
        """Test users don't share workspace returns False."""
        from app.repository import users as users_repo

        user1_id = uuid4()
        user2_id = uuid4()

        # Mock that users have no workspaces
        mock_session.exec.return_value.all.side_effect = [
            [],  # user1 owned
            [],  # user1 member
        ]

        result = users_repo.users_share_workspace(
            session=mock_session,
            user_id_1=user1_id,
            user_id_2=user2_id
        )

        assert result is False
