"""
Cards API Routes - Clean routes without direct database queries.
"""
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, SessionDep
from app.repository import cards as cards_repo
from app.models.cards import Card, CardCreate, CardPublic, CardsPublic, CardUpdate
from app.models.notifications import Notification, NotificationType
from app.models.enums import MemberRole
from app.models.auth import Message
from app.utils import send_email

router = APIRouter(prefix="/cards", tags=["cards"])


def enrich_card_with_owner(session, card: Card) -> CardPublic:
    """Add owner info to card."""
    owner = None
    if card.created_by:
        owner = cards_repo.get_user_by_id(session=session, user_id=card.created_by)
    
    return CardPublic(
        id=card.id,
        title=card.title,
        description=card.description,
        position=card.position,
        due_date=card.due_date,
        is_archived=card.is_archived,
        cover_image=card.cover_image,
        list_id=card.list_id,
        created_by=card.created_by,
        created_at=card.created_at,
        updated_at=card.updated_at,
        is_deleted=card.is_deleted,
        owner_full_name=owner.full_name if owner else None,
        owner_email=owner.email if owner else None,
    )


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
    
    # Enrich cards with owner info
    enriched_cards = [enrich_card_with_owner(session, card) for card in cards]

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
    return enrich_card_with_owner(session, card)


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
        if role not in [MemberRole.admin, MemberRole.member]:
            raise HTTPException(status_code=403, detail="Not enough permissions")
    
    card = cards_repo.create_card(
        session=session, card_in=card_in, created_by=current_user.id
    )
    return enrich_card_with_owner(session, card)


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
    
    card = cards_repo.update_card(session=session, card=card, card_in=card_in)
    return enrich_card_with_owner(session, card)


@router.patch("/{id}/move", response_model=CardPublic)
def move_card(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    list_id: uuid.UUID,
    position: float
) -> Any:
    card = cards_repo.get_card_by_id(session=session, card_id=id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    if not current_user.is_superuser and not cards_repo.can_edit_card(
        session=session, user_id=current_user.id, card=card
    ):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    new_list = cards_repo.get_list_by_id(session=session, list_id=list_id)
    if not new_list:
        raise HTTPException(status_code=404, detail="Target list not found")
    
    old_list = cards_repo.get_list_by_id(session=session, list_id=card.list_id)
    old_list_name = old_list.name if old_list else "Unknown"
    new_list_name = new_list.name
    
    # Move the card
    card = cards_repo.move_card(session=session, card=card, list_id=list_id, position=position)
    
    # Notify card owner if someone else moves the card
    if card.created_by and card.created_by != current_user.id:
        card_owner = cards_repo.get_user_by_id(session=session, user_id=card.created_by)
        if card_owner and not card_owner.is_deleted:
            # Create in-app notification
            notification = Notification(
                user_id=card_owner.id,
                type=NotificationType.card_moved,
                title="Card Moved",
                message=f"{current_user.full_name or current_user.email} moved your card '{card.title}' from '{old_list_name}' to '{new_list_name}'",
                reference_id=card.id,
                reference_type="card",
            )
            session.add(notification)
            session.commit()
            
            # Send email notification
            send_email(
                email_to=card_owner.email,
                subject=f"Card '{card.title}' was moved",
                html_content=f"""
                <h2>Card Moved</h2>
                <p><strong>{current_user.full_name or current_user.email}</strong> moved your card <strong>"{card.title}"</strong>:</p>
                <p>From: <strong>{old_list_name}</strong> → To: <strong>{new_list_name}</strong></p>
                <p><a href="#">View Card</a></p>
                """,
                use_queue=True,
            )
    
    return enrich_card_with_owner(session, card)


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