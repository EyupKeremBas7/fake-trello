"""
Tests for Workspace Repository.
"""
import uuid

from sqlmodel import Session

from app.repository import workspaces as workspace_repo
from app.models.workspaces import WorkspaceCreate, WorkspaceUpdate
from app.models.enums import MemberRole
from tests.utils.utils import random_lower_string


def test_create_workspace(db: Session, test_user) -> None:
    """Test creating a new workspace."""
    workspace_in = WorkspaceCreate(
        name=f"Test Workspace {random_lower_string()[:8]}",
        description="A test workspace"
    )
    workspace = workspace_repo.create_workspace(
        session=db, workspace_in=workspace_in, owner_id=test_user.id
    )
    assert workspace.name == workspace_in.name
    assert workspace.description == workspace_in.description
    assert workspace.owner_id == test_user.id


def test_get_workspace_by_id(db: Session, test_user) -> None:
    """Test getting workspace by ID."""
    workspace_in = WorkspaceCreate(
        name=f"Test Workspace {random_lower_string()[:8]}",
        description="A test workspace"
    )
    created = workspace_repo.create_workspace(
        session=db, workspace_in=workspace_in, owner_id=test_user.id
    )
    
    fetched = workspace_repo.get_workspace_by_id(session=db, workspace_id=created.id)
    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.name == created.name


def test_get_workspaces_for_user(db: Session, test_user) -> None:
    """Test getting workspaces for a user."""
    # Create a workspace
    workspace_in = WorkspaceCreate(
        name=f"Test Workspace {random_lower_string()[:8]}",
        description="A test workspace"
    )
    workspace_repo.create_workspace(
        session=db, workspace_in=workspace_in, owner_id=test_user.id
    )
    
    workspaces, count = workspace_repo.get_workspaces_for_user(
        session=db, user_id=test_user.id
    )
    assert len(workspaces) >= 1
    assert count >= 1


def test_update_workspace(db: Session, test_user) -> None:
    """Test updating a workspace."""
    workspace_in = WorkspaceCreate(
        name=f"Test Workspace {random_lower_string()[:8]}",
        description="Original description"
    )
    workspace = workspace_repo.create_workspace(
        session=db, workspace_in=workspace_in, owner_id=test_user.id
    )
    
    update_in = WorkspaceUpdate(description="Updated description")
    updated = workspace_repo.update_workspace(
        session=db, workspace=workspace, workspace_in=update_in
    )
    assert updated.description == "Updated description"


def test_soft_delete_workspace(db: Session, test_user) -> None:
    """Test soft deleting a workspace."""
    workspace_in = WorkspaceCreate(
        name=f"Test Workspace {random_lower_string()[:8]}",
        description="To be deleted"
    )
    workspace = workspace_repo.create_workspace(
        session=db, workspace_in=workspace_in, owner_id=test_user.id
    )
    
    deleted = workspace_repo.soft_delete_workspace(
        session=db, workspace=workspace, deleted_by=test_user.id
    )
    assert deleted.is_deleted is True
    assert deleted.deleted_at is not None
    assert deleted.deleted_by == str(test_user.id)


def test_add_workspace_member(db: Session, test_user) -> None:
    """Test adding a member to workspace."""
    from tests.utils.user import create_random_user
    
    workspace_in = WorkspaceCreate(
        name=f"Test Workspace {random_lower_string()[:8]}",
        description="Test workspace with members"
    )
    workspace = workspace_repo.create_workspace(
        session=db, workspace_in=workspace_in, owner_id=test_user.id
    )
    
    new_member = create_random_user(db)
    member = workspace_repo.add_workspace_member(
        session=db,
        user_id=new_member.id,
        workspace_id=workspace.id,
        role=MemberRole.member
    )
    assert member.user_id == new_member.id
    assert member.workspace_id == workspace.id
    assert member.role == MemberRole.member


def test_remove_workspace_member(db: Session, test_user) -> None:
    """Test removing a member from workspace."""
    from tests.utils.user import create_random_user
    
    workspace_in = WorkspaceCreate(
        name=f"Test Workspace {random_lower_string()[:8]}",
        description="Test workspace"
    )
    workspace = workspace_repo.create_workspace(
        session=db, workspace_in=workspace_in, owner_id=test_user.id
    )
    
    new_member = create_random_user(db)
    member = workspace_repo.add_workspace_member(
        session=db,
        user_id=new_member.id,
        workspace_id=workspace.id,
        role=MemberRole.observer
    )
    
    workspace_repo.remove_workspace_member(session=db, member=member)
    
    # Verify member is removed
    found = workspace_repo.get_member_by_user_and_workspace(
        session=db, user_id=new_member.id, workspace_id=workspace.id
    )
    assert found is None


def test_can_access_workspace(db: Session, test_user) -> None:
    """Test workspace access check."""
    workspace_in = WorkspaceCreate(
        name=f"Test Workspace {random_lower_string()[:8]}",
        description="Test workspace"
    )
    workspace = workspace_repo.create_workspace(
        session=db, workspace_in=workspace_in, owner_id=test_user.id
    )
    
    # Owner should have access
    can_access = workspace_repo.can_access_workspace(
        session=db, user_id=test_user.id, workspace=workspace
    )
    assert can_access is True
    
    # Random user should not have access
    random_uuid = uuid.uuid4()
    can_access_random = workspace_repo.can_access_workspace(
        session=db, user_id=random_uuid, workspace=workspace
    )
    assert can_access_random is False


def test_get_user_role_in_workspace(db: Session, test_user) -> None:
    """Test getting user role in workspace."""
    from tests.utils.user import create_random_user
    
    workspace_in = WorkspaceCreate(
        name=f"Test Workspace {random_lower_string()[:8]}",
        description="Test workspace"
    )
    workspace = workspace_repo.create_workspace(
        session=db, workspace_in=workspace_in, owner_id=test_user.id
    )
    
    member_user = create_random_user(db)
    workspace_repo.add_workspace_member(
        session=db,
        user_id=member_user.id,
        workspace_id=workspace.id,
        role=MemberRole.admin
    )
    
    role = workspace_repo.get_user_role_in_workspace(
        session=db, user_id=member_user.id, workspace_id=workspace.id
    )
    assert role == MemberRole.admin
