"""
Tests for Checklist Repository.
"""
import uuid

from sqlmodel import Session

from app.repository import checklists as checklist_repo
from app.repository import cards as card_repo
from app.repository import lists as list_repo
from app.repository import boards as board_repo
from app.repository import workspaces as workspace_repo
from app.models.checklists import ChecklistItemCreate, ChecklistItemUpdate
from app.models.cards import CardCreate
from app.models.lists import ListCreate
from app.models.boards import BoardCreate
from app.models.workspaces import WorkspaceCreate
from tests.utils.utils import random_lower_string


def _create_test_card(db: Session, owner_id: uuid.UUID):
    """Helper to create a test card with full hierarchy."""
    workspace_in = WorkspaceCreate(
        name=f"Test Workspace {random_lower_string()[:8]}",
        description="Test workspace for checklist tests"
    )
    workspace = workspace_repo.create_workspace(
        session=db, workspace_in=workspace_in, owner_id=owner_id
    )
    
    board_in = BoardCreate(
        name=f"Test Board {random_lower_string()[:8]}",
        description="Test board for checklist tests",
        workspace_id=workspace.id
    )
    board = board_repo.create_board(
        session=db, board_in=board_in, owner_id=owner_id
    )
    
    list_in = ListCreate(
        name=f"Test List {random_lower_string()[:8]}",
        board_id=board.id
    )
    board_list = list_repo.create_list(session=db, list_in=list_in)
    
    card_in = CardCreate(
        title=f"Test Card {random_lower_string()[:8]}",
        description="Test card for checklist tests",
        list_id=board_list.id
    )
    return card_repo.create_card(session=db, card_in=card_in, created_by=owner_id)


def test_create_checklist_item(db: Session, test_user) -> None:
    """Test creating a new checklist item."""
    card = _create_test_card(db, test_user.id)
    
    item_in = ChecklistItemCreate(
        title=f"Checklist Item {random_lower_string()[:8]}",
        card_id=card.id,
        position=1.0
    )
    item = checklist_repo.create_checklist_item(session=db, item_in=item_in)
    assert item.title == item_in.title
    assert item.card_id == card.id
    assert item.is_completed is False


def test_get_checklist_item_by_id(db: Session, test_user) -> None:
    """Test getting checklist item by ID."""
    card = _create_test_card(db, test_user.id)
    
    item_in = ChecklistItemCreate(
        title=f"Checklist Item {random_lower_string()[:8]}",
        card_id=card.id,
        position=1.0
    )
    created = checklist_repo.create_checklist_item(session=db, item_in=item_in)
    
    fetched = checklist_repo.get_checklist_item_by_id(session=db, item_id=created.id)
    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.title == created.title


def test_get_checklist_items_by_card(db: Session, test_user) -> None:
    """Test getting checklist items for a card."""
    card = _create_test_card(db, test_user.id)
    
    # Create multiple items
    for i in range(3):
        item_in = ChecklistItemCreate(
            title=f"Item {i} {random_lower_string()[:8]}",
            card_id=card.id,
            position=float(i)
        )
        checklist_repo.create_checklist_item(session=db, item_in=item_in)
    
    items, count = checklist_repo.get_checklist_items_by_card(
        session=db, card_id=card.id
    )
    assert len(items) >= 3
    assert count >= 3


def test_update_checklist_item(db: Session, test_user) -> None:
    """Test updating a checklist item."""
    card = _create_test_card(db, test_user.id)
    
    item_in = ChecklistItemCreate(
        title=f"Original Title {random_lower_string()[:8]}",
        card_id=card.id,
        position=1.0
    )
    item = checklist_repo.create_checklist_item(session=db, item_in=item_in)
    
    update_in = ChecklistItemUpdate(title="Updated Title")
    updated = checklist_repo.update_checklist_item(
        session=db, item=item, item_in=update_in
    )
    assert updated.title == "Updated Title"
    assert updated.updated_at is not None


def test_toggle_checklist_item(db: Session, test_user) -> None:
    """Test toggling checklist item completion status."""
    card = _create_test_card(db, test_user.id)
    
    item_in = ChecklistItemCreate(
        title=f"Toggleable Item {random_lower_string()[:8]}",
        card_id=card.id,
        position=1.0
    )
    item = checklist_repo.create_checklist_item(session=db, item_in=item_in)
    assert item.is_completed is False
    
    # Toggle to completed
    toggled = checklist_repo.toggle_checklist_item(session=db, item=item)
    assert toggled.is_completed is True
    
    # Toggle back to incomplete
    toggled_again = checklist_repo.toggle_checklist_item(session=db, item=toggled)
    assert toggled_again.is_completed is False


def test_soft_delete_checklist_item(db: Session, test_user) -> None:
    """Test soft deleting a checklist item."""
    card = _create_test_card(db, test_user.id)
    
    item_in = ChecklistItemCreate(
        title=f"Delete Me {random_lower_string()[:8]}",
        card_id=card.id,
        position=1.0
    )
    item = checklist_repo.create_checklist_item(session=db, item_in=item_in)
    
    deleted = checklist_repo.soft_delete_checklist_item(
        session=db, item=item, deleted_by=test_user.id
    )
    assert deleted.is_deleted is True
    assert deleted.deleted_at is not None
    assert deleted.deleted_by == str(test_user.id)


def test_items_ordered_by_position(db: Session, test_user) -> None:
    """Test that checklist items are returned ordered by position."""
    card = _create_test_card(db, test_user.id)
    
    # Create items with specific positions
    positions = [3.0, 1.0, 2.0]
    for i, pos in enumerate(positions):
        item_in = ChecklistItemCreate(
            title=f"Item {i}",
            card_id=card.id,
            position=pos
        )
        checklist_repo.create_checklist_item(session=db, item_in=item_in)
    
    items, _ = checklist_repo.get_checklist_items_by_card(session=db, card_id=card.id)
    
    # Verify they're ordered by position
    for i in range(len(items) - 1):
        assert items[i].position <= items[i + 1].position
