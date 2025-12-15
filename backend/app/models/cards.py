from __future__ import annotations

from sqlmodel import SQLModel, Field
from datetime import datetime
import uuid
from typing import TYPE_CHECKING, List
from pydantic import field_validator

from app.core.sanitization import sanitize_plain_text, sanitize_html, sanitize_url
from app.models.mixins import SoftDeleteMixin

if TYPE_CHECKING:
    from app.models.lists import BoardList
    from app.models.checklists import ChecklistItem
    from app.models.comments import CardComment


class CardBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None)
    position: float = Field(default=65535.0)
    due_date: datetime | None = None
    is_archived: bool = False
    cover_image: str | None = None

    @field_validator('title', mode='before')
    @classmethod
    def sanitize_title(cls, v: str | None) -> str | None:
        return sanitize_plain_text(v)

    @field_validator('description', mode='before')
    @classmethod
    def sanitize_description(cls, v: str | None) -> str | None:
        return sanitize_html(v)

    @field_validator('cover_image', mode='before')
    @classmethod
    def sanitize_cover_image(cls, v: str | None) -> str | None:
        return sanitize_url(v)


class CardCreate(CardBase):
    list_id: uuid.UUID


class CardUpdate(SQLModel):
    title: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None)
    position: float | None = None
    list_id: uuid.UUID | None = None
    due_date: datetime | None = None
    is_archived: bool | None = None
    cover_image: str | None = None


class Card(CardBase, SoftDeleteMixin, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    list_id: uuid.UUID = Field(foreign_key="board_list.id", ondelete="CASCADE")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CardPublic(CardBase):
    id: uuid.UUID
    list_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    is_deleted: bool = False


class CardsPublic(SQLModel):
    data: list[CardPublic]
    count: int