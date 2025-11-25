import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.models import Board, BoardCreate, BoardsPublic, BoardUpdate, Message

router = APIRouter(prefix="/boards", tags=["boards"])


@router.get("/", response_model=BoardsPublic)
def read_boards(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve Boards.
    """

    if current_user.is_superuser:
        count_statement = select(func.count()).select_from(Board)
        count = session.exec(count_statement).one()
        statement = select(Board).offset(skip).limit(limit)
        Boards = session.exec(statement).all()
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
        Boards = session.exec(statement).all()

    return BoardsPublic(data=Boards, count=count)


@router.get("/{id}", response_model=BoardsPublic)
def read_Board(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> Any:
    """
    Get Board by ID.
    """
    Board = session.get(Board, id)
    if not Board:
        raise HTTPException(status_code=404, detail="Board not found")
    if not current_user.is_superuser and (Board.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return Board


@router.post("/", response_model=BoardsPublic)
def create_Board(
    *, session: SessionDep, current_user: CurrentUser, Board_in: BoardCreate
) -> Any:
    """
    Create new Board.
    """
    Board = Board.model_validate(Board_in, update={"owner_id": current_user.id})
    session.add(Board)
    session.commit()
    session.refresh(Board)
    return Board


@router.put("/{id}", response_model=BoardsPublic)
def update_Board(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    Board_in: BoardUpdate,
) -> Any:
    """
    Update an Board.
    """
    Board = session.get(Board, id)
    if not Board:
        raise HTTPException(status_code=404, detail="Board not found")
    if not current_user.is_superuser and (Board.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    update_dict = Board_in.model_dump(exclude_unset=True)
    Board.sqlmodel_update(update_dict)
    session.add(Board)
    session.commit()
    session.refresh(Board)
    return Board


@router.delete("/{id}")
def delete_Board(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Message:
    """
    Delete an Board.
    """
    Board = session.get(Board, id)
    if not Board:
        raise HTTPException(status_code=404, detail="Board not found")
    if not current_user.is_superuser and (Board.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    session.delete(Board)
    session.commit()
    return Message(message="Board deleted successfully")
