from __future__ import annotations

from sqlmodel import SQLModel, Field
from datetime import datetime
import uuid
from enum import Enum
from typing import TYPE_CHECKING

from app.models.enums import MemberRole

if TYPE_CHECKING:
    from app.models.users import User
    from app.models.workspaces import Workspace


class InvitationStatus(str, Enum):
    """Status of workspace invitation"""
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"
    expired = "expired"


class WorkspaceInvitationBase(SQLModel):
    role: MemberRole = Field(default=MemberRole.member)
    status: InvitationStatus = Field(default=InvitationStatus.pending)
    message: str | None = Field(default=None, max_length=500)  # Optional invitation message


class WorkspaceInvitationCreate(SQLModel):
    """Create invitation by email or user_id"""
    workspace_id: uuid.UUID
    invitee_email: str | None = None  # Invite by email
    invitee_id: uuid.UUID | None = None  # Or invite by user_id
    role: MemberRole = MemberRole.member
    message: str | None = None


class WorkspaceInvitationRespond(SQLModel):
    """Accept or reject an invitation"""
    accept: bool


class WorkspaceInvitation(WorkspaceInvitationBase, table=True):
    __tablename__ = "workspace_invitation"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    workspace_id: uuid.UUID = Field(foreign_key="workspace.id", ondelete="CASCADE", index=True)
    inviter_id: uuid.UUID = Field(foreign_key="user.id", ondelete="CASCADE")  # Who sent the invite
    invitee_id: uuid.UUID = Field(foreign_key="user.id", ondelete="CASCADE", index=True)  # Who receives
    created_at: datetime = Field(default_factory=datetime.utcnow)
    responded_at: datetime | None = Field(default=None)
    expires_at: datetime | None = Field(default=None)  # Optional expiration


class WorkspaceInvitationPublic(WorkspaceInvitationBase):
    id: uuid.UUID
    workspace_id: uuid.UUID
    inviter_id: uuid.UUID
    invitee_id: uuid.UUID
    created_at: datetime
    responded_at: datetime | None
    expires_at: datetime | None


class WorkspaceInvitationWithDetails(WorkspaceInvitationPublic):
    """Invitation with workspace and inviter names for display"""
    workspace_name: str
    inviter_name: str
    inviter_email: str


class WorkspaceInvitationsPublic(SQLModel):
    data: list[WorkspaceInvitationPublic]
    count: int
