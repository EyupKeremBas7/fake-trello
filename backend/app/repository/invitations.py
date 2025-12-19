"""
Invitations Repository - All database operations for WorkspaceInvitation model.
"""
import uuid
from datetime import datetime

from sqlmodel import Session, select

from app.models.enums import MemberRole
from app.models.invitations import (
    InvitationStatus,
    WorkspaceInvitation,
)
from app.models.users import User
from app.models.workspace_members import WorkspaceMember
from app.models.workspaces import Workspace


def get_invitation_by_id(*, session: Session, invitation_id: uuid.UUID) -> WorkspaceInvitation | None:
    """Get invitation by ID."""
    return session.get(WorkspaceInvitation, invitation_id)


def get_workspace_by_id(*, session: Session, workspace_id: uuid.UUID) -> Workspace | None:
    """Get workspace by ID."""
    return session.get(Workspace, workspace_id)


def get_user_by_id(*, session: Session, user_id: uuid.UUID) -> User | None:
    """Get user by ID."""
    return session.get(User, user_id)


def get_user_by_email(*, session: Session, email: str) -> User | None:
    """Get user by email."""
    return session.exec(
        select(User).where(
            User.email == email,
            User.is_deleted == False
        )
    ).first()


def get_user_role_in_workspace(
    *, session: Session, user_id: uuid.UUID, workspace_id: uuid.UUID
) -> str | None:
    """Check if user has admin access to workspace."""
    workspace = session.get(Workspace, workspace_id)
    if not workspace:
        return None
    if workspace.owner_id == user_id:
        return "owner"
    member = session.exec(
        select(WorkspaceMember).where(
            WorkspaceMember.user_id == user_id,
            WorkspaceMember.workspace_id == workspace_id
        )
    ).first()
    return member.role if member else None


def get_invitations_for_user(
    *, session: Session, user_id: uuid.UUID, status: InvitationStatus | None = None
) -> list[WorkspaceInvitation]:
    """Get all invitations sent to a user."""
    query = select(WorkspaceInvitation).where(
        WorkspaceInvitation.invitee_id == user_id
    )

    if status:
        query = query.where(WorkspaceInvitation.status == status)
    else:
        # By default, show pending invitations
        query = query.where(WorkspaceInvitation.status == InvitationStatus.pending)

    invitations = session.exec(query.order_by(WorkspaceInvitation.created_at.desc())).all()
    return list(invitations)


def get_sent_invitations(
    *, session: Session, user_id: uuid.UUID, workspace_id: uuid.UUID | None = None
) -> list[WorkspaceInvitation]:
    """Get all invitations sent by a user."""
    query = select(WorkspaceInvitation).where(
        WorkspaceInvitation.inviter_id == user_id
    )

    if workspace_id:
        query = query.where(WorkspaceInvitation.workspace_id == workspace_id)

    invitations = session.exec(query.order_by(WorkspaceInvitation.created_at.desc())).all()
    return list(invitations)


def get_member_by_user_and_workspace(
    *, session: Session, user_id: uuid.UUID, workspace_id: uuid.UUID
) -> WorkspaceMember | None:
    """Get workspace member by user_id and workspace_id."""
    return session.exec(
        select(WorkspaceMember).where(
            WorkspaceMember.user_id == user_id,
            WorkspaceMember.workspace_id == workspace_id
        )
    ).first()


def get_pending_invitation(
    *, session: Session, invitee_id: uuid.UUID, workspace_id: uuid.UUID
) -> WorkspaceInvitation | None:
    """Get pending invitation for a user and workspace."""
    return session.exec(
        select(WorkspaceInvitation).where(
            WorkspaceInvitation.invitee_id == invitee_id,
            WorkspaceInvitation.workspace_id == workspace_id,
            WorkspaceInvitation.status == InvitationStatus.pending
        )
    ).first()


def create_invitation(
    *, session: Session,
    workspace_id: uuid.UUID,
    inviter_id: uuid.UUID,
    invitee_id: uuid.UUID,
    role: MemberRole,
    message: str | None = None
) -> WorkspaceInvitation:
    """Create a new invitation."""
    invitation = WorkspaceInvitation(
        workspace_id=workspace_id,
        inviter_id=inviter_id,
        invitee_id=invitee_id,
        role=role,
        message=message,
        status=InvitationStatus.pending,
    )
    session.add(invitation)
    session.commit()
    session.refresh(invitation)
    return invitation


def respond_to_invitation(
    *, session: Session, invitation: WorkspaceInvitation, accept: bool
) -> WorkspaceInvitation:
    """Accept or reject an invitation."""
    if accept:
        invitation.status = InvitationStatus.accepted
    else:
        invitation.status = InvitationStatus.rejected

    invitation.responded_at = datetime.utcnow()
    session.add(invitation)
    session.commit()
    session.refresh(invitation)
    return invitation


def add_workspace_member(
    *, session: Session, user_id: uuid.UUID, workspace_id: uuid.UUID, role: MemberRole
) -> WorkspaceMember:
    """Add a member to workspace."""
    member = WorkspaceMember(
        user_id=user_id,
        workspace_id=workspace_id,
        role=role,
    )
    session.add(member)
    session.commit()
    session.refresh(member)
    return member


def delete_invitation(*, session: Session, invitation: WorkspaceInvitation) -> None:
    """Delete an invitation."""
    session.delete(invitation)
    session.commit()
