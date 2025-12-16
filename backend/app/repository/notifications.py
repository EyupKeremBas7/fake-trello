"""
Notifications Repository - All database operations for Notification model.
"""
import uuid
from typing import Any

from sqlmodel import Session, select, func

from app.models.notifications import Notification, NotificationType


def get_notification_by_id(*, session: Session, notification_id: uuid.UUID) -> Notification | None:
    """Get notification by ID."""
    return session.get(Notification, notification_id)


def get_user_notifications(
    *, session: Session, user_id: uuid.UUID, skip: int = 0, limit: int = 50, unread_only: bool = False
) -> tuple[list[Notification], int, int]:
    """Get notifications for a user with count and unread count."""
    # Base query
    base_query = select(Notification).where(Notification.user_id == user_id)
    
    if unread_only:
        base_query = base_query.where(Notification.is_read == False)
    
    # Get total count
    count = session.exec(
        select(func.count()).select_from(Notification).where(Notification.user_id == user_id)
    ).one()
    
    # Get unread count
    unread_count = session.exec(
        select(func.count()).select_from(Notification).where(
            Notification.user_id == user_id,
            Notification.is_read == False
        )
    ).one()
    
    # Get notifications ordered by newest first
    notifications = session.exec(
        base_query.order_by(Notification.created_at.desc()).offset(skip).limit(limit)
    ).all()
    
    return list(notifications), count, unread_count


def get_unread_count(*, session: Session, user_id: uuid.UUID) -> int:
    """Get count of unread notifications for a user."""
    count = session.exec(
        select(func.count()).select_from(Notification).where(
            Notification.user_id == user_id,
            Notification.is_read == False
        )
    ).one()
    return count


def get_unread_notifications(*, session: Session, user_id: uuid.UUID) -> list[Notification]:
    """Get all unread notifications for a user."""
    notifications = session.exec(
        select(Notification).where(
            Notification.user_id == user_id,
            Notification.is_read == False
        )
    ).all()
    return list(notifications)


def create_notification(
    *, session: Session,
    user_id: uuid.UUID,
    notification_type: NotificationType,
    title: str,
    message: str,
    reference_id: uuid.UUID | None = None,
    reference_type: str | None = None,
) -> Notification:
    """Create a new notification."""
    notification = Notification(
        user_id=user_id,
        type=notification_type,
        title=title,
        message=message,
        reference_id=reference_id,
        reference_type=reference_type,
    )
    session.add(notification)
    session.commit()
    session.refresh(notification)
    return notification


def mark_as_read(*, session: Session, notification: Notification) -> Notification:
    """Mark a notification as read."""
    notification.is_read = True
    session.add(notification)
    session.commit()
    session.refresh(notification)
    return notification


def mark_all_as_read(*, session: Session, user_id: uuid.UUID) -> int:
    """Mark all notifications as read for a user. Returns count of marked notifications."""
    notifications = get_unread_notifications(session=session, user_id=user_id)
    
    for notification in notifications:
        notification.is_read = True
        session.add(notification)
    
    session.commit()
    return len(notifications)


def delete_notification(*, session: Session, notification: Notification) -> None:
    """Delete a notification."""
    session.delete(notification)
    session.commit()
