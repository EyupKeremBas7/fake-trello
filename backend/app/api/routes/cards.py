"""
Cards API Routes - Clean routes without direct database queries.
"""
import logging
import uuid
from typing import Any

logger = logging.getLogger(__name__)

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, SessionDep
from app.repository import cards as cards_repo
from app.repository import notifications as notifications_repo
from app.models.cards import Card, CardCreate, CardPublic, CardsPublic, CardUpdate
from app.models.notifications import NotificationType
from app.models.auth import Message
from app.utils import send_email
from app.core.permissions import has_permission, Action

router = APIRouter(prefix="/cards", tags=["cards"])

@router.get("/", response_model=CardsPublic)
def read_cards(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    if current_user.is_superuser:
        cards, count = cards_repo.get_cards_superuser(
            session=session, skip=skip, limit=limit
        )
    else:
        cards, count = cards_repo.get_cards_for_user(
            session=session, user_id=current_user.id, skip=skip, limit=limit
        )
    
    enriched_cards = [cards_repo.enrich_card_with_owner(session, card) for card in cards]

    return CardsPublic(data=enriched_cards, count=count)


@router.get("/{id}", response_model=CardPublic)
def read_card(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> Any:
    card = cards_repo.get_card_by_id(session=session, card_id=id)
    if not card or card.is_deleted:
        raise HTTPException(status_code=404, detail="Card not found")
    if not current_user.is_superuser and not cards_repo.can_access_card(
        session=session, user_id=current_user.id, card=card
    ):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return cards_repo.enrich_card_with_owner(session, card)


@router.post("/", response_model=CardPublic)
def create_card(
    *, session: SessionDep, current_user: CurrentUser, card_in: CardCreate
) -> Any:
    board_list = cards_repo.get_list_by_id(session=session, list_id=card_in.list_id)
    if not board_list:
        raise HTTPException(status_code=404, detail="List not found")
    
    board = cards_repo.get_board_by_id(session=session, board_id=board_list.board_id)
    workspace = cards_repo.get_workspace_by_id(session=session, workspace_id=board.workspace_id)
    
    if workspace.owner_id != current_user.id:
        role = cards_repo.get_user_role_in_workspace(
            session=session, user_id=current_user.id, workspace_id=workspace.id
        )
        if not has_permission(role, Action.CREATE_CARD):
            raise HTTPException(status_code=403, detail="Not enough permissions")
    
    card = cards_repo.create_card(
        session=session, card_in=card_in, created_by=current_user.id
    )
    return cards_repo.enrich_card_with_owner(session, card)


@router.put("/{id}", response_model=CardPublic)
def update_card(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    card_in: CardUpdate,
) -> Any:    
    card = cards_repo.get_card_by_id(session=session, card_id=id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    if not current_user.is_superuser and not cards_repo.can_edit_card(
        session=session, user_id=current_user.id, card=card
    ):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    old_list_id = card.list_id
    old_list = cards_repo.get_list_by_id(session=session, list_id=old_list_id)
    old_list_name = old_list.name if old_list else "Unknown"
    
    card = cards_repo.update_card(session=session, card=card, card_in=card_in)
    
    # Dispatch CardMovedEvent if list changed (Observer pattern)
    if card_in.list_id and card_in.list_id != old_list_id:
        new_list = cards_repo.get_list_by_id(session=session, list_id=card_in.list_id)
        new_list_name = new_list.name if new_list else "Unknown"
        
        logger.info(f"Card moved via PUT - from {old_list_name} to {new_list_name}")
        
        # Get card owner info for event
        card_owner = None
        card_owner_email = None
        if card.created_by:
            owner = cards_repo.get_user_by_id(session=session, user_id=card.created_by)
            if owner and not owner.is_deleted:
                card_owner = owner.id
                card_owner_email = owner.email
        
        from app.events import EventDispatcher, CardMovedEvent
        EventDispatcher.dispatch(CardMovedEvent(
            card_id=card.id,
            card_title=card.title,
            old_list_name=old_list_name,
            new_list_name=new_list_name,
            moved_by_id=current_user.id,
            moved_by_name=current_user.full_name or current_user.email,
            card_owner_id=card_owner,
            card_owner_email=card_owner_email,
        ))
    
    return cards_repo.enrich_card_with_owner(session, card)

@router.delete("/{id}")
def delete_card(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Message:
    card = cards_repo.get_card_by_id(session=session, card_id=id)
    if not card or card.is_deleted:
        raise HTTPException(status_code=404, detail="Card not found")
    if not current_user.is_superuser and not cards_repo.can_edit_card(
        session=session, user_id=current_user.id, card=card
    ):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    cards_repo.soft_delete_card(session=session, card=card, deleted_by=current_user.id)
    return Message(message="Card deleted successfully")