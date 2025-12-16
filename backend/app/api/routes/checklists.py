"""
Checklists API Routes - Clean routes without direct database queries.
"""
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, SessionDep
from app.repository import checklists as checklists_repo
from app.models.checklists import (
    ChecklistItem,
    ChecklistItemCreate,
    ChecklistItemPublic,
    ChecklistItemsPublic,
    ChecklistItemUpdate,
)
from app.models.notifications import Notification, NotificationType
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
    # Verify card exists
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
    
    # Toggle the item
    item = checklists_repo.toggle_checklist_item(session=session, item=item)
    
    # Get the card and notify owner if someone else toggles the checklist
    card = checklists_repo.get_card_by_id(session=session, card_id=item.card_id)
    if card and card.created_by and card.created_by != current_user.id:
        card_owner = checklists_repo.get_user_by_id(session=session, user_id=card.created_by)
        if card_owner and not card_owner.is_deleted:
            status = "completed" if item.is_completed else "uncompleted"
            
            # Create in-app notification
            notification = Notification(
                user_id=card_owner.id,
                type=NotificationType.checklist_toggled,
                title="Checklist Item Updated",
                message=f"{current_user.full_name or current_user.email} marked '{item.title}' as {status} on your card '{card.title}'",
                reference_id=card.id,
                reference_type="card",
            )
            session.add(notification)
            session.commit()
            
            # Send email notification
            status_emoji = "✅" if item.is_completed else "⬜"
            send_email(
                email_to=card_owner.email,
                subject=f"Checklist item updated on '{card.title}'",
                html_content=f"""
                <h2>Checklist Item Updated</h2>
                <p><strong>{current_user.full_name or current_user.email}</strong> updated a checklist item on your card <strong>"{card.title}"</strong>:</p>
                <p>{status_emoji} <strong>{item.title}</strong> - marked as {status}</p>
                <p><a href="#">View Card</a></p>
                """,
                use_queue=True,
            )
    
    return item
