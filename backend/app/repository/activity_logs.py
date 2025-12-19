"""
Activity Logs Repository - All database operations for ActivityLog model.
"""
import uuid

from sqlmodel import Session, func, select

from app.models.activity_logs import (
    ActionType,
    ActivityLog,
    ActivityLogPublic,
    EntityType,
)
from app.models.users import User


def create_activity_log(
    *,
    session: Session,
    user_id: uuid.UUID,
    action: ActionType,
    entity_type: EntityType,
    entity_id: uuid.UUID,
    entity_name: str | None = None,
    board_id: uuid.UUID | None = None,
    workspace_id: uuid.UUID | None = None,
    details: dict | None = None,
) -> ActivityLog:
    """Create a new activity log entry."""
    log = ActivityLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        entity_name=entity_name,
        board_id=board_id,
        workspace_id=workspace_id,
        details=details or {},
    )
    session.add(log)
    session.commit()
    session.refresh(log)
    return log


def get_board_activity(
    *,
    session: Session,
    board_id: uuid.UUID,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[ActivityLog], int]:
    """Get activity logs for a specific board."""
    count_stmt = select(func.count()).select_from(ActivityLog).where(
        ActivityLog.board_id == board_id
    )
    count = session.exec(count_stmt).one()

    stmt = (
        select(ActivityLog)
        .where(ActivityLog.board_id == board_id)
        .order_by(ActivityLog.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    logs = session.exec(stmt).all()

    return list(logs), count


def get_workspace_activity(
    *,
    session: Session,
    workspace_id: uuid.UUID,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[ActivityLog], int]:
    """Get activity logs for a specific workspace."""
    count_stmt = select(func.count()).select_from(ActivityLog).where(
        ActivityLog.workspace_id == workspace_id
    )
    count = session.exec(count_stmt).one()

    stmt = (
        select(ActivityLog)
        .where(ActivityLog.workspace_id == workspace_id)
        .order_by(ActivityLog.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    logs = session.exec(stmt).all()

    return list(logs), count


def get_card_activity(
    *,
    session: Session,
    card_id: uuid.UUID,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[ActivityLog], int]:
    """Get activity logs for a specific card."""
    count_stmt = select(func.count()).select_from(ActivityLog).where(
        ActivityLog.entity_type == EntityType.card,
        ActivityLog.entity_id == card_id
    )
    count = session.exec(count_stmt).one()

    stmt = (
        select(ActivityLog)
        .where(
            ActivityLog.entity_type == EntityType.card,
            ActivityLog.entity_id == card_id
        )
        .order_by(ActivityLog.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    logs = session.exec(stmt).all()

    return list(logs), count


def get_user_by_id(*, session: Session, user_id: uuid.UUID) -> User | None:
    """Get user by ID."""
    return session.get(User, user_id)


def enrich_activity_log(session: Session, log: ActivityLog) -> ActivityLogPublic:
    """Enrich activity log with user info."""
    user = get_user_by_id(session=session, user_id=log.user_id)

    return ActivityLogPublic(
        id=log.id,
        user_id=log.user_id,
        action=log.action,
        entity_type=log.entity_type,
        entity_id=log.entity_id,
        entity_name=log.entity_name,
        board_id=log.board_id,
        workspace_id=log.workspace_id,
        details=log.details,
        created_at=log.created_at,
        user_full_name=user.full_name if user else None,
        user_email=user.email if user else None,
    )
