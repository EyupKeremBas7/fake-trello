import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select, or_

from app.api.deps import CurrentUser, SessionDep
from app.models.cards import Card, CardCreate, CardPublic, CardsPublic, CardUpdate
from app.models.lists import BoardList
from app.models.boards import Board
from app.models.workspaces import Workspace
from app.models.workspace_members import WorkspaceMember
from app.models.enums import MemberRole
from app.models.auth import Message

router = APIRouter(prefix="/cards", tags=["cards"])


def get_user_role_in_workspace(session: SessionDep, user_id: uuid.UUID, workspace_id: uuid.UUID) -> MemberRole | None:
    member = session.exec(
        select(WorkspaceMember).where(
            WorkspaceMember.user_id == user_id,
            WorkspaceMember.workspace_id == workspace_id
        )
    ).first()
    return member.role if member else None


def can_access_card(session: SessionDep, user_id: uuid.UUID, card: Card) -> bool:
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
    role = get_user_role_in_workspace(session, user_id, workspace.id)
    return role is not None


def can_edit_card(session: SessionDep, user_id: uuid.UUID, card: Card) -> bool:
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
    role = get_user_role_in_workspace(session, user_id, workspace.id)
    return role in [MemberRole.admin, MemberRole.member]


@router.get("/", response_model=CardsPublic)
def read_cards(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    if current_user.is_superuser:
        count_statement = select(func.count()).select_from(Card).where(Card.is_deleted == False)
        count = session.exec(count_statement).one()
        statement = select(Card).where(Card.is_deleted == False).offset(skip).limit(limit)
        cards = session.exec(statement).all()
    else:
        statement = (
            select(Card)
            .join(BoardList, Card.list_id == BoardList.id)
            .join(Board, BoardList.board_id == Board.id)
            .join(Workspace, Board.workspace_id == Workspace.id)
            .outerjoin(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
            .where(
                Card.is_deleted == False,
                or_(
                    Workspace.owner_id == current_user.id,
                    WorkspaceMember.user_id == current_user.id
                )
            )
            .distinct()
            .offset(skip)
            .limit(limit)
        )
        cards = session.exec(statement).all()
        count = len(cards)

    return CardsPublic(data=cards, count=count)


@router.get("/{id}", response_model=CardPublic)
def read_card(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> Any:
    card = session.get(Card, id)
    if not card or card.is_deleted:
        raise HTTPException(status_code=404, detail="Card not found")
    if not current_user.is_superuser and not can_access_card(session, current_user.id, card):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return card


@router.post("/", response_model=CardPublic)
def create_card(
    *, session: SessionDep, current_user: CurrentUser, card_in: CardCreate
) -> Any:
    board_list = session.get(BoardList, card_in.list_id)
    if not board_list:
        raise HTTPException(status_code=404, detail="List not found")
    
    board = session.get(Board, board_list.board_id)
    workspace = session.get(Workspace, board.workspace_id)
    
    if workspace.owner_id != current_user.id:
        role = get_user_role_in_workspace(session, current_user.id, workspace.id)
        if role not in [MemberRole.admin, MemberRole.member]:
            raise HTTPException(status_code=403, detail="Not enough permissions")
    
    card = Card.model_validate(card_in)
    session.add(card)
    session.commit()
    session.refresh(card)
    return card


@router.put("/{id}", response_model=CardPublic)
def update_card(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    card_in: CardUpdate,
) -> Any:
    card = session.get(Card, id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    if not current_user.is_superuser and not can_edit_card(session, current_user.id, card):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    update_dict = card_in.model_dump(exclude_unset=True)
    card.sqlmodel_update(update_dict)
    session.add(card)
    session.commit()
    session.refresh(card)
    return card


@router.patch("/{id}/move", response_model=CardPublic)
def move_card(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    list_id: uuid.UUID,
    position: float
) -> Any:
    card = session.get(Card, id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    if not current_user.is_superuser and not can_edit_card(session, current_user.id, card):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    new_list = session.get(BoardList, list_id)
    if not new_list:
        raise HTTPException(status_code=404, detail="Target list not found")
    
    card.list_id = list_id
    card.position = position
    session.add(card)
    session.commit()
    session.refresh(card)
    return card


@router.delete("/{id}")
def delete_card(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Message:
    card = session.get(Card, id)
    if not card or card.is_deleted:
        raise HTTPException(status_code=404, detail="Card not found")
    if not current_user.is_superuser and not can_edit_card(session, current_user.id, card):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    card.is_deleted = True
    card.deleted_at = datetime.utcnow()
    card.deleted_by = str(current_user.id)
    session.add(card)
    session.commit()
    return Message(message="Card deleted successfully")