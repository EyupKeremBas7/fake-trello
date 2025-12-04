import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.models.cards import Card, CardCreate, CardsPublic, CardUpdate
from app.models.lists import BoardList
from app.models.auth import Message

router = APIRouter(prefix="/cards", tags=["cards"])


@router.get("/", response_model=CardsPublic)
def read_cards(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve Cards.
    """
    if current_user.is_superuser:
        count_statement = select(func.count()).select_from(Card)
        count = session.exec(count_statement).one()
        statement = select(Card).offset(skip).limit(limit)
        cards = session.exec(statement).all()
    else:
       
        count_statement = select(func.count()).select_from(Card)
        count = session.exec(count_statement).one()
        statement = select(Card).offset(skip).limit(limit)
        cards = session.exec(statement).all()

    return CardsPublic(data=cards, count=count)


@router.get("/{id}", response_model=Card)
def read_card(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> Any:
    """
    Get Card by ID.
    """
    card = session.get(Card, id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    return card


@router.post("/", response_model=Card)
def create_card(
    *, session: SessionDep, current_user: CurrentUser, card_in: CardCreate
) -> Any:
    """
    Create new Card.
    """
    board_list = session.get(BoardList, card_in.list_id)
    if not board_list:
        raise HTTPException(status_code=404, detail="List not found")
    
    card = Card.model_validate(card_in)
    session.add(card)
    session.commit()
    session.refresh(card)
    return card


@router.put("/{id}", response_model=Card)
def update_card(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    card_in: CardUpdate,
) -> Any:
    """
    Update a Card.
    """
    card = session.get(Card, id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    update_dict = card_in.model_dump(exclude_unset=True)
    card.sqlmodel_update(update_dict)
    session.add(card)
    session.commit()
    session.refresh(card)
    return card


@router.delete("/{id}")
def delete_card(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Message:
    """
    Delete a Card.
    """
    card = session.get(Card, id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    session.delete(card)
    session.commit()
    return Message(message="Card deleted successfully")