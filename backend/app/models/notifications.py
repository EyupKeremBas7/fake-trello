from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlmodel import Field, SQLModel

if TYPE_CHECKING:
    pass


class NotificationType(str, Enum):
    """Types of notifications"""
    workspace_invitation = "workspace_invitation"
    invitation_accepted = "invitation_accepted"
    invitation_rejected = "invitation_rejected"
    comment_added = "comment_added"
    card_assigned = "card_assigned"
    card_due_soon = "card_due_soon"
    mentioned = "mentioned"
    card_moved = "card_moved"
    checklist_toggled = "checklist_toggled"


class NotificationBase(SQLModel):
    type: NotificationType
    title: str = Field(max_length=255)
    message: str = Field(max_length=1000)
    is_read: bool = Field(default=False)
    # Reference IDs for navigation
    reference_id: uuid.UUID | None = None  # e.g., invitation_id, card_id
    reference_type: str | None = None  # e.g., "invitation", "card", "comment"


class NotificationCreate(SQLModel):
    user_id: uuid.UUID
    type: NotificationType
    title: str
    message: str
    reference_id: uuid.UUID | None = None
    reference_type: str | None = None


class Notification(NotificationBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", ondelete="CASCADE", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class NotificationPublic(NotificationBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime


class NotificationsPublic(SQLModel):
    data: list[NotificationPublic]
    count: int
    unread_count: int
