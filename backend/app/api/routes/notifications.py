"""
Notifications API Routes - Clean routes without direct database queries.
"""
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, SessionDep
from app.models.auth import Message
from app.models.notifications import (
    NotificationPublic,
    NotificationsPublic,
)
from app.repository import notifications as notifications_repo

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/", response_model=NotificationsPublic)
def read_notifications(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 50,
    unread_only: bool = False,
) -> Any:
    """Get current user's notifications."""
    notifications, count, unread_count = notifications_repo.get_user_notifications(
        session=session,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        unread_only=unread_only
    )

    return NotificationsPublic(data=notifications, count=count, unread_count=unread_count)


@router.get("/unread-count")
def get_unread_count(session: SessionDep, current_user: CurrentUser) -> dict:
    """Get count of unread notifications."""
    count = notifications_repo.get_unread_count(session=session, user_id=current_user.id)
    return {"unread_count": count}


@router.get("/{id}", response_model=NotificationPublic)
def read_notification(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Any:
    """Get a specific notification."""
    notification = notifications_repo.get_notification_by_id(session=session, notification_id=id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    if notification.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your notification")
    return notification


@router.put("/{id}/read", response_model=NotificationPublic)
def mark_as_read(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Any:
    """Mark a notification as read."""
    notification = notifications_repo.get_notification_by_id(session=session, notification_id=id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    if notification.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your notification")

    notification = notifications_repo.mark_as_read(session=session, notification=notification)
    return notification


@router.put("/read-all")
def mark_all_as_read(session: SessionDep, current_user: CurrentUser) -> Message:
    """Mark all notifications as read."""
    count = notifications_repo.mark_all_as_read(session=session, user_id=current_user.id)
    return Message(message=f"Marked {count} notifications as read")


@router.delete("/{id}")
def delete_notification(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Message:
    """Delete a notification."""
    notification = notifications_repo.get_notification_by_id(session=session, notification_id=id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    if notification.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your notification")

    notifications_repo.delete_notification(session=session, notification=notification)
    return Message(message="Notification deleted")
