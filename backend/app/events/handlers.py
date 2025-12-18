"""
Event Handlers - React to events and perform side effects.

These handlers are registered with EventDispatcher and called when events are dispatched.
This decouples the business logic from notification/email concerns.
"""
import logging
from typing import Union

from app.events.base import Event
from app.events.types import (
    CardMovedEvent,
    CommentAddedEvent,
    ChecklistToggledEvent,
    InvitationSentEvent,
    InvitationRespondedEvent,
)
from app.models.notifications import NotificationType

logger = logging.getLogger(__name__)


NotifiableEvent = Union[
    CardMovedEvent,
    CommentAddedEvent,
    ChecklistToggledEvent,
    InvitationSentEvent,
    InvitationRespondedEvent,
]


def handle_notification(event: NotifiableEvent) -> None:
    """
    Create in-app notification for an event.
    Uses lazy import to avoid circular dependencies.
    """
    from sqlmodel import Session
    from app.core.db import engine
    from app.repository import notifications as notifications_repo
    
    with Session(engine) as session:
        if isinstance(event, CardMovedEvent):
            if event.card_owner_id and event.card_owner_id != event.moved_by_id:
                notifications_repo.create_notification(
                    session=session,
                    user_id=event.card_owner_id,
                    notification_type=NotificationType.card_moved,
                    title="Card Moved",
                    message=f"{event.moved_by_name} moved your card '{event.card_title}' from '{event.old_list_name}' to '{event.new_list_name}'",
                    reference_id=event.card_id,
                    reference_type="card",
                )
                logger.info(f"Notification created for card move: {event.card_id}")
        
        elif isinstance(event, CommentAddedEvent):
            if event.card_owner_id and event.card_owner_id != event.commenter_id:
                notifications_repo.create_notification(
                    session=session,
                    user_id=event.card_owner_id,
                    notification_type=NotificationType.comment_added,
                    title="New Comment",
                    message=f"{event.commenter_name} commented on your card '{event.card_title}'",
                    reference_id=event.card_id,
                    reference_type="card",
                )
                logger.info(f"Notification created for comment: {event.card_id}")
        
        elif isinstance(event, ChecklistToggledEvent):
            if event.card_owner_id and event.card_owner_id != event.toggled_by_id:
                status = "completed" if event.is_completed else "uncompleted"
                notifications_repo.create_notification(
                    session=session,
                    user_id=event.card_owner_id,
                    notification_type=NotificationType.checklist_toggled,
                    title="Checklist Item Updated",
                    message=f"{event.toggled_by_name} marked '{event.item_title}' as {status} on your card '{event.card_title}'",
                    reference_id=event.card_id,
                    reference_type="card",
                )
                logger.info(f"Notification created for checklist toggle: {event.card_id}")
        
        elif isinstance(event, InvitationSentEvent):
            notifications_repo.create_notification(
                session=session,
                user_id=event.invitee_id,
                notification_type=NotificationType.workspace_invitation,
                title="Workspace Invitation",
                message=f"{event.inviter_name} invited you to join '{event.workspace_name}'",
                reference_id=event.invitation_id,
                reference_type="invitation",
            )
            logger.info(f"Notification created for invitation: {event.invitation_id}")
        
        elif isinstance(event, InvitationRespondedEvent):
            notification_type = (
                NotificationType.invitation_accepted if event.accepted
                else NotificationType.invitation_rejected
            )
            status = "accepted" if event.accepted else "rejected"
            notifications_repo.create_notification(
                session=session,
                user_id=event.inviter_id,
                notification_type=notification_type,
                title=f"Invitation {status.title()}",
                message=f"{event.responder_name} {status} your invitation to '{event.workspace_name}'",
                reference_id=event.workspace_id,
                reference_type="workspace",
            )
            logger.info(f"Notification created for invitation response: {event.invitation_id}")


def handle_email(event: NotifiableEvent) -> None:
    """
    Queue email for an event.
    Uses lazy import to avoid circular dependencies.
    """
    from app.utils import send_email
    
    if isinstance(event, CardMovedEvent):
        if event.card_owner_email and event.card_owner_id != event.moved_by_id:
            send_email(
                email_to=event.card_owner_email,
                subject=f"Card '{event.card_title}' was moved",
                html_content=f"""
                <h2>Card Moved</h2>
                <p><strong>{event.moved_by_name}</strong> moved your card <strong>"{event.card_title}"</strong>:</p>
                <p>From: <strong>{event.old_list_name}</strong> → To: <strong>{event.new_list_name}</strong></p>
                <p><a href="#">View Card</a></p>
                """,
                use_queue=True,
            )
            logger.info(f"Email queued for card move: {event.card_owner_email}")
    
    elif isinstance(event, CommentAddedEvent):
        if event.card_owner_email and event.card_owner_id != event.commenter_id:
            content_preview = event.comment_content[:500]
            if len(event.comment_content) > 500:
                content_preview += "..."
            send_email(
                email_to=event.card_owner_email,
                subject=f"New comment on '{event.card_title}'",
                html_content=f"""
                <h2>New Comment on Your Card</h2>
                <p><strong>{event.commenter_name}</strong> commented on your card <strong>"{event.card_title}"</strong>:</p>
                <blockquote style="border-left: 3px solid #ccc; padding-left: 10px; color: #666;">
                    {content_preview}
                </blockquote>
                <p><a href="#">View Card</a></p>
                """,
                use_queue=True,
            )
            logger.info(f"Email queued for comment: {event.card_owner_email}")
    
    elif isinstance(event, ChecklistToggledEvent):
        if event.card_owner_email and event.card_owner_id != event.toggled_by_id:
            status = "completed" if event.is_completed else "uncompleted"
            status_emoji = "✅" if event.is_completed else "⬜"
            send_email(
                email_to=event.card_owner_email,
                subject=f"Checklist item updated on '{event.card_title}'",
                html_content=f"""
                <h2>Checklist Item Updated</h2>
                <p><strong>{event.toggled_by_name}</strong> updated a checklist item on your card <strong>"{event.card_title}"</strong>:</p>
                <p>{status_emoji} <strong>{event.item_title}</strong> - marked as {status}</p>
                <p><a href="#">View Card</a></p>
                """,
                use_queue=True,
            )
            logger.info(f"Email queued for checklist toggle: {event.card_owner_email}")
