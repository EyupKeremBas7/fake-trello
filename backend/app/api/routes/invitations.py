"""
Invitations API Routes - Clean routes without direct database queries.
"""
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, SessionDep
from app.repository import invitations as invitations_repo
from app.models.invitations import (
    WorkspaceInvitation,
    WorkspaceInvitationCreate,
    WorkspaceInvitationPublic,
    WorkspaceInvitationWithDetails,
    WorkspaceInvitationsPublic,
    WorkspaceInvitationRespond,
    InvitationStatus,
)
from app.models.notifications import Notification, NotificationType
from app.models.auth import Message

router = APIRouter(prefix="/invitations", tags=["invitations"])


@router.get("/", response_model=list[WorkspaceInvitationWithDetails])
def read_my_invitations(
    session: SessionDep,
    current_user: CurrentUser,
    status: InvitationStatus | None = None,
) -> Any:
    """Get all invitations sent to current user."""
    invitations = invitations_repo.get_invitations_for_user(
        session=session, user_id=current_user.id, status=status
    )
    
    # Enrich with workspace and inviter details
    result = []
    for inv in invitations:
        workspace = invitations_repo.get_workspace_by_id(session=session, workspace_id=inv.workspace_id)
        inviter = invitations_repo.get_user_by_id(session=session, user_id=inv.inviter_id)
        
        result.append(WorkspaceInvitationWithDetails(
            id=inv.id,
            workspace_id=inv.workspace_id,
            inviter_id=inv.inviter_id,
            invitee_id=inv.invitee_id,
            role=inv.role,
            status=inv.status,
            message=inv.message,
            created_at=inv.created_at,
            responded_at=inv.responded_at,
            expires_at=inv.expires_at,
            workspace_name=workspace.name if workspace else "Unknown",
            inviter_name=inviter.full_name or inviter.email if inviter else "Unknown",
            inviter_email=inviter.email if inviter else "Unknown",
        ))
    
    return result


@router.get("/sent", response_model=WorkspaceInvitationsPublic)
def read_sent_invitations(
    session: SessionDep,
    current_user: CurrentUser,
    workspace_id: uuid.UUID | None = None,
) -> Any:
    """Get all invitations sent by current user."""
    invitations = invitations_repo.get_sent_invitations(
        session=session, user_id=current_user.id, workspace_id=workspace_id
    )
    
    return WorkspaceInvitationsPublic(data=invitations, count=len(invitations))


@router.post("/", response_model=WorkspaceInvitationPublic)
def create_invitation(
    session: SessionDep,
    current_user: CurrentUser,
    invitation_in: WorkspaceInvitationCreate,
) -> Any:
    """Send a workspace invitation to a user."""
    # Check workspace exists
    workspace = invitations_repo.get_workspace_by_id(session=session, workspace_id=invitation_in.workspace_id)
    if not workspace or workspace.is_deleted:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # Check permission - must be owner or admin
    role = invitations_repo.get_user_role_in_workspace(
        session=session, user_id=current_user.id, workspace_id=workspace.id
    )
    if role not in ["owner", "admin"] and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Only workspace owner or admin can invite members")
    
    # Find invitee
    invitee = None
    if invitation_in.invitee_id:
        invitee = invitations_repo.get_user_by_id(session=session, user_id=invitation_in.invitee_id)
    elif invitation_in.invitee_email:
        invitee = invitations_repo.get_user_by_email(session=session, email=invitation_in.invitee_email)
    
    if not invitee:
        raise HTTPException(
            status_code=404,
            detail="User not found. They need to register first."
        )
    
    # Can't invite yourself
    if invitee.id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot invite yourself")
    
    # Can't invite the owner
    if invitee.id == workspace.owner_id:
        raise HTTPException(status_code=400, detail="Cannot invite the workspace owner")
    
    # Check if already a member
    existing_member = invitations_repo.get_member_by_user_and_workspace(
        session=session, user_id=invitee.id, workspace_id=workspace.id
    )
    if existing_member:
        raise HTTPException(status_code=400, detail="User is already a member of this workspace")
    
    # Check if there's already a pending invitation
    existing_invitation = invitations_repo.get_pending_invitation(
        session=session, invitee_id=invitee.id, workspace_id=workspace.id
    )
    if existing_invitation:
        raise HTTPException(status_code=400, detail="There's already a pending invitation for this user")
    
    # Create invitation
    invitation = invitations_repo.create_invitation(
        session=session,
        workspace_id=workspace.id,
        inviter_id=current_user.id,
        invitee_id=invitee.id,
        role=invitation_in.role,
        message=invitation_in.message
    )
    
    # Create notification for invitee
    notification = Notification(
        user_id=invitee.id,
        type=NotificationType.workspace_invitation,
        title="Workspace Invitation",
        message=f"{current_user.full_name or current_user.email} invited you to join '{workspace.name}'",
        reference_id=invitation.id,
        reference_type="invitation",
    )
    session.add(notification)
    session.commit()
    
    return invitation


@router.post("/{id}/respond", response_model=WorkspaceInvitationPublic)
def respond_to_invitation(
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    response: WorkspaceInvitationRespond,
) -> Any:
    """Accept or reject an invitation."""
    invitation = invitations_repo.get_invitation_by_id(session=session, invitation_id=id)
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")
    
    # Only the invitee can respond
    if invitation.invitee_id != current_user.id:
        raise HTTPException(status_code=403, detail="This invitation is not for you")
    
    # Check if already responded
    if invitation.status != InvitationStatus.pending:
        raise HTTPException(
            status_code=400,
            detail=f"Invitation already {invitation.status.value}"
        )
    
    # Get workspace for notification
    workspace = invitations_repo.get_workspace_by_id(session=session, workspace_id=invitation.workspace_id)
    
    if response.accept:
        # Accept invitation - add user to workspace
        invitation = invitations_repo.respond_to_invitation(
            session=session, invitation=invitation, accept=True
        )
        
        # Create workspace member
        invitations_repo.add_workspace_member(
            session=session,
            user_id=current_user.id,
            workspace_id=invitation.workspace_id,
            role=invitation.role
        )
        
        # Notify inviter
        notification = Notification(
            user_id=invitation.inviter_id,
            type=NotificationType.invitation_accepted,
            title="Invitation Accepted",
            message=f"{current_user.full_name or current_user.email} accepted your invitation to '{workspace.name}'",
            reference_id=invitation.workspace_id,
            reference_type="workspace",
        )
        session.add(notification)
        session.commit()
    else:
        # Reject invitation
        invitation = invitations_repo.respond_to_invitation(
            session=session, invitation=invitation, accept=False
        )
        
        # Notify inviter
        notification = Notification(
            user_id=invitation.inviter_id,
            type=NotificationType.invitation_rejected,
            title="Invitation Rejected",
            message=f"{current_user.full_name or current_user.email} rejected your invitation to '{workspace.name}'",
            reference_id=invitation.workspace_id,
            reference_type="workspace",
        )
        session.add(notification)
        session.commit()
    
    return invitation


@router.delete("/{id}")
def cancel_invitation(
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
) -> Message:
    """Cancel a pending invitation (by inviter or workspace admin)."""
    invitation = invitations_repo.get_invitation_by_id(session=session, invitation_id=id)
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")
    
    # Check permission
    is_inviter = invitation.inviter_id == current_user.id
    role = invitations_repo.get_user_role_in_workspace(
        session=session, user_id=current_user.id, workspace_id=invitation.workspace_id
    )
    
    if not is_inviter and role not in ["owner", "admin"] and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    if invitation.status != InvitationStatus.pending:
        raise HTTPException(status_code=400, detail="Can only cancel pending invitations")
    
    invitations_repo.delete_invitation(session=session, invitation=invitation)
    
    return Message(message="Invitation cancelled")
