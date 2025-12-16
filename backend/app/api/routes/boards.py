"""
Boards API Routes - Clean routes without direct database queries.
"""
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, SessionDep
from app.repository import boards as boards_repo
from app.models.boards import Board, BoardCreate, BoardPublic, BoardsPublic, BoardUpdate
from app.models.enums import MemberRole
from app.models.auth import Message

router = APIRouter(prefix="/boards", tags=["boards"])


@router.get("/", response_model=BoardsPublic)
def read_boards(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    if current_user.is_superuser:
        boards, count = boards_repo.get_boards_superuser(
            session=session, skip=skip, limit=limit
        )
    else:
        boards, count = boards_repo.get_boards_for_user(
            session=session, user_id=current_user.id, skip=skip, limit=limit
        )

    return BoardsPublic(data=boards, count=count)


@router.get("/{id}", response_model=BoardPublic)
def read_board(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> Any:
    board = boards_repo.get_board_by_id(session=session, board_id=id)
    if not board or board.is_deleted:
        raise HTTPException(status_code=404, detail="Board not found")
    if not current_user.is_superuser and not boards_repo.can_access_board(
        session=session, user_id=current_user.id, board=board
    ):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return board


@router.post("/", response_model=BoardPublic)
def create_board(
    *, session: SessionDep, current_user: CurrentUser, board_in: BoardCreate
) -> Any:
    workspace = boards_repo.get_workspace_by_id(session=session, workspace_id=board_in.workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    if workspace.owner_id != current_user.id:
        role = boards_repo.get_user_role_in_workspace(
            session=session, user_id=current_user.id, workspace_id=workspace.id
        )
        if role not in [MemberRole.admin, MemberRole.member]:
            raise HTTPException(status_code=403, detail="Not enough permissions to create board")
    
    board = boards_repo.create_board(
        session=session, board_in=board_in, owner_id=current_user.id
    )
    return board


@router.put("/{id}", response_model=BoardPublic)
def update_board(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    board_in: BoardUpdate,
) -> Any:
    board = boards_repo.get_board_by_id(session=session, board_id=id)
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    if not current_user.is_superuser and not boards_repo.can_edit_board(
        session=session, user_id=current_user.id, board=board
    ):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    board = boards_repo.update_board(session=session, board=board, board_in=board_in)
    return board


@router.delete("/{id}")
def delete_board(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Message:
    board = boards_repo.get_board_by_id(session=session, board_id=id)
    if not board or board.is_deleted:
        raise HTTPException(status_code=404, detail="Board not found")
    
    workspace = boards_repo.get_workspace_by_id(session=session, workspace_id=board.workspace_id)
    if not current_user.is_superuser and workspace.owner_id != current_user.id:
        role = boards_repo.get_user_role_in_workspace(
            session=session, user_id=current_user.id, workspace_id=workspace.id
        )
        if role != MemberRole.admin:
            raise HTTPException(status_code=403, detail="Only owner or admin can delete board")
    
    boards_repo.soft_delete_board(session=session, board=board, deleted_by=current_user.id)
    return Message(message="Board deleted successfully")