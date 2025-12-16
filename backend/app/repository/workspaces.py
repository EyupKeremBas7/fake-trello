"""
Workspaces Repository - All database operations for Workspace and WorkspaceMember models.
"""
import uuid
from datetime import datetime
from typing import Any

from sqlmodel import Session, select, func, or_

from app.models.workspaces import Workspace, WorkspaceCreate, WorkspaceUpdate
from app.models.workspace_members import WorkspaceMember, WorkspaceMemberCreate, WorkspaceMemberUpdate
from app.models.users import User
from app.models.enums import MemberRole


# ==================== Workspace Member Helpers ====================

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


def can_access_workspace(
    *, session: Session, user_id: uuid.UUID, workspace: Workspace
) -> bool:
    """Check if user can access the workspace."""
    if workspace.owner_id == user_id:
        return True
    role = get_user_role_in_workspace(session=session, user_id=user_id, workspace_id=workspace.id)
    return role is not None


def can_edit_workspace(
    *, session: Session, user_id: uuid.UUID, workspace: Workspace
) -> bool:
    """Check if user can edit the workspace (owner or admin)."""
    if workspace.owner_id == user_id:
        return True
    role = get_user_role_in_workspace(session=session, user_id=user_id, workspace_id=workspace.id)
    return role == MemberRole.admin


def can_edit_boards(
    *, session: Session, user_id: uuid.UUID, workspace: Workspace
) -> bool:
    """Check if user can edit boards in workspace."""
    if workspace.owner_id == user_id:
        return True
    role = get_user_role_in_workspace(session=session, user_id=user_id, workspace_id=workspace.id)
    return role in [MemberRole.admin, MemberRole.member]


# ==================== Workspace CRUD ====================

def get_workspace_by_id(*, session: Session, workspace_id: uuid.UUID) -> Workspace | None:
    """Get workspace by ID."""
    return session.get(Workspace, workspace_id)


def get_workspaces_for_user(
    *, session: Session, user_id: uuid.UUID, skip: int = 0, limit: int = 100
) -> tuple[list[Workspace], int]:
    """Get workspaces that user owns or is a member of."""
    count_statement = (
        select(func.count())
        .select_from(Workspace)
        .outerjoin(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
        .where(
            Workspace.is_deleted == False,
            or_(
                Workspace.owner_id == user_id,
                WorkspaceMember.user_id == user_id
            )
        )
    )
    count = session.exec(count_statement).one()
    
    statement = (
        select(Workspace)
        .outerjoin(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
        .where(
            Workspace.is_deleted == False,
            or_(
                Workspace.owner_id == user_id,
                WorkspaceMember.user_id == user_id
            )
        )
        .distinct()
        .offset(skip)
        .limit(limit)
    )
    workspaces = session.exec(statement).all()
    
    return list(workspaces), count


def get_workspaces_superuser(
    *, session: Session, skip: int = 0, limit: int = 100
) -> tuple[list[Workspace], int]:
    """Get all workspaces (superuser)."""
    count_statement = select(func.count()).select_from(Workspace).where(Workspace.is_deleted == False)
    count = session.exec(count_statement).one()
    
    statement = select(Workspace).where(Workspace.is_deleted == False).offset(skip).limit(limit)
    workspaces = session.exec(statement).all()
    
    return list(workspaces), count


def create_workspace(
    *, session: Session, workspace_in: WorkspaceCreate, owner_id: uuid.UUID
) -> Workspace:
    """Create a new workspace."""
    workspace = Workspace.model_validate(workspace_in, update={"owner_id": owner_id})
    session.add(workspace)
    session.commit()
    session.refresh(workspace)
    return workspace


def update_workspace(
    *, session: Session, workspace: Workspace, workspace_in: WorkspaceUpdate
) -> Workspace:
    """Update a workspace."""
    update_dict = workspace_in.model_dump(exclude_unset=True)
    workspace.sqlmodel_update(update_dict)
    session.add(workspace)
    session.commit()
    session.refresh(workspace)
    return workspace


def soft_delete_workspace(
    *, session: Session, workspace: Workspace, deleted_by: uuid.UUID
) -> Workspace:
    """Soft delete a workspace."""
    workspace.is_deleted = True
    workspace.deleted_at = datetime.utcnow()
    workspace.deleted_by = str(deleted_by)
    session.add(workspace)
    session.commit()
    session.refresh(workspace)
    return workspace


# ==================== Workspace Members CRUD ====================

def get_workspace_members(
    *, session: Session, workspace_id: uuid.UUID
) -> list[WorkspaceMember]:
    """Get all members of a workspace."""
    statement = select(WorkspaceMember).where(WorkspaceMember.workspace_id == workspace_id)
    members = session.exec(statement).all()
    return list(members)


def get_member_by_user_and_workspace(
    *, session: Session, user_id: uuid.UUID, workspace_id: uuid.UUID
) -> WorkspaceMember | None:
    """Get workspace member by user_id and workspace_id."""
    existing = session.exec(
        select(WorkspaceMember).where(
            WorkspaceMember.user_id == user_id,
            WorkspaceMember.workspace_id == workspace_id
        )
    ).first()
    return existing


def get_member_by_id(*, session: Session, member_id: uuid.UUID) -> WorkspaceMember | None:
    """Get workspace member by ID."""
    return session.get(WorkspaceMember, member_id)


def add_workspace_member(
    *, session: Session, user_id: uuid.UUID, workspace_id: uuid.UUID, role: MemberRole
) -> WorkspaceMember:
    """Add a member to workspace."""
    member = WorkspaceMember(
        user_id=user_id,
        workspace_id=workspace_id,
        role=role
    )
    session.add(member)
    session.commit()
    session.refresh(member)
    return member


def update_workspace_member(
    *, session: Session, member: WorkspaceMember, member_in: WorkspaceMemberUpdate
) -> WorkspaceMember:
    """Update a workspace member's role."""
    update_dict = member_in.model_dump(exclude_unset=True)
    member.sqlmodel_update(update_dict)
    session.add(member)
    session.commit()
    session.refresh(member)
    return member


def remove_workspace_member(*, session: Session, member: WorkspaceMember) -> None:
    """Remove a member from workspace."""
    session.delete(member)
    session.commit()


def get_user_by_email(*, session: Session, email: str) -> User | None:
    """Get user by email for invitations."""
    return session.exec(
        select(User).where(User.email == email)
    ).first()
