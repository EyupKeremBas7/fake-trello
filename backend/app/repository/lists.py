"""
Lists Repository - All database operations for BoardList model.
"""
import uuid
from datetime import datetime
from typing import Any

from sqlmodel import Session, select, func, or_

from app.models.lists import BoardList, ListCreate, ListUpdate
from app.models.boards import Board
from app.models.workspaces import Workspace
from app.models.workspace_members import WorkspaceMember


# ==================== Helper Functions ====================

def can_access_list_board(*, session: Session, user_id: uuid.UUID, board: Board) -> bool:
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


def get_next_position(*, session: Session, board_id: uuid.UUID) -> float:
    """Get the next position for a new list in a board."""
    last_list = session.exec(
        select(BoardList)
        .where(BoardList.board_id == board_id, BoardList.is_deleted == False)
        .order_by(BoardList.position.desc())
    ).first()
    
    if last_list:
        return last_list.position + 65536.0
    return 65536.0


# ==================== List CRUD ====================

def get_list_by_id(*, session: Session, list_id: uuid.UUID) -> BoardList | None:
    """Get list by ID."""
    return session.get(BoardList, list_id)


def get_board_by_id(*, session: Session, board_id: uuid.UUID) -> Board | None:
    """Get board by ID."""
    return session.get(Board, board_id)


def get_lists_for_user(
    *, session: Session, user_id: uuid.UUID, skip: int = 0, limit: int = 100
) -> tuple[list[BoardList], int]:
    """Get lists that user can access."""
    statement = (
        select(BoardList)
        .join(Board, BoardList.board_id == Board.id)
        .join(Workspace, Board.workspace_id == Workspace.id)
        .outerjoin(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
        .where(
            BoardList.is_deleted == False,
            or_(
                Workspace.owner_id == user_id,
                WorkspaceMember.user_id == user_id
            )
        )
        .distinct()
        .offset(skip)
        .limit(limit)
    )
    lists = session.exec(statement).all()
    count = len(lists)
    
    return list(lists), count


def get_lists_superuser(
    *, session: Session, skip: int = 0, limit: int = 100
) -> tuple[list[BoardList], int]:
    """Get all lists (superuser)."""
    count_statement = select(func.count()).select_from(BoardList).where(BoardList.is_deleted == False)
    count = session.exec(count_statement).one()
    
    statement = select(BoardList).where(BoardList.is_deleted == False).offset(skip).limit(limit)
    lists = session.exec(statement).all()
    
    return list(lists), count


def get_lists_by_board(*, session: Session, board_id: uuid.UUID) -> list[BoardList]:
    """Get all lists for a specific board."""
    statement = select(BoardList).where(
        BoardList.board_id == board_id,
        BoardList.is_deleted == False
    ).order_by(BoardList.position)
    lists = session.exec(statement).all()
    return list(lists)


def create_list(*, session: Session, list_in: ListCreate, auto_position: bool = True) -> BoardList:
    """Create a new list with automatic position calculation."""
    list_data = list_in.model_dump()
    
    # Auto-calculate position if not explicitly set or if using default
    if auto_position and list_data.get("position", 65535.0) == 65535.0:
        list_data["position"] = get_next_position(session=session, board_id=list_in.board_id)
    
    board_list = BoardList(**list_data)
    session.add(board_list)
    session.commit()
    session.refresh(board_list)
    return board_list


def update_list(*, session: Session, board_list: BoardList, list_in: ListUpdate) -> BoardList:
    """Update a list."""
    update_dict = list_in.model_dump(exclude_unset=True)
    board_list.sqlmodel_update(update_dict)
    session.add(board_list)
    session.commit()
    session.refresh(board_list)
    return board_list


def soft_delete_list(
    *, session: Session, board_list: BoardList, deleted_by: uuid.UUID
) -> BoardList:
    """Soft delete a list."""
    board_list.is_deleted = True
    board_list.deleted_at = datetime.utcnow()
    board_list.deleted_by = str(deleted_by)
    session.add(board_list)
    session.commit()
    session.refresh(board_list)
    return board_list
