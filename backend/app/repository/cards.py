"""
Cards Repository - All database operations for Card model.
"""
import uuid
from datetime import datetime

from sqlmodel import Session, func, or_, select

from app.models.boards import Board
from app.models.cards import Card, CardCreate, CardPublic, CardUpdate
from app.models.enums import MemberRole
from app.models.lists import BoardList
from app.models.users import User
from app.models.workspace_members import WorkspaceMember
from app.models.workspaces import Workspace
from app.repository.common import get_user_role_in_workspace as _get_role


def enrich_card_with_owner(session: Session, card: Card) -> CardPublic:
    """Add owner info to card."""
    owner = None
    if card.created_by:
        owner = session.get(User, card.created_by)

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


def get_user_role_in_workspace(
    *, session: Session, user_id: uuid.UUID, workspace_id: uuid.UUID
) -> MemberRole | None:
    """Get user's role in a workspace."""
    member = session.exec(
        select(WorkspaceMember).where(
            WorkspaceMember.user_id == user_id,
            WorkspaceMember.workspace_id == workspace_id
        )
    ).first()
    return member.role if member else None


def can_access_card(*, session: Session, user_id: uuid.UUID, card: Card) -> bool:
    """Check if user can access the card."""
    board_list = session.get(BoardList, card.list_id)
    if not board_list:
        return False
    board = session.get(Board, board_list.board_id)
    if not board:
        return False
    workspace = session.get(Workspace, board.workspace_id)
    if not workspace:
        return False
    if workspace.owner_id == user_id:
        return True
    role = get_user_role_in_workspace(session=session, user_id=user_id, workspace_id=workspace.id)
    return role is not None


def can_edit_card(*, session: Session, user_id: uuid.UUID, card: Card) -> bool:
    """Check if user can edit the card."""
    board_list = session.get(BoardList, card.list_id)
    if not board_list:
        return False
    board = session.get(Board, board_list.board_id)
    if not board:
        return False
    workspace = session.get(Workspace, board.workspace_id)
    if not workspace:
        return False
    if workspace.owner_id == user_id:
        return True
    role = get_user_role_in_workspace(session=session, user_id=user_id, workspace_id=workspace.id)
    return role in [MemberRole.admin, MemberRole.member]


# ==================== Card CRUD ====================

def get_card_by_id(*, session: Session, card_id: uuid.UUID) -> Card | None:
    """Get card by ID."""
    return session.get(Card, card_id)


def get_list_by_id(*, session: Session, list_id: uuid.UUID) -> BoardList | None:
    """Get list by ID."""
    return session.get(BoardList, list_id)


def get_board_by_id(*, session: Session, board_id: uuid.UUID) -> Board | None:
    """Get board by ID."""
    return session.get(Board, board_id)


def get_workspace_by_id(*, session: Session, workspace_id: uuid.UUID) -> Workspace | None:
    """Get workspace by ID."""
    return session.get(Workspace, workspace_id)


def get_user_by_id(*, session: Session, user_id: uuid.UUID) -> User | None:
    """Get user by ID."""
    return session.get(User, user_id)


def get_cards_for_user(
    *, session: Session, user_id: uuid.UUID, skip: int = 0, limit: int = 100
) -> tuple[list[Card], int]:
    """Get cards that user can access."""
    statement = (
        select(Card)
        .join(BoardList, Card.list_id == BoardList.id)
        .join(Board, BoardList.board_id == Board.id)
        .join(Workspace, Board.workspace_id == Workspace.id)
        .outerjoin(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
        .where(
            Card.is_deleted == False,
            or_(
                Workspace.owner_id == user_id,
                WorkspaceMember.user_id == user_id
            )
        )
        .distinct()
        .offset(skip)
        .limit(limit)
    )
    cards = session.exec(statement).all()
    count = len(cards)

    return list(cards), count


def get_cards_superuser(
    *, session: Session, skip: int = 0, limit: int = 100
) -> tuple[list[Card], int]:
    """Get all cards (superuser)."""
    count_statement = select(func.count()).select_from(Card).where(Card.is_deleted == False)
    count = session.exec(count_statement).one()

    statement = select(Card).where(Card.is_deleted == False).offset(skip).limit(limit)
    cards = session.exec(statement).all()

    return list(cards), count


def create_card(
    *, session: Session, card_in: CardCreate, created_by: uuid.UUID
) -> Card:
    """Create a new card."""
    card = Card.model_validate(card_in, update={"created_by": created_by})
    session.add(card)
    session.commit()
    session.refresh(card)
    return card


def update_card(*, session: Session, card: Card, card_in: CardUpdate) -> Card:
    """Update a card."""
    update_dict = card_in.model_dump(exclude_unset=True)
    card.sqlmodel_update(update_dict)
    session.add(card)
    session.commit()
    session.refresh(card)
    return card


def move_card(
    *, session: Session, card: Card, list_id: uuid.UUID, position: float
) -> Card:
    """Move a card to a different list/position."""
    card.list_id = list_id
    card.position = position
    session.add(card)
    session.commit()
    session.refresh(card)
    return card


def soft_delete_card(
    *, session: Session, card: Card, deleted_by: uuid.UUID
) -> Card:
    """Soft delete a card."""
    card.is_deleted = True
    card.deleted_at = datetime.utcnow()
    card.deleted_by = str(deleted_by)
    session.add(card)
    session.commit()
    session.refresh(card)
    return card
