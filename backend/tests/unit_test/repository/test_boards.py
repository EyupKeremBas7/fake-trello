"""
Unit tests for Boards Repository.
Tests all database operations for Board model.
"""
import pytest
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch
from uuid import uuid4

from app.models.enums import MemberRole


class TestBoardCRUD:
    """Tests for board CRUD operations."""

    def test_create_board_success(self, mock_session):
        """Test successful board creation."""
        from app.models.boards import BoardCreate
        from app.repository import boards as boards_repo

        board_in = BoardCreate(
            name="Test Board",
            workspace_id=uuid4()
        )
        owner_id = uuid4()

        result = boards_repo.create_board(
            session=mock_session,
            board_in=board_in,
            owner_id=owner_id
        )

        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()

    def test_update_board(self, mock_session, mock_board):
        """Test updating board."""
        from app.models.boards import BoardUpdate
        from app.repository import boards as boards_repo

        board_in = BoardUpdate(name="Updated Board")
        mock_board.sqlmodel_update = Mock()

        result = boards_repo.update_board(
            session=mock_session,
            board=mock_board,
            board_in=board_in
        )

        mock_board.sqlmodel_update.assert_called_once()
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    def test_soft_delete_board(self, mock_session, mock_board):
        """Test soft deleting board."""
        from app.repository import boards as boards_repo

        deleted_by = uuid4()
        mock_board.is_deleted = False

        result = boards_repo.soft_delete_board(
            session=mock_session,
            board=mock_board,
            deleted_by=deleted_by
        )

        assert mock_board.is_deleted is True
        assert mock_board.deleted_by == str(deleted_by)
        mock_session.commit.assert_called_once()


class TestBoardAccess:
    """Tests for board access permissions."""

    def test_can_access_board_owner(self, mock_session, mock_board, mock_workspace):
        """Test workspace owner can access board."""
        from app.repository import boards as boards_repo

        user_id = mock_workspace.owner_id
        mock_session.get.return_value = mock_workspace

        result = boards_repo.can_access_board(
            session=mock_session,
            user_id=user_id,
            board=mock_board
        )

        assert result is True

    def test_can_access_board_member(self, mock_session, mock_board, mock_workspace):
        """Test workspace member can access board."""
        from app.repository import boards as boards_repo

        user_id = uuid4()
        mock_workspace.owner_id = uuid4()  # Different owner
        mock_session.get.return_value = mock_workspace

        mock_member = Mock()
        mock_member.role = MemberRole.member
        mock_session.exec.return_value.first.return_value = mock_member

        result = boards_repo.can_access_board(
            session=mock_session,
            user_id=user_id,
            board=mock_board
        )

        assert result is True

    def test_can_access_board_denied(self, mock_session, mock_board, mock_workspace):
        """Test non-member cannot access board."""
        from app.repository import boards as boards_repo

        user_id = uuid4()
        mock_workspace.owner_id = uuid4()
        mock_session.get.return_value = mock_workspace
        mock_session.exec.return_value.first.return_value = None

        result = boards_repo.can_access_board(
            session=mock_session,
            user_id=user_id,
            board=mock_board
        )

        assert result is False

    def test_can_access_board_no_workspace(self, mock_session, mock_board):
        """Test access denied when workspace not found."""
        from app.repository import boards as boards_repo

        mock_session.get.return_value = None

        result = boards_repo.can_access_board(
            session=mock_session,
            user_id=uuid4(),
            board=mock_board
        )

        assert result is False

    def test_can_edit_board_owner(self, mock_session, mock_board, mock_workspace):
        """Test workspace owner can edit board."""
        from app.repository import boards as boards_repo

        user_id = mock_workspace.owner_id
        mock_session.get.return_value = mock_workspace

        result = boards_repo.can_edit_board(
            session=mock_session,
            user_id=user_id,
            board=mock_board
        )

        assert result is True

    def test_can_edit_board_admin(self, mock_session, mock_board, mock_workspace):
        """Test admin can edit board."""
        from app.repository import boards as boards_repo

        user_id = uuid4()
        mock_workspace.owner_id = uuid4()
        mock_session.get.return_value = mock_workspace

        mock_member = Mock()
        mock_member.role = MemberRole.admin
        mock_session.exec.return_value.first.return_value = mock_member

        result = boards_repo.can_edit_board(
            session=mock_session,
            user_id=user_id,
            board=mock_board
        )

        assert result is True

    def test_can_edit_board_member(self, mock_session, mock_board, mock_workspace):
        """Test regular member can edit board."""
        from app.repository import boards as boards_repo

        user_id = uuid4()
        mock_workspace.owner_id = uuid4()
        mock_session.get.return_value = mock_workspace

        mock_member = Mock()
        mock_member.role = MemberRole.member
        mock_session.exec.return_value.first.return_value = mock_member

        result = boards_repo.can_edit_board(
            session=mock_session,
            user_id=user_id,
            board=mock_board
        )

        assert result is True

    def test_can_edit_board_observer_denied(self, mock_session, mock_board, mock_workspace):
        """Test observer cannot edit board."""
        from app.repository import boards as boards_repo

        user_id = uuid4()
        mock_workspace.owner_id = uuid4()
        mock_session.get.return_value = mock_workspace

        mock_member = Mock()
        mock_member.role = MemberRole.observer
        mock_session.exec.return_value.first.return_value = mock_member

        result = boards_repo.can_edit_board(
            session=mock_session,
            user_id=user_id,
            board=mock_board
        )

        assert result is False


class TestGetBoards:
    """Tests for board retrieval functions."""

    def test_get_boards_for_user(self, mock_session, mock_board):
        """Test getting boards for user."""
        from app.repository import boards as boards_repo

        user_id = uuid4()
        mock_session.exec.return_value.all.return_value = [mock_board]

        boards, count = boards_repo.get_boards_for_user(
            session=mock_session,
            user_id=user_id
        )

        assert len(boards) == 1
        assert count == 1

    def test_get_boards_superuser(self, mock_session, mock_board):
        """Test getting all boards as superuser."""
        from app.repository import boards as boards_repo

        mock_session.exec.return_value.one.return_value = 1
        mock_session.exec.return_value.all.return_value = [mock_board]

        boards, count = boards_repo.get_boards_superuser(session=mock_session)

        assert len(boards) == 1
        assert count == 1
