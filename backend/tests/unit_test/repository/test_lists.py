"""
Unit tests for Lists Repository.
Tests all database operations for BoardList model.
"""
import pytest
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch
from uuid import uuid4


class TestListCRUD:
    """Tests for list CRUD operations."""

    def test_create_list_auto_position(self, mock_session):
        """Test creating list with auto position calculation."""
        from app.models.lists import ListCreate
        from app.repository import lists as lists_repo

        board_id = uuid4()
        list_in = ListCreate(
            name="Test List",
            board_id=board_id
        )

        # Mock no existing lists
        mock_session.exec.return_value.first.return_value = None

        result = lists_repo.create_list(
            session=mock_session,
            list_in=list_in,
            auto_position=True
        )

        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    def test_get_list_by_id(self, mock_session, mock_list):
        """Test getting list by ID."""
        from app.repository import lists as lists_repo

        mock_session.get.return_value = mock_list

        result = lists_repo.get_list_by_id(
            session=mock_session,
            list_id=mock_list.id
        )

        assert result == mock_list

    def test_update_list(self, mock_session, mock_list):
        """Test updating list."""
        from app.models.lists import ListUpdate
        from app.repository import lists as lists_repo

        list_in = ListUpdate(name="Updated List")
        mock_list.sqlmodel_update = Mock()

        result = lists_repo.update_list(
            session=mock_session,
            board_list=mock_list,
            list_in=list_in
        )

        mock_list.sqlmodel_update.assert_called_once()
        mock_session.commit.assert_called_once()

    def test_soft_delete_list(self, mock_session, mock_list):
        """Test soft deleting list."""
        from app.repository import lists as lists_repo

        deleted_by = uuid4()
        mock_list.is_deleted = False

        result = lists_repo.soft_delete_list(
            session=mock_session,
            board_list=mock_list,
            deleted_by=deleted_by
        )

        assert mock_list.is_deleted is True
        assert mock_list.deleted_by == str(deleted_by)


class TestGetNextPosition:
    """Tests for position calculation."""

    def test_get_next_position_empty_board(self, mock_session):
        """Test position for first list in empty board."""
        from app.repository import lists as lists_repo

        mock_session.exec.return_value.first.return_value = None

        result = lists_repo.get_next_position(
            session=mock_session,
            board_id=uuid4()
        )

        assert result == 65536.0

    def test_get_next_position_with_existing(self, mock_session, mock_list):
        """Test position calculation with existing lists."""
        from app.repository import lists as lists_repo

        mock_list.position = 65536.0
        mock_session.exec.return_value.first.return_value = mock_list

        result = lists_repo.get_next_position(
            session=mock_session,
            board_id=uuid4()
        )

        assert result == 65536.0 + 65536.0  # Next position


class TestGetLists:
    """Tests for list retrieval functions."""

    def test_get_lists_by_board(self, mock_session, mock_list):
        """Test getting lists for a board."""
        from app.repository import lists as lists_repo

        mock_session.exec.return_value.all.return_value = [mock_list]

        result = lists_repo.get_lists_by_board(
            session=mock_session,
            board_id=uuid4()
        )

        assert len(result) == 1

    def test_get_lists_for_user(self, mock_session, mock_list):
        """Test getting lists for user."""
        from app.repository import lists as lists_repo

        mock_session.exec.return_value.all.return_value = [mock_list]

        lists, count = lists_repo.get_lists_for_user(
            session=mock_session,
            user_id=uuid4()
        )

        assert len(lists) == 1

    def test_get_lists_superuser(self, mock_session, mock_list):
        """Test getting all lists as superuser."""
        from app.repository import lists as lists_repo

        mock_session.exec.return_value.one.return_value = 1
        mock_session.exec.return_value.all.return_value = [mock_list]

        lists, count = lists_repo.get_lists_superuser(session=mock_session)

        assert len(lists) == 1


class TestListAccess:
    """Tests for list access permissions."""

    def test_can_access_list_board_owner(self, mock_session, mock_board, mock_workspace):
        """Test workspace owner can access list."""
        from app.repository import lists as lists_repo

        user_id = mock_workspace.owner_id
        mock_session.get.return_value = mock_workspace

        result = lists_repo.can_access_list_board(
            session=mock_session,
            user_id=user_id,
            board=mock_board
        )

        assert result is True

    def test_can_access_list_board_denied(self, mock_session, mock_board, mock_workspace):
        """Test non-member cannot access list."""
        from app.repository import lists as lists_repo

        user_id = uuid4()
        mock_workspace.owner_id = uuid4()
        mock_session.get.return_value = mock_workspace
        mock_session.exec.return_value.first.return_value = None

        result = lists_repo.can_access_list_board(
            session=mock_session,
            user_id=user_id,
            board=mock_board
        )

        assert result is False
