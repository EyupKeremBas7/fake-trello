"""
Boards Repository - All database operations for Board model.
"""
import uuid
from datetime import datetime
from typing import Any

from sqlmodel import Session, select, func, or_

from app.models.boards import Board, BoardCreate, BoardUpdate
from app.models.workspaces import Workspace
from app.models.workspace_members import WorkspaceMember
from app.models.enums import MemberRole


# ==================== Helper Functions ====================

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


def can_access_board(*, session: Session, user_id: uuid.UUID, board: Board) -> bool:
    """Check if user can access the board."""
    workspace = session.get(Workspace, board.workspace_id)
    if not workspace:
        return False
    if workspace.owner_id == user_id:
        return True
    role = get_user_role_in_workspace(session=session, user_id=user_id, workspace_id=workspace.id)
    return role is not None


def can_edit_board(*, session: Session, user_id: uuid.UUID, board: Board) -> bool:
    """Check if user can edit the board."""
    workspace = session.get(Workspace, board.workspace_id)
    if not workspace:
        return False
    if workspace.owner_id == user_id:
        return True
    role = get_user_role_in_workspace(session=session, user_id=user_id, workspace_id=workspace.id)
    return role in [MemberRole.admin, MemberRole.member]


# ==================== Board CRUD ====================

def get_board_by_id(*, session: Session, board_id: uuid.UUID) -> Board | None:
    """Get board by ID."""
    return session.get(Board, board_id)


def get_workspace_by_id(*, session: Session, workspace_id: uuid.UUID) -> Workspace | None:
    """Get workspace by ID."""
    return session.get(Workspace, workspace_id)


def get_boards_for_user(
    *, session: Session, user_id: uuid.UUID, skip: int = 0, limit: int = 100
) -> tuple[list[Board], int]:
    """Get boards that user can access."""
    statement = (
        select(Board)
        .join(Workspace, Board.workspace_id == Workspace.id)
        .outerjoin(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
        .where(
            Board.is_deleted == False,
            or_(
                Workspace.owner_id == user_id,
                WorkspaceMember.user_id == user_id
            )
        )
        .distinct()
        .offset(skip)
        .limit(limit)
    )
    boards = session.exec(statement).all()
    count = len(boards)
    
    return list(boards), count


def get_boards_superuser(
    *, session: Session, skip: int = 0, limit: int = 100
) -> tuple[list[Board], int]:
    """Get all boards (superuser)."""
    count_statement = select(func.count()).select_from(Board).where(Board.is_deleted == False)
    count = session.exec(count_statement).one()
    
    statement = select(Board).where(Board.is_deleted == False).offset(skip).limit(limit)
    boards = session.exec(statement).all()
    
    return list(boards), count


def create_board(
    *, session: Session, board_in: BoardCreate, owner_id: uuid.UUID
) -> Board:
    """Create a new board."""
    board = Board.model_validate(board_in, update={"owner_id": owner_id})
    session.add(board)
    session.commit()
    session.refresh(board)
    return board


def update_board(
    *, session: Session, board: Board, board_in: BoardUpdate
) -> Board:
    """Update a board."""
    update_dict = board_in.model_dump(exclude_unset=True)
    board.sqlmodel_update(update_dict)
    session.add(board)
    session.commit()
    session.refresh(board)
    return board


def soft_delete_board(
    *, session: Session, board: Board, deleted_by: uuid.UUID
) -> Board:
    """Soft delete a board."""
    board.is_deleted = True
    board.deleted_at = datetime.utcnow()
    board.deleted_by = str(deleted_by)
    session.add(board)
    session.commit()
    session.refresh(board)
    return board
