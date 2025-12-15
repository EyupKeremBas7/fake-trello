import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select, or_

from app.api.deps import CurrentUser, SessionDep
from app.models.boards import Board, BoardCreate, BoardPublic, BoardsPublic, BoardUpdate
from app.models.workspaces import Workspace
from app.models.workspace_members import WorkspaceMember
from app.models.enums import MemberRole
from app.models.auth import Message

router = APIRouter(prefix="/boards", tags=["boards"])


def get_user_role_in_workspace(session: SessionDep, user_id: uuid.UUID, workspace_id: uuid.UUID) -> MemberRole | None:
    member = session.exec(
        select(WorkspaceMember).where(
            WorkspaceMember.user_id == user_id,
            WorkspaceMember.workspace_id == workspace_id
        )
    ).first()
    return member.role if member else None


def can_access_board(session: SessionDep, user_id: uuid.UUID, board: Board) -> bool:
    workspace = session.get(Workspace, board.workspace_id)
    if not workspace:
        return False
    if workspace.owner_id == user_id:
        return True
    role = get_user_role_in_workspace(session, user_id, workspace.id)
    return role is not None


def can_edit_board(session: SessionDep, user_id: uuid.UUID, board: Board) -> bool:
    workspace = session.get(Workspace, board.workspace_id)
    if not workspace:
        return False
    if workspace.owner_id == user_id:
        return True
    role = get_user_role_in_workspace(session, user_id, workspace.id)
    return role in [MemberRole.admin, MemberRole.member]


@router.get("/", response_model=BoardsPublic)
def read_boards(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    if current_user.is_superuser:
        count_statement = select(func.count()).select_from(Board).where(Board.is_deleted == False)
        count = session.exec(count_statement).one()
        statement = select(Board).where(Board.is_deleted == False).offset(skip).limit(limit)
        boards = session.exec(statement).all()
    else:
        statement = (
            select(Board)
            .join(Workspace, Board.workspace_id == Workspace.id)
            .outerjoin(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
            .where(
                Board.is_deleted == False,
                or_(
                    Workspace.owner_id == current_user.id,
                    WorkspaceMember.user_id == current_user.id
                )
            )
            .distinct()
            .offset(skip)
            .limit(limit)
        )
        boards = session.exec(statement).all()
        count = len(boards)

    return BoardsPublic(data=boards, count=count)


@router.get("/{id}", response_model=BoardPublic)
def read_board(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> Any:
    board = session.get(Board, id)
    if not board or board.is_deleted:
        raise HTTPException(status_code=404, detail="Board not found")
    if not current_user.is_superuser and not can_access_board(session, current_user.id, board):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return board


@router.post("/", response_model=BoardPublic)
def create_board(
    *, session: SessionDep, current_user: CurrentUser, board_in: BoardCreate
) -> Any:
    workspace = session.get(Workspace, board_in.workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    if workspace.owner_id != current_user.id:
        role = get_user_role_in_workspace(session, current_user.id, workspace.id)
        if role not in [MemberRole.admin, MemberRole.member]:
            raise HTTPException(status_code=403, detail="Not enough permissions to create board")
    
    board = Board.model_validate(board_in, update={"owner_id": current_user.id})
    session.add(board)
    session.commit()
    session.refresh(board)
    return board


@router.put("/{id}", response_model=BoardPublic)
def update_board(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    board_in: BoardUpdate,
) -> Any:
    board = session.get(Board, id)
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    if not current_user.is_superuser and not can_edit_board(session, current_user.id, board):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    update_dict = board_in.model_dump(exclude_unset=True)
    board.sqlmodel_update(update_dict)
    session.add(board)
    session.commit()
    session.refresh(board)
    return board


@router.delete("/{id}")
def delete_board(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Message:
    board = session.get(Board, id)
    if not board or board.is_deleted:
        raise HTTPException(status_code=404, detail="Board not found")
    
    workspace = session.get(Workspace, board.workspace_id)
    if not current_user.is_superuser and workspace.owner_id != current_user.id:
        role = get_user_role_in_workspace(session, current_user.id, workspace.id)
        if role != MemberRole.admin:
            raise HTTPException(status_code=403, detail="Only owner or admin can delete board")
    
    board.is_deleted = True
    board.deleted_at = datetime.utcnow()
    board.deleted_by = str(current_user.id)
    session.add(board)
    session.commit()
    return Message(message="Board deleted successfully")