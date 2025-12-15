from __future__ import annotations

from sqlmodel import SQLModel, Field
from datetime import datetime
import uuid
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from app.models.cards import Card


class CardCommentBase(SQLModel):
    content: str = Field(min_length=1, max_length=5000)


class CardCommentCreate(CardCommentBase):
    card_id: uuid.UUID


class CardCommentUpdate(SQLModel):
    content: str | None = Field(default=None, max_length=5000)


class CardComment(CardCommentBase, table=True):
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


class CardCommentsPublic(SQLModel):
    data: list[CardCommentPublic]
    count: int
