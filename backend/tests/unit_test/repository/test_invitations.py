import uuid
from unittest.mock import Mock, patch
from app.repository import invitations as invitations_repo
from app.models.invitations import WorkspaceInvitation, InvitationStatus
from app.models.enums import MemberRole
from app.models.users import User

class TestCreateInvitation:
    def test_create_invitation_with_email(self, mock_session):
        """Test creating invitation when email is provided."""
        workspace_id = uuid.uuid4()
        inviter_id = uuid.uuid4()
        invitee_id = uuid.uuid4()
        email = "test@example.com"
        
        invitation = invitations_repo.create_invitation(
            session=mock_session,
            workspace_id=workspace_id,
            inviter_id=inviter_id,
            invitee_id=invitee_id,
            role=MemberRole.member,
            invitee_email=email
        )
        
        assert invitation.invitee_email == email
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()

    def test_create_invitation_populates_email(self, mock_session):
        """Test creating invitation without email populates it from user."""
        workspace_id = uuid.uuid4()
        inviter_id = uuid.uuid4()
        invitee_id = uuid.uuid4()
        email = "user@example.com"
        
        # Mock user found in DB
        mock_user = Mock(spec=User)
        mock_user.email = email
        mock_user.id = invitee_id
        mock_session.get.return_value = mock_user
        
        invitation = invitations_repo.create_invitation(
            session=mock_session,
            workspace_id=workspace_id,
            inviter_id=inviter_id,
            invitee_id=invitee_id,
            role=MemberRole.member,
            invitee_email=None  # Logic should fetch it
        )
        
        assert invitation.invitee_email == email
        mock_session.get.assert_called_with(User, invitee_id)
        mock_session.add.assert_called_once()
