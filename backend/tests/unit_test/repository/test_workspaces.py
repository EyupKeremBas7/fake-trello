"""
Unit tests for Workspaces Repository.
Tests all database operations for Workspace and WorkspaceMember models.
"""
import pytest
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch
from uuid import uuid4

from app.models.enums import MemberRole


class TestWorkspaceCRUD:
    """Tests for workspace CRUD operations."""

    def test_create_workspace_success(self, mock_session):
        """Test successful workspace creation."""
        from app.models.workspaces import WorkspaceCreate
        from app.repository import workspaces as ws_repo

        workspace_in = WorkspaceCreate(
            name="Test Workspace",
            description="Test Description"
        )
        owner_id = uuid4()

        result = ws_repo.create_workspace(
            session=mock_session,
            workspace_in=workspace_in,
            owner_id=owner_id
        )

        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()

    def test_get_workspace_by_id(self, mock_session, mock_workspace):
        """Test getting workspace by ID."""
        from app.repository import workspaces as ws_repo

        mock_session.get.return_value = mock_workspace

        result = ws_repo.get_workspace_by_id(
            session=mock_session,
            workspace_id=mock_workspace.id
        )

        assert result == mock_workspace
        mock_session.get.assert_called_once()

    def test_get_workspace_by_id_not_found(self, mock_session):
        """Test workspace not found returns None."""
        from app.repository import workspaces as ws_repo

        mock_session.get.return_value = None

        result = ws_repo.get_workspace_by_id(
            session=mock_session,
            workspace_id=uuid4()
        )

        assert result is None

    def test_update_workspace(self, mock_session, mock_workspace):
        """Test updating workspace."""
        from app.models.workspaces import WorkspaceUpdate
        from app.repository import workspaces as ws_repo

        workspace_in = WorkspaceUpdate(name="Updated Name")
        mock_workspace.sqlmodel_update = Mock()

        result = ws_repo.update_workspace(
            session=mock_session,
            workspace=mock_workspace,
            workspace_in=workspace_in
        )

        mock_workspace.sqlmodel_update.assert_called_once()
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    def test_soft_delete_workspace(self, mock_session, mock_workspace):
        """Test soft deleting workspace."""
        from app.repository import workspaces as ws_repo

        deleted_by = uuid4()
        mock_workspace.is_deleted = False

        result = ws_repo.soft_delete_workspace(
            session=mock_session,
            workspace=mock_workspace,
            deleted_by=deleted_by
        )

        assert mock_workspace.is_deleted is True
        assert mock_workspace.deleted_by == str(deleted_by)
        mock_session.commit.assert_called_once()


class TestWorkspaceAccess:
    """Tests for workspace access permissions."""

    def test_get_user_role_in_workspace_member(self, mock_session):
        """Test getting user role when user is a member."""
        from app.repository import workspaces as ws_repo

        user_id = uuid4()
        workspace_id = uuid4()

        mock_member = Mock()
        mock_member.role = MemberRole.member
        mock_session.exec.return_value.first.return_value = mock_member

        result = ws_repo.get_user_role_in_workspace(
            session=mock_session,
            user_id=user_id,
            workspace_id=workspace_id
        )

        assert result == MemberRole.member

    def test_get_user_role_in_workspace_not_member(self, mock_session):
        """Test getting user role when user is not a member."""
        from app.repository import workspaces as ws_repo

        mock_session.exec.return_value.first.return_value = None

        result = ws_repo.get_user_role_in_workspace(
            session=mock_session,
            user_id=uuid4(),
            workspace_id=uuid4()
        )

        assert result is None

    def test_can_access_workspace_owner(self, mock_session, mock_workspace):
        """Test workspace owner can access."""
        from app.repository import workspaces as ws_repo

        user_id = mock_workspace.owner_id

        result = ws_repo.can_access_workspace(
            session=mock_session,
            user_id=user_id,
            workspace=mock_workspace
        )

        assert result is True

    def test_can_access_workspace_member(self, mock_session, mock_workspace):
        """Test workspace member can access."""
        from app.repository import workspaces as ws_repo

        user_id = uuid4()
        mock_member = Mock()
        mock_member.role = MemberRole.member
        mock_session.exec.return_value.first.return_value = mock_member

        result = ws_repo.can_access_workspace(
            session=mock_session,
            user_id=user_id,
            workspace=mock_workspace
        )

        assert result is True

    def test_can_access_workspace_denied(self, mock_session, mock_workspace):
        """Test non-member cannot access."""
        from app.repository import workspaces as ws_repo

        user_id = uuid4()
        mock_session.exec.return_value.first.return_value = None

        result = ws_repo.can_access_workspace(
            session=mock_session,
            user_id=user_id,
            workspace=mock_workspace
        )

        assert result is False

    def test_can_edit_workspace_owner(self, mock_session, mock_workspace):
        """Test workspace owner can edit."""
        from app.repository import workspaces as ws_repo

        result = ws_repo.can_edit_workspace(
            session=mock_session,
            user_id=mock_workspace.owner_id,
            workspace=mock_workspace
        )

        assert result is True

    def test_can_edit_workspace_admin(self, mock_session, mock_workspace):
        """Test workspace admin can edit."""
        from app.repository import workspaces as ws_repo

        user_id = uuid4()
        mock_member = Mock()
        mock_member.role = MemberRole.admin
        mock_session.exec.return_value.first.return_value = mock_member

        result = ws_repo.can_edit_workspace(
            session=mock_session,
            user_id=user_id,
            workspace=mock_workspace
        )

        assert result is True

    def test_can_edit_workspace_member_denied(self, mock_session, mock_workspace):
        """Test regular member cannot edit workspace."""
        from app.repository import workspaces as ws_repo

        user_id = uuid4()
        mock_member = Mock()
        mock_member.role = MemberRole.member
        mock_session.exec.return_value.first.return_value = mock_member

        result = ws_repo.can_edit_workspace(
            session=mock_session,
            user_id=user_id,
            workspace=mock_workspace
        )

        assert result is False


class TestWorkspaceMemberCRUD:
    """Tests for workspace member operations."""

    def test_add_workspace_member(self, mock_session):
        """Test adding member to workspace."""
        from app.repository import workspaces as ws_repo

        user_id = uuid4()
        workspace_id = uuid4()

        result = ws_repo.add_workspace_member(
            session=mock_session,
            user_id=user_id,
            workspace_id=workspace_id,
            role=MemberRole.member
        )

        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    def test_get_workspace_members(self, mock_session):
        """Test getting all workspace members."""
        from app.repository import workspaces as ws_repo

        workspace_id = uuid4()
        mock_members = [Mock(), Mock()]
        mock_session.exec.return_value.all.return_value = mock_members

        result = ws_repo.get_workspace_members(
            session=mock_session,
            workspace_id=workspace_id
        )

        assert len(result) == 2

    def test_remove_workspace_member(self, mock_session):
        """Test removing member from workspace."""
        from app.repository import workspaces as ws_repo

        mock_member = Mock()

        ws_repo.remove_workspace_member(
            session=mock_session,
            member=mock_member
        )

        mock_session.delete.assert_called_once_with(mock_member)
        mock_session.commit.assert_called_once()

    def test_get_member_by_user_and_workspace(self, mock_session):
        """Test getting member by user and workspace IDs."""
        from app.repository import workspaces as ws_repo

        mock_member = Mock()
        mock_session.exec.return_value.first.return_value = mock_member

        result = ws_repo.get_member_by_user_and_workspace(
            session=mock_session,
            user_id=uuid4(),
            workspace_id=uuid4()
        )

        assert result == mock_member
