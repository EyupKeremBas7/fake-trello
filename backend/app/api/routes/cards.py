import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.models.cards import Card, CardCreate, CardsPublic, CardUpdate
from app.models.auth import Message

router = APIRouter(prefix="/cards", tags=["cards"])


@router.get("/", response_model=CardsPublic)
def read_cards(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve Boards.
    """

    if current_user.is_superuser:
        count_statement = select(func.count()).select_from(Board)
        count = session.exec(count_statement).one()
        statement = select(Board).offset(skip).limit(limit)
        boards = session.exec(statement).all() 
    else:
        count_statement = (
            select(func.count())
            .select_from(Board)
            .where(Board.owner_id == current_user.id)
        )
        count = session.exec(count_statement).one()
        statement = (
            select(Board)
            .where(Board.owner_id == current_user.id)
            .offset(skip)
            .limit(limit)
        )
        boards = session.exec(statement).all() 

    return BoardsPublic(data=boards, count=count)

@router.get("/{id}", response_model=Board) 
def read_board(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> Any:
    """
    Get Board by ID.
    """
    board = session.get(Board, id) 
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    if not current_user.is_superuser and (board.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return board


@router.post("/", response_model=Board) 
def create_board(
    *, session: SessionDep, current_user: CurrentUser, board_in: BoardCreate
) -> Any:
    """
    Create new Board.
    """
    board = Board.model_validate(board_in, update={"owner_id": current_user.id})
    session.add(board)
    session.commit()
    session.refresh(board)
    return board


@router.put("/{id}", response_model=Board)
def update_board(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    board_in: BoardUpdate,
) -> Any:
    """
    Update a Board.
    """
    board = session.get(Board, id)
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    if not current_user.is_superuser and (board.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    
    update_dict = board_in.model_dump(exclude_unset=True)
    board.sqlmodel_update(update_dict)
    session.add(board)
    session.commit()
    session.refresh(board)
    return board


@router.delete("/{id}")
def delete_board(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Message:
    """
    Delete a Board.
    """
    board = session.get(Board, id)
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    if not current_user.is_superuser and (board.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    session.delete(board)
    session.commit()
    return Message(message="Board deleted successfully")