"""
Event Types - Concrete event classes for different actions.
"""
from dataclasses import dataclass
from uuid import UUID

from app.events.base import Event


@dataclass
class CardMovedEvent(Event):
    """Fired when a card is moved to a different list."""
    card_id: UUID
    card_title: str
    old_list_name: str
    new_list_name: str
    moved_by_id: UUID
    moved_by_name: str
    # Owner = card creator, Assignee = assigned person (notifications go to assignee)
    card_owner_id: UUID | None = None
    card_owner_email: str | None = None
    card_assignee_id: UUID | None = None
    card_assignee_email: str | None = None


@dataclass
class CommentAddedEvent(Event):
    """Fired when a comment is added to a card."""
    card_id: UUID
    card_title: str
    comment_content: str
    commenter_id: UUID
    commenter_name: str
    card_owner_id: UUID | None = None
    card_owner_email: str | None = None
    card_assignee_id: UUID | None = None
    card_assignee_email: str | None = None


@dataclass
class ChecklistToggledEvent(Event):
    """Fired when a checklist item is toggled."""
    card_id: UUID
    card_title: str
    item_title: str
    is_completed: bool
    toggled_by_id: UUID
    toggled_by_name: str
    card_owner_id: UUID | None = None
    card_owner_email: str | None = None
    card_assignee_id: UUID | None = None
    card_assignee_email: str | None = None


@dataclass
class CardAssignedEvent(Event):
    """Fired when a card is assigned to someone."""
    card_id: UUID
    card_title: str
    assigned_by_id: UUID
    assigned_by_name: str
    assignee_id: UUID
    assignee_email: str


@dataclass
class InvitationSentEvent(Event):
    """Fired when a workspace invitation is sent."""
    invitation_id: UUID
    workspace_id: UUID
    workspace_name: str
    inviter_id: UUID
    inviter_name: str
    invitee_id: UUID
    invitee_email: str


@dataclass
class InvitationRespondedEvent(Event):
    """Fired when an invitation is accepted or rejected."""
    invitation_id: UUID
    workspace_id: UUID
    workspace_name: str
    accepted: bool
    responder_id: UUID
    responder_name: str
    inviter_id: UUID

@dataclass
class WelcomeEmailSentEvent(Event):
    """Fired when a welcome email is sent."""
    user_id: UUID
    user_email: str

