import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select, or_, SQLModel

from app.api.deps import CurrentUser, SessionDep
from app.models.workspaces import Workspace, WorkspaceCreate, WorkspacePublic, WorkspacesPublic, WorkspaceUpdate
from app.models.workspace_members import WorkspaceMember, WorkspaceMemberCreate, WorkspaceMemberPublic, WorkspaceMembersPublic, WorkspaceMemberUpdate, WorkspaceInvite
from app.models.users import User
from app.models.enums import MemberRole
from app.models.auth import Message

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


def get_user_role_in_workspace(session: SessionDep, user_id: uuid.UUID, workspace_id: uuid.UUID) -> MemberRole | None:
    member = session.exec(
        select(WorkspaceMember).where(
            WorkspaceMember.user_id == user_id,
            WorkspaceMember.workspace_id == workspace_id
        )
    ).first()
    return member.role if member else None


def can_access_workspace(session: SessionDep, user_id: uuid.UUID, workspace: Workspace) -> bool:
    if workspace.owner_id == user_id:
        return True
    role = get_user_role_in_workspace(session, user_id, workspace.id)
    return role is not None


def can_edit_workspace(session: SessionDep, user_id: uuid.UUID, workspace: Workspace) -> bool:
    if workspace.owner_id == user_id:
        return True
    role = get_user_role_in_workspace(session, user_id, workspace.id)
    return role == MemberRole.admin


def can_edit_boards(session: SessionDep, user_id: uuid.UUID, workspace: Workspace) -> bool:
    if workspace.owner_id == user_id:
        return True
    role = get_user_role_in_workspace(session, user_id, workspace.id)
    return role in [MemberRole.admin, MemberRole.member]


@router.get("/", response_model=WorkspacesPublic)
def read_workspaces(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    if current_user.is_superuser:
        count_statement = select(func.count()).select_from(Workspace)
        count = session.exec(count_statement).one()
        statement = select(Workspace).offset(skip).limit(limit)
        workspaces = session.exec(statement).all()
    else:
        count_statement = (
            select(func.count())
            .select_from(Workspace)
            .outerjoin(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
            .where(
                or_(
                    Workspace.owner_id == current_user.id,
                    WorkspaceMember.user_id == current_user.id
                )
            )
        )
        count = session.exec(count_statement).one()
        statement = (
            select(Workspace)
            .outerjoin(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
            .where(
                or_(
                    Workspace.owner_id == current_user.id,
                    WorkspaceMember.user_id == current_user.id
                )
            )
            .distinct()
            .offset(skip)
            .limit(limit)
        )
        workspaces = session.exec(statement).all()

    return WorkspacesPublic(data=workspaces, count=count)


@router.get("/{id}", response_model=WorkspacePublic)
def read_workspace(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> Any:
    workspace = session.get(Workspace, id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    if not current_user.is_superuser and not can_access_workspace(session, current_user.id, workspace):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return workspace


@router.post("/", response_model=WorkspacePublic)
def create_workspace(
    *, session: SessionDep, current_user: CurrentUser, workspace_in: WorkspaceCreate
) -> Any:
    workspace = Workspace.model_validate(workspace_in, update={"owner_id": current_user.id})
    session.add(workspace)
    session.commit()
    session.refresh(workspace)
    return workspace


@router.put("/{id}", response_model=WorkspacePublic)
def update_workspace(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    workspace_in: WorkspaceUpdate,
) -> Any:
    workspace = session.get(Workspace, id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    if not current_user.is_superuser and not can_edit_workspace(session, current_user.id, workspace):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    update_dict = workspace_in.model_dump(exclude_unset=True)
    workspace.sqlmodel_update(update_dict)
    session.add(workspace)
    session.commit()
    session.refresh(workspace)
    return workspace


@router.delete("/{id}")
def delete_workspace(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Message:
    workspace = session.get(Workspace, id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    if not current_user.is_superuser and workspace.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only owner can delete workspace")
    session.delete(workspace)
    session.commit()
    return Message(message="Workspace deleted successfully")


@router.get("/{id}/members", response_model=WorkspaceMembersPublic)
def read_workspace_members(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Any:
    workspace = session.get(Workspace, id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    if not current_user.is_superuser and not can_access_workspace(session, current_user.id, workspace):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    statement = select(WorkspaceMember).where(WorkspaceMember.workspace_id == id)
    members = session.exec(statement).all()
    count = len(members)
    
    return WorkspaceMembersPublic(data=members, count=count)


@router.post("/{id}/members", response_model=WorkspaceMemberPublic)
def add_workspace_member(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    member_in: WorkspaceMemberCreate
) -> Any:
    workspace = session.get(Workspace, id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    if not current_user.is_superuser and not can_edit_workspace(session, current_user.id, workspace):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    existing = session.exec(
        select(WorkspaceMember).where(
            WorkspaceMember.user_id == member_in.user_id,
            WorkspaceMember.workspace_id == id
        )
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="User is already a member")
    
    if member_in.user_id == workspace.owner_id:
        raise HTTPException(status_code=400, detail="Owner cannot be added as member")
    
    member = WorkspaceMember(
        user_id=member_in.user_id,
        workspace_id=id,
        role=member_in.role
    )
    session.add(member)
    session.commit()
    session.refresh(member)
    return member


@router.post("/{id}/invite", response_model=WorkspaceMemberPublic)
def invite_workspace_member(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    invite_in: WorkspaceInvite
) -> Any:
    """Invite a user to workspace by email."""
    workspace = session.get(Workspace, id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    if not current_user.is_superuser and not can_edit_workspace(session, current_user.id, workspace):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Find user by email
    user = session.exec(
        select(User).where(User.email == invite_in.email)
    ).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User with this email not found. They need to register first.")
    
    if user.id == workspace.owner_id:
        raise HTTPException(status_code=400, detail="Owner cannot be added as member")
    
    # Check if already a member
    existing = session.exec(
        select(WorkspaceMember).where(
            WorkspaceMember.user_id == user.id,
            WorkspaceMember.workspace_id == id
        )
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="User is already a member of this workspace")
    
    member = WorkspaceMember(
        user_id=user.id,
        workspace_id=id,
        role=invite_in.role
    )
    session.add(member)
    session.commit()
    session.refresh(member)
    return member


@router.put("/{id}/members/{member_id}", response_model=WorkspaceMemberPublic)
def update_workspace_member(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    member_id: uuid.UUID,
    member_in: WorkspaceMemberUpdate
) -> Any:
    workspace = session.get(Workspace, id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    if not current_user.is_superuser and not can_edit_workspace(session, current_user.id, workspace):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    member = session.get(WorkspaceMember, member_id)
    if not member or member.workspace_id != id:
        raise HTTPException(status_code=404, detail="Member not found")
    
    update_dict = member_in.model_dump(exclude_unset=True)
    member.sqlmodel_update(update_dict)
    session.add(member)
    session.commit()
    session.refresh(member)
    return member


@router.delete("/{id}/members/{member_id}")
def remove_workspace_member(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID, member_id: uuid.UUID
) -> Message:
    workspace = session.get(Workspace, id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    if not current_user.is_superuser and not can_edit_workspace(session, current_user.id, workspace):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    member = session.get(WorkspaceMember, member_id)
    if not member or member.workspace_id != id:
        raise HTTPException(status_code=404, detail="Member not found")
    
    session.delete(member)
    session.commit()
    return Message(message="Member removed successfully")