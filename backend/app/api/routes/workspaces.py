"""
Workspaces API Routes - Clean routes without direct database queries.
"""
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, SessionDep
from app.models.auth import Message
from app.models.workspace_members import (
    WorkspaceInvite,
    WorkspaceMemberCreate,
    WorkspaceMemberPublic,
    WorkspaceMembersPublic,
    WorkspaceMemberUpdate,
)
from app.models.workspaces import (
    WorkspaceCreate,
    WorkspacePublic,
    WorkspacesPublic,
    WorkspaceUpdate,
)
from app.repository import workspaces as workspaces_repo

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.get("/", response_model=WorkspacesPublic)
def read_workspaces(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    if current_user.is_superuser:
        workspaces, count = workspaces_repo.get_workspaces_superuser(
            session=session, skip=skip, limit=limit
        )
    else:
        workspaces, count = workspaces_repo.get_workspaces_for_user(
            session=session, user_id=current_user.id, skip=skip, limit=limit
        )

    return WorkspacesPublic(data=workspaces, count=count)


@router.get("/{id}", response_model=WorkspacePublic)
def read_workspace(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> Any:
    workspace = workspaces_repo.get_workspace_by_id(session=session, workspace_id=id)
    if not workspace or workspace.is_deleted:
        raise HTTPException(status_code=404, detail="Workspace not found")
    if not current_user.is_superuser and not workspaces_repo.can_access_workspace(
        session=session, user_id=current_user.id, workspace=workspace
    ):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return workspace


@router.post("/", response_model=WorkspacePublic)
def create_workspace(
    *, session: SessionDep, current_user: CurrentUser, workspace_in: WorkspaceCreate
) -> Any:
    workspace = workspaces_repo.create_workspace(
        session=session, workspace_in=workspace_in, owner_id=current_user.id
    )
    return workspace


@router.put("/{id}", response_model=WorkspacePublic)
def update_workspace(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    workspace_in: WorkspaceUpdate,
) -> Any:
    workspace = workspaces_repo.get_workspace_by_id(session=session, workspace_id=id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    if not current_user.is_superuser and not workspaces_repo.can_edit_workspace(
        session=session, user_id=current_user.id, workspace=workspace
    ):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    workspace = workspaces_repo.update_workspace(
        session=session, workspace=workspace, workspace_in=workspace_in
    )
    return workspace


@router.delete("/{id}")
def delete_workspace(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Message:
    workspace = workspaces_repo.get_workspace_by_id(session=session, workspace_id=id)
    if not workspace or workspace.is_deleted:
        raise HTTPException(status_code=404, detail="Workspace not found")
    if not current_user.is_superuser and workspace.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only owner can delete workspace")

    workspaces_repo.soft_delete_workspace(
        session=session, workspace=workspace, deleted_by=current_user.id
    )
    return Message(message="Workspace deleted successfully")


@router.get("/{id}/members", response_model=WorkspaceMembersPublic)
def read_workspace_members(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Any:
    workspace = workspaces_repo.get_workspace_by_id(session=session, workspace_id=id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    if not current_user.is_superuser and not workspaces_repo.can_access_workspace(
        session=session, user_id=current_user.id, workspace=workspace
    ):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    members = workspaces_repo.get_workspace_members(session=session, workspace_id=id)

    return WorkspaceMembersPublic(data=members, count=len(members))


@router.post("/{id}/members", response_model=WorkspaceMemberPublic)
def add_workspace_member(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    member_in: WorkspaceMemberCreate
) -> Any:
    workspace = workspaces_repo.get_workspace_by_id(session=session, workspace_id=id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    if not current_user.is_superuser and not workspaces_repo.can_edit_workspace(
        session=session, user_id=current_user.id, workspace=workspace
    ):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    existing = workspaces_repo.get_member_by_user_and_workspace(
        session=session, user_id=member_in.user_id, workspace_id=id
    )
    if existing:
        raise HTTPException(status_code=400, detail="User is already a member")

    if member_in.user_id == workspace.owner_id:
        raise HTTPException(status_code=400, detail="Owner cannot be added as member")

    member = workspaces_repo.add_workspace_member(
        session=session, user_id=member_in.user_id, workspace_id=id, role=member_in.role
    )
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
    workspace = workspaces_repo.get_workspace_by_id(session=session, workspace_id=id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    if not current_user.is_superuser and not workspaces_repo.can_edit_workspace(
        session=session, user_id=current_user.id, workspace=workspace
    ):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    user = workspaces_repo.get_user_by_email(session=session, email=invite_in.email)

    if not user:
        raise HTTPException(status_code=404, detail="User with this email not found. They need to register first.")

    if user.id == workspace.owner_id:
        raise HTTPException(status_code=400, detail="Owner cannot be added as member")

    existing = workspaces_repo.get_member_by_user_and_workspace(
        session=session, user_id=user.id, workspace_id=id
    )
    if existing:
        raise HTTPException(status_code=400, detail="User is already a member of this workspace")
        
    member = workspaces_repo.add_workspace_member(
        session=session, user_id=user.id, workspace_id=id, role=invite_in.role
    )
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
    workspace = workspaces_repo.get_workspace_by_id(session=session, workspace_id=id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    if not current_user.is_superuser and not workspaces_repo.can_edit_workspace(
        session=session, user_id=current_user.id, workspace=workspace
    ):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    member = workspaces_repo.get_member_by_id(session=session, member_id=member_id)
    if not member or member.workspace_id != id:
        raise HTTPException(status_code=404, detail="Member not found")

    member = workspaces_repo.update_workspace_member(
        session=session, member=member, member_in=member_in
    )
    return member


@router.delete("/{id}/members/{member_id}")
def remove_workspace_member(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID, member_id: uuid.UUID
) -> Message:
    workspace = workspaces_repo.get_workspace_by_id(session=session, workspace_id=id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    if not current_user.is_superuser and not workspaces_repo.can_edit_workspace(
        session=session, user_id=current_user.id, workspace=workspace
    ):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    member = workspaces_repo.get_member_by_id(session=session, member_id=member_id)
    if not member or member.workspace_id != id:
        raise HTTPException(status_code=404, detail="Member not found")

    workspaces_repo.remove_workspace_member(session=session, member=member)
    return Message(message="Member removed successfully")
