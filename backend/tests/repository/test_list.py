"""
Tests for List Repository.
"""
import uuid

from sqlmodel import Session

from app.repository import lists as list_repo
from app.repository import boards as board_repo
from app.repository import workspaces as workspace_repo
from app.models.lists import ListCreate, ListUpdate
from app.models.boards import BoardCreate
from app.models.workspaces import WorkspaceCreate
from tests.utils.utils import random_lower_string


def _create_test_board(db: Session, owner_id: uuid.UUID):
    """Helper to create a test workspace and board."""
    workspace_in = WorkspaceCreate(
        name=f"Test Workspace {random_lower_string()[:8]}",
        description="Test workspace for list tests"
    )
    workspace = workspace_repo.create_workspace(
        session=db, workspace_in=workspace_in, owner_id=owner_id
    )
    
    board_in = BoardCreate(
        name=f"Test Board {random_lower_string()[:8]}",
        description="Test board for list tests",
        workspace_id=workspace.id
    )
    return board_repo.create_board(
        session=db, board_in=board_in, owner_id=owner_id
    )


def test_create_list(db: Session, test_user) -> None:
    """Test creating a new list."""
    board = _create_test_board(db, test_user.id)
    
    list_in = ListCreate(
        name=f"Test List {random_lower_string()[:8]}",
        board_id=board.id
    )
    board_list = list_repo.create_list(session=db, list_in=list_in)
    assert board_list.name == list_in.name
    assert board_list.board_id == board.id


def test_get_list_by_id(db: Session, test_user) -> None:
    """Test getting list by ID."""
    board = _create_test_board(db, test_user.id)
    
    list_in = ListCreate(
        name=f"Test List {random_lower_string()[:8]}",
        board_id=board.id
    )
    created = list_repo.create_list(session=db, list_in=list_in)
    
    fetched = list_repo.get_list_by_id(session=db, list_id=created.id)
    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.name == created.name


def test_get_lists_by_board(db: Session, test_user) -> None:
    """Test getting lists for a specific board."""
    board = _create_test_board(db, test_user.id)
    
    # Create multiple lists
    for i in range(3):
        list_in = ListCreate(
            name=f"Test List {i} {random_lower_string()[:8]}",
            board_id=board.id
        )
        list_repo.create_list(session=db, list_in=list_in)
    
    lists = list_repo.get_lists_by_board(session=db, board_id=board.id)
    assert len(lists) >= 3


def test_update_list(db: Session, test_user) -> None:
    """Test updating a list."""
    board = _create_test_board(db, test_user.id)
    
    list_in = ListCreate(
        name=f"Original List {random_lower_string()[:8]}",
        board_id=board.id
    )
    board_list = list_repo.create_list(session=db, list_in=list_in)
    
    update_in = ListUpdate(name="Updated List Name")
    updated = list_repo.update_list(
        session=db, board_list=board_list, list_in=update_in
    )
    assert updated.name == "Updated List Name"


def test_soft_delete_list(db: Session, test_user) -> None:
    """Test soft deleting a list."""
    board = _create_test_board(db, test_user.id)
    
    list_in = ListCreate(
        name=f"Test List {random_lower_string()[:8]}",
        board_id=board.id
    )
    board_list = list_repo.create_list(session=db, list_in=list_in)
    
    deleted = list_repo.soft_delete_list(
        session=db, board_list=board_list, deleted_by=test_user.id
    )
    assert deleted.is_deleted is True
    assert deleted.deleted_at is not None
    assert deleted.deleted_by == str(test_user.id)


def test_get_next_position(db: Session, test_user) -> None:
    """Test automatic position calculation for new lists."""
    board = _create_test_board(db, test_user.id)
    
    # First list should get default position
    first_position = list_repo.get_next_position(session=db, board_id=board.id)
    assert first_position == 65536.0
    
    # Create a list
    list_in = ListCreate(
        name=f"Test List {random_lower_string()[:8]}",
        board_id=board.id
    )
    list_repo.create_list(session=db, list_in=list_in)
    
    # Second position should be higher
    second_position = list_repo.get_next_position(session=db, board_id=board.id)
    assert second_position > first_position


def test_lists_ordered_by_position(db: Session, test_user) -> None:
    """Test that lists are returned ordered by position."""
    board = _create_test_board(db, test_user.id)
    
    # Create lists with different positions
    for i in range(3):
        list_in = ListCreate(
            name=f"List {i}",
            board_id=board.id
        )
        list_repo.create_list(session=db, list_in=list_in)
    
    lists = list_repo.get_lists_by_board(session=db, board_id=board.id)
    
    # Verify they're ordered by position
    for i in range(len(lists) - 1):
        assert lists[i].position <= lists[i + 1].position
