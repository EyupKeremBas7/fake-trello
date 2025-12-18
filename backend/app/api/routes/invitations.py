"""
Invitations API Routes - Clean routes without direct database queries.
"""
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, SessionDep
from app.repository import invitations as invitations_repo
from app.repository import notifications as notifications_repo
from app.models.invitations import (
    WorkspaceInvitation,
    WorkspaceInvitationCreate,
    WorkspaceInvitationPublic,
    WorkspaceInvitationWithDetails,
    WorkspaceInvitationsPublic,
    WorkspaceInvitationRespond,
    InvitationStatus,
)
from app.models.notifications import NotificationType
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
    workspace = invitations_repo.get_workspace_by_id(session=session, workspace_id=invitation_in.workspace_id)
    if not workspace or workspace.is_deleted:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    role = invitations_repo.get_user_role_in_workspace(
        session=session, user_id=current_user.id, workspace_id=workspace.id
    )
    if role not in ["owner", "admin"] and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Only workspace owner or admin can invite members")
    
    
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
    
    if invitee.id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot invite yourself")
    
    if invitee.id == workspace.owner_id:
        raise HTTPException(status_code=400, detail="Cannot invite the workspace owner")
    
    existing_member = invitations_repo.get_member_by_user_and_workspace(
        session=session, user_id=invitee.id, workspace_id=workspace.id
    )
    if existing_member:
        raise HTTPException(status_code=400, detail="User is already a member of this workspace")
    
    existing_invitation = invitations_repo.get_pending_invitation(
        session=session, invitee_id=invitee.id, workspace_id=workspace.id
    )
    if existing_invitation:
        raise HTTPException(status_code=400, detail="There's already a pending invitation for this user")
    
    invitation = invitations_repo.create_invitation(
        session=session,
        workspace_id=workspace.id,
        inviter_id=current_user.id,
        invitee_id=invitee.id,
        role=invitation_in.role,
        message=invitation_in.message
    )
    
    # Dispatch InvitationSentEvent (Observer pattern)
    from app.events import EventDispatcher, InvitationSentEvent
    EventDispatcher.dispatch(InvitationSentEvent(
        invitation_id=invitation.id,
        workspace_id=workspace.id,
        workspace_name=workspace.name,
        inviter_id=current_user.id,
        inviter_name=current_user.full_name or current_user.email,
        invitee_id=invitee.id,
        invitee_email=invitee.email,
    ))
    
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
    
    if invitation.invitee_id != current_user.id:
        raise HTTPException(status_code=403, detail="This invitation is not for you")
    
    if invitation.status != InvitationStatus.pending:
        raise HTTPException(
            status_code=400,
            detail=f"Invitation already {invitation.status.value}"
        )
    
    workspace = invitations_repo.get_workspace_by_id(session=session, workspace_id=invitation.workspace_id)
    
    if response.accept:
        invitation = invitations_repo.respond_to_invitation(
            session=session, invitation=invitation, accept=True
        )
        
        invitations_repo.add_workspace_member(
            session=session,
            user_id=current_user.id,
            workspace_id=invitation.workspace_id,
            role=invitation.role
        )
    else:
        invitation = invitations_repo.respond_to_invitation(
            session=session, invitation=invitation, accept=False
        )
    
    # Dispatch InvitationRespondedEvent (Observer pattern)
    from app.events import EventDispatcher, InvitationRespondedEvent
    EventDispatcher.dispatch(InvitationRespondedEvent(
        invitation_id=invitation.id,
        workspace_id=invitation.workspace_id,
        workspace_name=workspace.name,
        accepted=response.accept,
        responder_id=current_user.id,
        responder_name=current_user.full_name or current_user.email,
        inviter_id=invitation.inviter_id,
    ))
    
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
