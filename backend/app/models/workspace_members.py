import uuid
from datetime import datetime
from sqlmodel import Field, SQLModel
from typing import TYPE_CHECKING

from app.models.enums import MemberRole

if TYPE_CHECKING:
    from app.models.users import User
    from app.models.workspaces import Workspace


class WorkspaceMemberBase(SQLModel):
    role: MemberRole = Field(default=MemberRole.member)


class WorkspaceMemberCreate(SQLModel):
    user_id: uuid.UUID
    workspace_id: uuid.UUID
    role: MemberRole = MemberRole.member


class WorkspaceMemberUpdate(SQLModel):
    role: MemberRole | None = None


class WorkspaceInvite(SQLModel):
    email: str
    role: MemberRole = MemberRole.member


class WorkspaceMember(WorkspaceMemberBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    workspace_id: uuid.UUID = Field(foreign_key="workspace.id", nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class WorkspaceMemberPublic(WorkspaceMemberBase):
    id: uuid.UUID
    user_id: uuid.UUID
    workspace_id: uuid.UUID
    created_at: datetime


class WorkspaceMembersPublic(SQLModel):
    data: list[WorkspaceMemberPublic]
    count: int