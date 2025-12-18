"""
Tests for Card Repository.
"""
import uuid

from sqlmodel import Session

from app.repository import cards as card_repo
from app.repository import lists as list_repo
from app.repository import boards as board_repo
from app.repository import workspaces as workspace_repo
from app.models.cards import CardCreate, CardUpdate
from app.models.lists import ListCreate
from app.models.boards import BoardCreate
from app.models.workspaces import WorkspaceCreate
from tests.utils.utils import random_lower_string


def _create_test_list(db: Session, owner_id: uuid.UUID):
    """Helper to create a test workspace, board, and list."""
    workspace_in = WorkspaceCreate(
        name=f"Test Workspace {random_lower_string()[:8]}",
        description="Test workspace for card tests"
    )
    workspace = workspace_repo.create_workspace(
        session=db, workspace_in=workspace_in, owner_id=owner_id
    )
    
    board_in = BoardCreate(
        name=f"Test Board {random_lower_string()[:8]}",
        description="Test board for card tests",
        workspace_id=workspace.id
    )
    board = board_repo.create_board(
        session=db, board_in=board_in, owner_id=owner_id
    )
    
    list_in = ListCreate(
        name=f"Test List {random_lower_string()[:8]}",
        board_id=board.id
    )
    return list_repo.create_list(session=db, list_in=list_in)


def test_create_card(db: Session, test_user) -> None:
    """Test creating a new card."""
    board_list = _create_test_list(db, test_user.id)
    
    card_in = CardCreate(
        title=f"Test Card {random_lower_string()[:8]}",
        description="A test card",
        list_id=board_list.id
    )
    card = card_repo.create_card(
        session=db, card_in=card_in, created_by=test_user.id
    )
    assert card.title == card_in.title
    assert card.description == card_in.description
    assert card.list_id == board_list.id
    assert card.created_by == test_user.id


def test_get_card_by_id(db: Session, test_user) -> None:
    """Test getting card by ID."""
    board_list = _create_test_list(db, test_user.id)
    
    card_in = CardCreate(
        title=f"Test Card {random_lower_string()[:8]}",
        description="A test card",
        list_id=board_list.id
    )
    created = card_repo.create_card(
        session=db, card_in=card_in, created_by=test_user.id
    )
    
    fetched = card_repo.get_card_by_id(session=db, card_id=created.id)
    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.title == created.title


def test_update_card(db: Session, test_user) -> None:
    """Test updating a card."""
    board_list = _create_test_list(db, test_user.id)
    
    card_in = CardCreate(
        title=f"Original Title {random_lower_string()[:8]}",
        description="Original description",
        list_id=board_list.id
    )
    card = card_repo.create_card(
        session=db, card_in=card_in, created_by=test_user.id
    )
    
    update_in = CardUpdate(
        title="Updated Title",
        description="Updated description"
    )
    updated = card_repo.update_card(session=db, card=card, card_in=update_in)
    assert updated.title == "Updated Title"
    assert updated.description == "Updated description"


def test_move_card(db: Session, test_user) -> None:
    """Test moving a card to a different list."""
    board_list1 = _create_test_list(db, test_user.id)
    
    # Create a second list in the same board
    list_in = ListCreate(
        name=f"Second List {random_lower_string()[:8]}",
        board_id=board_list1.board_id
    )
    board_list2 = list_repo.create_list(session=db, list_in=list_in)
    
    # Create a card in the first list
    card_in = CardCreate(
        title=f"Movable Card {random_lower_string()[:8]}",
        description="Card to move",
        list_id=board_list1.id
    )
    card = card_repo.create_card(
        session=db, card_in=card_in, created_by=test_user.id
    )
    
    # Move the card to the second list
    new_position = 100.0
    moved = card_repo.move_card(
        session=db, card=card, list_id=board_list2.id, position=new_position
    )
    assert moved.list_id == board_list2.id
    assert moved.position == new_position


def test_soft_delete_card(db: Session, test_user) -> None:
    """Test soft deleting a card."""
    board_list = _create_test_list(db, test_user.id)
    
    card_in = CardCreate(
        title=f"Test Card {random_lower_string()[:8]}",
        description="To be deleted",
        list_id=board_list.id
    )
    card = card_repo.create_card(
        session=db, card_in=card_in, created_by=test_user.id
    )
    
    deleted = card_repo.soft_delete_card(
        session=db, card=card, deleted_by=test_user.id
    )
    assert deleted.is_deleted is True
    assert deleted.deleted_at is not None
    assert deleted.deleted_by == str(test_user.id)


def test_can_access_card(db: Session, test_user) -> None:
    """Test card access check."""
    board_list = _create_test_list(db, test_user.id)
    
    card_in = CardCreate(
        title=f"Test Card {random_lower_string()[:8]}",
        description="Test card for access",
        list_id=board_list.id
    )
    card = card_repo.create_card(
        session=db, card_in=card_in, created_by=test_user.id
    )
    
    # Owner should have access
    can_access = card_repo.can_access_card(
        session=db, user_id=test_user.id, card=card
    )
    assert can_access is True
    
    # Random user should not have access
    random_uuid = uuid.uuid4()
    can_access_random = card_repo.can_access_card(
        session=db, user_id=random_uuid, card=card
    )
    assert can_access_random is False


def test_can_edit_card(db: Session, test_user) -> None:
    """Test card edit permission check."""
    board_list = _create_test_list(db, test_user.id)
    
    card_in = CardCreate(
        title=f"Test Card {random_lower_string()[:8]}",
        description="Test card for edit",
        list_id=board_list.id
    )
    card = card_repo.create_card(
        session=db, card_in=card_in, created_by=test_user.id
    )
    
    # Owner should be able to edit
    can_edit = card_repo.can_edit_card(
        session=db, user_id=test_user.id, card=card
    )
    assert can_edit is True
