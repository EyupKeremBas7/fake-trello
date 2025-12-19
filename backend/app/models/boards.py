import uuid
from typing import TYPE_CHECKING

from pydantic import field_validator
from sqlmodel import Field, SQLModel

from app.core.sanitization import sanitize_plain_text
from app.models.enums import Visibility
from app.models.mixins import SoftDeleteMixin

if TYPE_CHECKING:
    pass

class BoardBase(SQLModel):
    name: str = Field(min_length=1, max_length=100)
    visibility: Visibility = Field(default=Visibility.workspace)
    background_image: str | None = Field(default=None)
    is_archived: bool = False

    @field_validator('name', mode='before')
    @classmethod
    def sanitize_name(cls, v: str | None) -> str | None:
        return sanitize_plain_text(v)


class BoardCreate(BoardBase):
    workspace_id: uuid.UUID


class BoardUpdate(BoardBase):
    name: str | None = Field(default=None, max_length=100)
    visibility: Visibility | None = None
    background_image: str | None = None


class Board(BoardBase, SoftDeleteMixin, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    workspace_id: uuid.UUID = Field(foreign_key="workspace.id", ondelete="CASCADE")
    owner_id: uuid.UUID = Field(foreign_key="user.id")


class BoardPublic(BoardBase):
    id: uuid.UUID
    workspace_id: uuid.UUID
    owner_id: uuid.UUID
    is_deleted: bool = False

class BoardsPublic(SQLModel):
    data: list[BoardPublic]
    count: int
