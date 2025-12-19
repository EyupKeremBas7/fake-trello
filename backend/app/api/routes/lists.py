"""
Lists API Routes - Clean routes without direct database queries.
"""
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, SessionDep
from app.models.auth import Message
from app.models.lists import ListCreate, ListPublic, ListsPublic, ListUpdate
from app.repository import lists as lists_repo

router = APIRouter(prefix="/lists", tags=["lists"])


@router.get("/", response_model=ListsPublic)
def read_board_lists(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """Get all lists."""
    if current_user.is_superuser:
        lists, count = lists_repo.get_lists_superuser(
            session=session, skip=skip, limit=limit
        )
    else:
        lists, count = lists_repo.get_lists_for_user(
            session=session, user_id=current_user.id, skip=skip, limit=limit
        )

    return ListsPublic(data=lists, count=count)


@router.get("/board/{board_id}", response_model=ListsPublic)
def read_lists_by_board(
    session: SessionDep, current_user: CurrentUser, board_id: uuid.UUID
) -> Any:
    """Get all lists for a specific board."""
    board = lists_repo.get_board_by_id(session=session, board_id=board_id)
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")

    if not current_user.is_superuser and not lists_repo.can_access_list_board(
        session=session, user_id=current_user.id, board=board
    ):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    lists = lists_repo.get_lists_by_board(session=session, board_id=board_id)

    return ListsPublic(data=lists, count=len(lists))


@router.get("/{id}", response_model=ListPublic)
def read_board_list(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> Any:
    """
    Get Board List by ID.
    """
    board_list = lists_repo.get_list_by_id(session=session, list_id=id)
    if not board_list or board_list.is_deleted:
        raise HTTPException(status_code=404, detail="List not found")
    return board_list


@router.post("/", response_model=ListPublic)
def create_board_list(
    *, session: SessionDep, current_user: CurrentUser, list_in: ListCreate
) -> Any:
    """
    Create new Board List.
    """
    board = lists_repo.get_board_by_id(session=session, board_id=list_in.board_id)
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")

    board_list = lists_repo.create_list(session=session, list_in=list_in)
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
    board_list = lists_repo.get_list_by_id(session=session, list_id=id)
    if not board_list:
        raise HTTPException(status_code=404, detail="List not found")

    board_list = lists_repo.update_list(session=session, board_list=board_list, list_in=list_in)
    return board_list


@router.delete("/{id}")
def delete_board_list(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Message:
    """
    Delete a Board List.
    """
    board_list = lists_repo.get_list_by_id(session=session, list_id=id)
    if not board_list or board_list.is_deleted:
        raise HTTPException(status_code=404, detail="List not found")

    lists_repo.soft_delete_list(session=session, board_list=board_list, deleted_by=current_user.id)
    return Message(message="List deleted successfully")
