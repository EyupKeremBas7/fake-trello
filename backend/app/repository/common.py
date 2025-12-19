"""
Common Repository Functions - Shared database operations.
These functions are used across multiple repositories to avoid code duplication.
"""
import uuid
from sqlmodel import Session, select

from app.models.workspace_members import WorkspaceMember
from app.models.workspaces import Workspace
from app.models.boards import Board
from app.models.enums import MemberRole


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


def get_workspace_by_id(*, session: Session, workspace_id: uuid.UUID) -> Workspace | None:
    """Get workspace by ID."""
    return session.get(Workspace, workspace_id)


def get_board_by_id(*, session: Session, board_id: uuid.UUID) -> Board | None:
    """Get board by ID."""
    return session.get(Board, board_id)
