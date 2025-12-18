"""
Tests for Board Repository.
"""
import uuid

from sqlmodel import Session

from app.repository import boards as board_repo
from app.repository import workspaces as workspace_repo
from app.models.boards import BoardCreate, BoardUpdate
from app.models.workspaces import WorkspaceCreate
from app.models.enums import MemberRole
from tests.utils.utils import random_lower_string


def _create_test_workspace(db: Session, owner_id: uuid.UUID):
    """Helper to create a test workspace."""
    workspace_in = WorkspaceCreate(
        name=f"Test Workspace {random_lower_string()[:8]}",
        description="Test workspace for board tests"
    )
    return workspace_repo.create_workspace(
        session=db, workspace_in=workspace_in, owner_id=owner_id
    )


def test_create_board(db: Session, test_user) -> None:
    """Test creating a new board."""
    workspace = _create_test_workspace(db, test_user.id)
    
    board_in = BoardCreate(
        name=f"Test Board {random_lower_string()[:8]}",
        workspace_id=workspace.id
    )
    board = board_repo.create_board(
        session=db, board_in=board_in, owner_id=test_user.id
    )
    assert board.name == board_in.name
    assert board.workspace_id == workspace.id
    assert board.owner_id == test_user.id


def test_get_board_by_id(db: Session, test_user) -> None:
    """Test getting board by ID."""
    workspace = _create_test_workspace(db, test_user.id)
    
    board_in = BoardCreate(
        name=f"Test Board {random_lower_string()[:8]}",
        workspace_id=workspace.id
    )
    created = board_repo.create_board(
        session=db, board_in=board_in, owner_id=test_user.id
    )
    
    fetched = board_repo.get_board_by_id(session=db, board_id=created.id)
    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.name == created.name


def test_get_boards_for_user(db: Session, test_user) -> None:
    """Test getting boards for a user."""
    workspace = _create_test_workspace(db, test_user.id)
    
    board_in = BoardCreate(
        name=f"Test Board {random_lower_string()[:8]}",
        workspace_id=workspace.id
    )
    board_repo.create_board(
        session=db, board_in=board_in, owner_id=test_user.id
    )
    
    boards, count = board_repo.get_boards_for_user(
        session=db, user_id=test_user.id
    )
    assert len(boards) >= 1


def test_update_board(db: Session, test_user) -> None:
    """Test updating a board."""
    workspace = _create_test_workspace(db, test_user.id)
    
    board_in = BoardCreate(
        name=f"Test Board {random_lower_string()[:8]}",
        workspace_id=workspace.id
    )
    board = board_repo.create_board(
        session=db, board_in=board_in, owner_id=test_user.id
    )
    
    update_in = BoardUpdate(name="Updated Board Name")
    updated = board_repo.update_board(
        session=db, board=board, board_in=update_in
    )
    assert updated.name == "Updated Board Name"


def test_soft_delete_board(db: Session, test_user) -> None:
    """Test soft deleting a board."""
    workspace = _create_test_workspace(db, test_user.id)
    
    board_in = BoardCreate(
        name=f"Test Board {random_lower_string()[:8]}",
        workspace_id=workspace.id
    )
    board = board_repo.create_board(
        session=db, board_in=board_in, owner_id=test_user.id
    )
    
    deleted = board_repo.soft_delete_board(
        session=db, board=board, deleted_by=test_user.id
    )
    assert deleted.is_deleted is True
    assert deleted.deleted_at is not None
    assert deleted.deleted_by == str(test_user.id)


def test_can_access_board(db: Session, test_user) -> None:
    """Test board access check."""
    workspace = _create_test_workspace(db, test_user.id)
    
    board_in = BoardCreate(
        name=f"Test Board {random_lower_string()[:8]}",
        workspace_id=workspace.id
    )
    board = board_repo.create_board(
        session=db, board_in=board_in, owner_id=test_user.id
    )
    
    # Owner should have access
    can_access = board_repo.can_access_board(
        session=db, user_id=test_user.id, board=board
    )
    assert can_access is True
    
    # Random user should not have access
    random_uuid = uuid.uuid4()
    can_access_random = board_repo.can_access_board(
        session=db, user_id=random_uuid, board=board
    )
    assert can_access_random is False


def test_can_edit_board(db: Session, test_user) -> None:
    """Test board edit permission check."""
    workspace = _create_test_workspace(db, test_user.id)
    
    board_in = BoardCreate(
        name=f"Test Board {random_lower_string()[:8]}",
        workspace_id=workspace.id
    )
    board = board_repo.create_board(
        session=db, board_in=board_in, owner_id=test_user.id
    )
    
    # Owner should be able to edit
    can_edit = board_repo.can_edit_board(
        session=db, user_id=test_user.id, board=board
    )
    assert can_edit is True


def test_workspace_member_can_access_board(db: Session, test_user) -> None:
    """Test that workspace members can access boards."""
    from tests.utils.user import create_random_user
    
    workspace = _create_test_workspace(db, test_user.id)
    
    board_in = BoardCreate(
        name=f"Test Board {random_lower_string()[:8]}",
        workspace_id=workspace.id
    )
    board = board_repo.create_board(
        session=db, board_in=board_in, owner_id=test_user.id
    )
    
    # Add a member to workspace
    member_user = create_random_user(db)
    workspace_repo.add_workspace_member(
        session=db,
        user_id=member_user.id,
        workspace_id=workspace.id,
        role=MemberRole.member
    )
    
    # Member should have access
    can_access = board_repo.can_access_board(
        session=db, user_id=member_user.id, board=board
    )
    assert can_access is True
