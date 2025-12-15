from fastapi import APIRouter, HTTPException
from sqlmodel import select
from datetime import datetime
import uuid

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    ChecklistItem,
    ChecklistItemCreate,
    ChecklistItemPublic,
    ChecklistItemsPublic,
    ChecklistItemUpdate,
    Card,
)

router = APIRouter(prefix="/checklists", tags=["checklists"])


@router.get("/", response_model=ChecklistItemsPublic)
def read_checklist_items(
    session: SessionDep,
    current_user: CurrentUser,
    card_id: uuid.UUID | None = None,
    skip: int = 0,
    limit: int = 100,
) -> ChecklistItemsPublic:
    """Get all checklist items, optionally filtered by card_id."""
    query = select(ChecklistItem).where(ChecklistItem.is_deleted == False)
    
    if card_id:
        query = query.where(ChecklistItem.card_id == card_id)
    
    query = query.order_by(ChecklistItem.position).offset(skip).limit(limit)
    items = session.exec(query).all()
    
    count_query = select(ChecklistItem).where(ChecklistItem.is_deleted == False)
    if card_id:
        count_query = count_query.where(ChecklistItem.card_id == card_id)
    count = len(session.exec(count_query).all())
    
    return ChecklistItemsPublic(data=items, count=count)


@router.get("/{id}", response_model=ChecklistItemPublic)
def read_checklist_item(
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
) -> ChecklistItem:
    """Get a specific checklist item by ID."""
    item = session.get(ChecklistItem, id)
    if not item:
        raise HTTPException(status_code=404, detail="Checklist item not found")
    return item


@router.post("/", response_model=ChecklistItemPublic)
def create_checklist_item(
    session: SessionDep,
    current_user: CurrentUser,
    item_in: ChecklistItemCreate,
) -> ChecklistItem:
    """Create a new checklist item."""
    # Verify card exists
    card = session.get(Card, item_in.card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    item = ChecklistItem.model_validate(item_in)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.patch("/{id}", response_model=ChecklistItemPublic)
def update_checklist_item(
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    item_in: ChecklistItemUpdate,
) -> ChecklistItem:
    """Update a checklist item."""
    item = session.get(ChecklistItem, id)
    if not item:
        raise HTTPException(status_code=404, detail="Checklist item not found")
    
    update_data = item_in.model_dump(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()
    item.sqlmodel_update(update_data)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.delete("/{id}")
def delete_checklist_item(
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
) -> dict:
    """Delete a checklist item."""
    item = session.get(ChecklistItem, id)
    if not item or item.is_deleted:
        raise HTTPException(status_code=404, detail="Checklist item not found")
    
    item.is_deleted = True
    item.deleted_at = datetime.utcnow()
    item.deleted_by = str(current_user.id)
    session.add(item)
    session.commit()
    return {"ok": True}


@router.post("/{id}/toggle", response_model=ChecklistItemPublic)
def toggle_checklist_item(
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
) -> ChecklistItem:
    """Toggle the completion status of a checklist item."""
    item = session.get(ChecklistItem, id)
    if not item:
        raise HTTPException(status_code=404, detail="Checklist item not found")
    
    item.is_completed = not item.is_completed
    item.updated_at = datetime.utcnow()
    session.add(item)
    session.commit()
    session.refresh(item)
    return item
