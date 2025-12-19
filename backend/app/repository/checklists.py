"""
Checklists Repository - All database operations for ChecklistItem model.
"""
import uuid
from datetime import datetime

from sqlmodel import Session, select

from app.models.cards import Card
from app.models.checklists import (
    ChecklistItem,
    ChecklistItemCreate,
    ChecklistItemUpdate,
)
from app.models.users import User


def get_checklist_item_by_id(*, session: Session, item_id: uuid.UUID) -> ChecklistItem | None:
    """Get checklist item by ID."""
    return session.get(ChecklistItem, item_id)


def get_card_by_id(*, session: Session, card_id: uuid.UUID) -> Card | None:
    """Get card by ID."""
    return session.get(Card, card_id)


def get_user_by_id(*, session: Session, user_id: uuid.UUID) -> User | None:
    """Get user by ID."""
    return session.get(User, user_id)


def get_checklist_items_by_card(
    *, session: Session, card_id: uuid.UUID | None = None, skip: int = 0, limit: int = 100
) -> tuple[list[ChecklistItem], int]:
    """Get checklist items, optionally filtered by card_id."""
    query = select(ChecklistItem).where(ChecklistItem.is_deleted == False)

    if card_id:
        query = query.where(ChecklistItem.card_id == card_id)

    query = query.order_by(ChecklistItem.position).offset(skip).limit(limit)
    items = session.exec(query).all()

    # Count query
    count_query = select(ChecklistItem).where(ChecklistItem.is_deleted == False)
    if card_id:
        count_query = count_query.where(ChecklistItem.card_id == card_id)
    count = len(session.exec(count_query).all())

    return list(items), count


def create_checklist_item(
    *, session: Session, item_in: ChecklistItemCreate
) -> ChecklistItem:
    """Create a new checklist item."""
    item = ChecklistItem.model_validate(item_in)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


def update_checklist_item(
    *, session: Session, item: ChecklistItem, item_in: ChecklistItemUpdate
) -> ChecklistItem:
    """Update a checklist item."""
    update_data = item_in.model_dump(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()
    item.sqlmodel_update(update_data)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


def toggle_checklist_item(*, session: Session, item: ChecklistItem) -> ChecklistItem:
    """Toggle the completion status of a checklist item."""
    item.is_completed = not item.is_completed
    item.updated_at = datetime.utcnow()
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


def soft_delete_checklist_item(
    *, session: Session, item: ChecklistItem, deleted_by: uuid.UUID
) -> ChecklistItem:
    """Soft delete a checklist item."""
    item.is_deleted = True
    item.deleted_at = datetime.utcnow()
    item.deleted_by = str(deleted_by)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item
