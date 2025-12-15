import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select, or_

from app.api.deps import CurrentUser, SessionDep
from app.models.lists import BoardList, ListCreate, ListUpdate, ListsPublic, ListPublic
from app.models.boards import Board
from app.models.workspaces import Workspace
from app.models.workspace_members import WorkspaceMember
from app.models.enums import MemberRole
from app.models.auth import Message

router = APIRouter(prefix="/lists", tags=["lists"])


def can_access_list_board(session, user_id: uuid.UUID, board: Board) -> bool:
    """Check if user can access the board's lists."""
    workspace = session.get(Workspace, board.workspace_id)
    if not workspace:
        return False
    if workspace.owner_id == user_id:
        return True
    member = session.exec(
        select(WorkspaceMember).where(
            WorkspaceMember.user_id == user_id,
            WorkspaceMember.workspace_id == workspace.id
        )
    ).first()
    return member is not None


@router.get("/", response_model=ListsPublic)
def read_board_lists(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """Get all lists."""
    if current_user.is_superuser:
        count_statement = select(func.count()).select_from(BoardList).where(BoardList.is_deleted == False)
        count = session.exec(count_statement).one()
        statement = select(BoardList).where(BoardList.is_deleted == False).offset(skip).limit(limit)
        lists = session.exec(statement).all()
    else:
        statement = (
            select(BoardList)
            .join(Board, BoardList.board_id == Board.id)
            .join(Workspace, Board.workspace_id == Workspace.id)
            .outerjoin(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
            .where(
                BoardList.is_deleted == False,
                or_(
                    Workspace.owner_id == current_user.id,
                    WorkspaceMember.user_id == current_user.id
                )
            )
            .distinct()
            .offset(skip)
            .limit(limit)
        )
        lists = session.exec(statement).all()
        count = len(lists)

    return ListsPublic(data=lists, count=count)


@router.get("/board/{board_id}", response_model=ListsPublic)
def read_lists_by_board(
    session: SessionDep, current_user: CurrentUser, board_id: uuid.UUID
) -> Any:
    """Get all lists for a specific board."""
    board = session.get(Board, board_id)
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    
    if not current_user.is_superuser and not can_access_list_board(session, current_user.id, board):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    statement = select(BoardList).where(BoardList.board_id == board_id, BoardList.is_deleted == False).order_by(BoardList.position)
    lists = session.exec(statement).all()
    
    return ListsPublic(data=lists, count=len(lists))


@router.get("/{id}", response_model=ListPublic)
def read_board_list(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> Any:
    """
    Get Board List by ID.
    """
    board_list = session.get(BoardList, id)
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
    if not board_list or board_list.is_deleted:
        raise HTTPException(status_code=404, detail="List not found")
    board_list.is_deleted = True
    board_list.deleted_at = datetime.utcnow()
    board_list.deleted_by = str(current_user.id)
    session.add(board_list)
    session.commit()
    return Message(message="List deleted successfully")