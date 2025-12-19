import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import field_validator
from sqlmodel import Field, SQLModel

from app.core.sanitization import sanitize_html, sanitize_plain_text
from app.models.mixins import SoftDeleteMixin

if TYPE_CHECKING:
    pass


class WorkspaceBase(SQLModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    is_archived: bool = False

    @field_validator('name', mode='before')
    @classmethod
    def sanitize_name(cls, v: str | None) -> str | None:
        return sanitize_plain_text(v)

    @field_validator('description', mode='before')
    @classmethod
    def sanitize_description(cls, v: str | None) -> str | None:
        return sanitize_html(v)


class WorkspaceCreate(WorkspaceBase):
    pass


class WorkspaceUpdate(SQLModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    is_archived: bool | None = None


class Workspace(WorkspaceBase, SoftDeleteMixin, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)



class WorkspacePublic(WorkspaceBase):
    id: uuid.UUID
    owner_id: uuid.UUID
    created_at: datetime
    is_deleted: bool = False


class WorkspacesPublic(SQLModel):
    data: list[WorkspacePublic]
    count: int
