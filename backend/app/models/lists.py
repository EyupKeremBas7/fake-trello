import uuid
from typing import TYPE_CHECKING

from pydantic import field_validator
from sqlmodel import Field, SQLModel

from app.core.sanitization import sanitize_plain_text
from app.models.mixins import SoftDeleteMixin

if TYPE_CHECKING:
    pass


class ListBase(SQLModel):
    name: str = Field(min_length=1, max_length=100)
    position: float = Field(default=65535.0)
    is_archived: bool = False

    @field_validator('name', mode='before')
    @classmethod
    def sanitize_name(cls, v: str | None) -> str | None:
        return sanitize_plain_text(v)


class ListCreate(ListBase):
    board_id: uuid.UUID


class ListUpdate(ListBase):
    name: str | None = Field(default=None, max_length=100)
    position: float | None = None


class BoardList(ListBase, SoftDeleteMixin, table=True):
    __tablename__ = "board_list"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    board_id: uuid.UUID = Field(foreign_key="board.id", ondelete="CASCADE")


class ListPublic(ListBase):
    id: uuid.UUID
    board_id: uuid.UUID
    is_deleted: bool = False

class ListsPublic(SQLModel):
    data: list[ListPublic]
    count: int
