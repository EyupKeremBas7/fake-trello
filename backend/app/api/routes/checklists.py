"""
Checklists API Routes - Clean routes without direct database queries.
"""
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, SessionDep
from app.repository import checklists as checklists_repo
from app.repository import notifications as notifications_repo
from app.models.checklists import (
    ChecklistItem,
    ChecklistItemCreate,
    ChecklistItemPublic,
    ChecklistItemsPublic,
    ChecklistItemUpdate,
)
from app.models.notifications import NotificationType
from app.utils import send_email

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
    items, count = checklists_repo.get_checklist_items_by_card(
        session=session, card_id=card_id, skip=skip, limit=limit
    )
    return ChecklistItemsPublic(data=items, count=count)


@router.get("/{id}", response_model=ChecklistItemPublic)
def read_checklist_item(
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
) -> ChecklistItem:
    """Get a specific checklist item by ID."""
    item = checklists_repo.get_checklist_item_by_id(session=session, item_id=id)
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
    card = checklists_repo.get_card_by_id(session=session, card_id=item_in.card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    item = checklists_repo.create_checklist_item(session=session, item_in=item_in)
    return item


@router.patch("/{id}", response_model=ChecklistItemPublic)
def update_checklist_item(
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    item_in: ChecklistItemUpdate,
) -> ChecklistItem:
    """Update a checklist item."""
    item = checklists_repo.get_checklist_item_by_id(session=session, item_id=id)
    if not item:
        raise HTTPException(status_code=404, detail="Checklist item not found")
    
    item = checklists_repo.update_checklist_item(session=session, item=item, item_in=item_in)
    return item


@router.delete("/{id}")
def delete_checklist_item(
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
) -> dict:
    """Delete a checklist item."""
    item = checklists_repo.get_checklist_item_by_id(session=session, item_id=id)
    if not item or item.is_deleted:
        raise HTTPException(status_code=404, detail="Checklist item not found")
    
    checklists_repo.soft_delete_checklist_item(session=session, item=item, deleted_by=current_user.id)
    return {"ok": True}


@router.post("/{id}/toggle", response_model=ChecklistItemPublic)
def toggle_checklist_item(
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
) -> ChecklistItem:
    """Toggle the completion status of a checklist item."""
    item = checklists_repo.get_checklist_item_by_id(session=session, item_id=id)
    if not item:
        raise HTTPException(status_code=404, detail="Checklist item not found")
    
    item = checklists_repo.toggle_checklist_item(session=session, item=item)
    
    # Dispatch ChecklistToggledEvent (Observer pattern)
    card = checklists_repo.get_card_by_id(session=session, card_id=item.card_id)
    if card:
        card_owner = None
        card_owner_email = None
        if card.created_by:
            owner = checklists_repo.get_user_by_id(session=session, user_id=card.created_by)
            if owner and not owner.is_deleted:
                card_owner = owner.id
                card_owner_email = owner.email
        
        from app.events import EventDispatcher, ChecklistToggledEvent
        EventDispatcher.dispatch(ChecklistToggledEvent(
            card_id=card.id,
            card_title=card.title,
            item_title=item.title,
            is_completed=item.is_completed,
            toggled_by_id=current_user.id,
            toggled_by_name=current_user.full_name or current_user.email,
            card_owner_id=card_owner,
            card_owner_email=card_owner_email,
        ))
    
    return item
