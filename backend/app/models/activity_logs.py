"""
Activity Logs Model - Tracking all user actions.
"""
import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import JSON
from sqlmodel import Column, Field, SQLModel


class ActionType(str, Enum):
    """Types of actions that can be logged."""
    created = "created"
    updated = "updated"
    deleted = "deleted"
    moved = "moved"
    archived = "archived"
    restored = "restored"
    completed = "completed"
    assigned = "assigned"
    commented = "commented"
    invited = "invited"
    joined = "joined"
    left = "left"


class EntityType(str, Enum):
    """Types of entities that can be logged."""
    card = "card"
    list = "list"
    board = "board"
    workspace = "workspace"
    comment = "comment"
    checklist_item = "checklist_item"
    member = "member"


class ActivityLog(SQLModel, table=True):
    """Activity log entry for tracking user actions."""
    __tablename__ = "activity_log"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", index=True)
    action: ActionType
    entity_type: EntityType
    entity_id: uuid.UUID = Field(index=True)
    entity_name: str | None = None

    # Context - for board/workspace level filtering
    board_id: uuid.UUID | None = Field(default=None, foreign_key="board.id", index=True)
    workspace_id: uuid.UUID | None = Field(default=None, foreign_key="workspace.id", index=True)

    # JSON field for additional details
    details: dict = Field(default_factory=dict, sa_column=Column(JSON))

    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)


class ActivityLogPublic(SQLModel):
    """Public representation of activity log."""
    id: uuid.UUID
    user_id: uuid.UUID
    action: ActionType
    entity_type: EntityType
    entity_id: uuid.UUID
    entity_name: str | None
    board_id: uuid.UUID | None
    workspace_id: uuid.UUID | None
    details: dict
    created_at: datetime

    # User info (enriched)
    user_full_name: str | None = None
    user_email: str | None = None


class ActivityLogsPublic(SQLModel):
    """List of activity logs."""
    data: list[ActivityLogPublic]
    count: int
