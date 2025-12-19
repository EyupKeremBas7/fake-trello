from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import field_validator
from sqlmodel import Field, SQLModel

from app.core.sanitization import sanitize_html
from app.models.mixins import SoftDeleteMixin

if TYPE_CHECKING:
    pass


class CardCommentBase(SQLModel):
    content: str = Field(min_length=1, max_length=5000)

    @field_validator('content', mode='before')
    @classmethod
    def sanitize_content(cls, v: str | None) -> str | None:
        return sanitize_html(v)


class CardCommentCreate(CardCommentBase):
    card_id: uuid.UUID


class CardCommentUpdate(SQLModel):
    content: str | None = Field(default=None, max_length=5000)


class CardComment(CardCommentBase, SoftDeleteMixin, table=True):
    __tablename__ = "card_comment"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    card_id: uuid.UUID = Field(foreign_key="card.id", ondelete="CASCADE")
    user_id: uuid.UUID = Field(foreign_key="user.id", ondelete="CASCADE")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CardCommentPublic(CardCommentBase):
    id: uuid.UUID
    card_id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    is_deleted: bool = False


class CardCommentsPublic(SQLModel):
    data: list[CardCommentPublic]
    count: int


class CardCommentWithUser(CardCommentPublic):
    user_full_name: str | None = None
    user_email: str | None = None


class CardCommentsWithUserPublic(CardCommentsPublic):
    data: list[CardCommentWithUser]

