import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.models.workspaces import Workspace, WorkspaceCreate, WorkspacesPublic, WorkspaceUpdate
from app.models.auth import Message

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.get("/", response_model=WorkspacesPublic)
def read_workspaces(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve Workspaces.
    """

    if current_user.is_superuser:
        count_statement = select(func.count()).select_from(Workspace)
        count = session.exec(count_statement).one()
        statement = select(Workspace).offset(skip).limit(limit)
        workspaces = session.exec(statement).all() # Değişken adı düzeltildi
    else:
        count_statement = (
            select(func.count())
            .select_from(Workspace)
            .where(Workspace.owner_id == current_user.id)
        )
        count = session.exec(count_statement).one()
        statement = (
            select(Workspace)
            .where(Workspace.owner_id == current_user.id)
            .offset(skip)
            .limit(limit)
        )
        workspaces = session.exec(statement).all() # Değişken adı düzeltildi

    # HATA BURADAYDI: data=Workspace yerine data=workspaces olmalı
    return WorkspacesPublic(data=workspaces, count=count)


@router.get("/{id}", response_model=WorkspacesPublic) # Dikkat: Tekil dönüş tipi WorkspacePublic değil WorkspacePublic içindeki tekil yapı olmalı ama şimdilik modelinize göre böyle kalsın
def read_workspace(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> Any:
    """
    Get Workspace by ID.
    """
    workspace = session.get(Workspace, id) # Değişken adı küçültüldü
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    if not current_user.is_superuser and (workspace.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return workspace


@router.post("/", response_model=WorkspacesPublic) # Burası da normalde WorkspacePublic değil tekil Workspace dönmeli
def create_workspace(
    *, session: SessionDep, current_user: CurrentUser, workspace_in: WorkspaceCreate
) -> Any:
    """
    Create new Workspace.
    """
    workspace = Workspace.model_validate(workspace_in, update={"owner_id": current_user.id})
    session.add(workspace)
    session.commit()
    session.refresh(workspace)
    return workspace


@router.put("/{id}", response_model=WorkspacesPublic)
def update_workspace(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    workspace_in: WorkspaceUpdate,
) -> Any:
    """
    Update an Workspace.
    """
    workspace = session.get(Workspace, id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    if not current_user.is_superuser and (workspace.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    
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
    """
    Delete an Workspace.
    """
    workspace = session.get(Workspace, id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    if not current_user.is_superuser and (workspace.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    session.delete(workspace)
    session.commit()
    return Message(message="Workspace deleted successfully")