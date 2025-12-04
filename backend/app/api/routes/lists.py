import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.models.lists import BoardList, ListCreate, ListUpdate, ListsPublic, ListPublic
from app.models.boards import Board
from app.models.auth import Message

router = APIRouter(prefix="/lists", tags=["lists"])


@router.get("/", response_model=ListsPublic)
def read_board_lists(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve Board Lists.
    """
    count_statement = select(func.count()).select_from(BoardList)
    count = session.exec(count_statement).one()
    statement = select(BoardList).offset(skip).limit(limit)
    lists = session.exec(statement).all()

    return ListsPublic(data=lists, count=count)


@router.get("/{id}", response_model=ListPublic)
def read_board_list(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> Any:
    """
    Get Board List by ID.
    """
    board_list = session.get(BoardList, id)
    if not board_list:
        raise HTTPException(status_code=404, detail="List not found")
    return board_list


@router.post("/", response_model=ListPublic)
def create_board_list(
    *, session: SessionDep, current_user: CurrentUser, list_in: ListCreate
) -> Any:
    """
    Create new Board List.
    """
    board = session.get(Board, list_in.board_id)
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    
    board_list = BoardList.model_validate(list_in)
    session.add(board_list)
    session.commit()
    session.refresh(board_list)
    return board_list


@router.put("/{id}", response_model=ListPublic)
def update_board_list(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    list_in: ListUpdate,
) -> Any:
    """
    Update a Board List.
    """
    board_list = session.get(BoardList, id)
    if not board_list:
        raise HTTPException(status_code=404, detail="List not found")
    
    update_dict = list_in.model_dump(exclude_unset=True)
    board_list.sqlmodel_update(update_dict)
    session.add(board_list)
    session.commit()
    session.refresh(board_list)
    return board_list


@router.delete("/{id}")
def delete_board_list(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Message:
    """
    Delete a Board List.
    """
    board_list = session.get(BoardList, id)
    if not board_list:
        raise HTTPException(status_code=404, detail="List not found")
    session.delete(board_list)
    session.commit()
    return Message(message="List deleted successfully")