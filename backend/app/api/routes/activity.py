"""
Activity Logs API Routes - Clean routes for activity tracking.
"""
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, SessionDep
from app.repository import activity_logs as activity_repo
from app.models.activity_logs import ActivityLogsPublic

router = APIRouter(prefix="/activity", tags=["activity"])


@router.get("/board/{board_id}", response_model=ActivityLogsPublic)
def get_board_activity(
    session: SessionDep,
    current_user: CurrentUser,
    board_id: uuid.UUID,
    skip: int = 0,
    limit: int = 50,
) -> Any:
    """Get activity logs for a specific board."""
    logs, count = activity_repo.get_board_activity(
        session=session, board_id=board_id, skip=skip, limit=limit
    )
    
    enriched_logs = [activity_repo.enrich_activity_log(session, log) for log in logs]
    
    return ActivityLogsPublic(data=enriched_logs, count=count)


@router.get("/workspace/{workspace_id}", response_model=ActivityLogsPublic)
def get_workspace_activity(
    session: SessionDep,
    current_user: CurrentUser,
    workspace_id: uuid.UUID,
    skip: int = 0,
    limit: int = 50,
) -> Any:
    """Get activity logs for a specific workspace."""
    logs, count = activity_repo.get_workspace_activity(
        session=session, workspace_id=workspace_id, skip=skip, limit=limit
    )
    
    enriched_logs = [activity_repo.enrich_activity_log(session, log) for log in logs]
    
    return ActivityLogsPublic(data=enriched_logs, count=count)


@router.get("/card/{card_id}", response_model=ActivityLogsPublic)
def get_card_activity(
    session: SessionDep,
    current_user: CurrentUser,
    card_id: uuid.UUID,
    skip: int = 0,
    limit: int = 50,
) -> Any:
    """Get activity logs for a specific card."""
    logs, count = activity_repo.get_card_activity(
        session=session, card_id=card_id, skip=skip, limit=limit
    )
    
    enriched_logs = [activity_repo.enrich_activity_log(session, log) for log in logs]
    
    return ActivityLogsPublic(data=enriched_logs, count=count)
