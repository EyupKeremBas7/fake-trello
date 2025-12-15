from __future__ import annotations

from sqlmodel import SQLModel, Field
from datetime import datetime
import uuid
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from app.models.cards import Card


class ChecklistItemBase(SQLModel):
    title: str = Field(min_length=1, max_length=500)
    is_completed: bool = False
    position: float = Field(default=65535.0)


class ChecklistItemCreate(ChecklistItemBase):
    card_id: uuid.UUID


class ChecklistItemUpdate(SQLModel):
    title: str | None = Field(default=None, max_length=500)
    is_completed: bool | None = None
    position: float | None = None


class ChecklistItem(ChecklistItemBase, table=True):
    __tablename__ = "checklist_item"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    card_id: uuid.UUID = Field(foreign_key="card.id", ondelete="CASCADE")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ChecklistItemPublic(ChecklistItemBase):
    id: uuid.UUID
    card_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class ChecklistItemsPublic(SQLModel):
    data: list[ChecklistItemPublic]
    count: int
