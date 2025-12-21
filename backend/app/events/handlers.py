"""
    This code can be refactored with Strategy + Registry Pattern in the future if I need to 
"""

import logging
from typing import Union

from app.events.types import (
    CardAssignedEvent,
    CardMovedEvent,
    ChecklistToggledEvent,
    CommentAddedEvent,
    InvitationRespondedEvent,
    InvitationSentEvent,
    WelcomeEmailSentEvent,
)
from app.models.notifications import NotificationType

logger = logging.getLogger(__name__)


NotifiableEvent = Union[
    CardMovedEvent,
    CommentAddedEvent,
    ChecklistToggledEvent,
    CardAssignedEvent,
    InvitationSentEvent,
    InvitationRespondedEvent,
    WelcomeEmailSentEvent,
]


def _get_notification_target(event) -> tuple:
    """
    Get the target user for notifications.
    Priority: assignee > owner
    Returns (user_id, user_email) or (None, None)
    """
    # Prefer assignee over owner for notifications
    if hasattr(event, 'card_assignee_id') and event.card_assignee_id:
        return event.card_assignee_id, getattr(event, 'card_assignee_email', None)
    if hasattr(event, 'card_owner_id') and event.card_owner_id:
        return event.card_owner_id, getattr(event, 'card_owner_email', None)
    return None, None


def handle_notification(event: NotifiableEvent) -> None:
    from sqlmodel import Session

    from app.core.db import engine
    from app.repository import notifications as notifications_repo

    with Session(engine) as session:
        if isinstance(event, CardMovedEvent):
            target_id, _ = _get_notification_target(event)
            if target_id and target_id != event.moved_by_id:
                notifications_repo.create_notification(
                    session=session,
                    user_id=target_id,
                    notification_type=NotificationType.card_moved,
                    title="Card Moved",
                    message=f"{event.moved_by_name} moved card '{event.card_title}' from '{event.old_list_name}' to '{event.new_list_name}'",
                    reference_id=event.card_id,
                    reference_type="card",
                )
                logger.info(f"Notification created for card move: {event.card_id}")

        elif isinstance(event, CommentAddedEvent):
            target_id, _ = _get_notification_target(event)
            if target_id and target_id != event.commenter_id:
                notifications_repo.create_notification(
                    session=session,
                    user_id=target_id,
                    notification_type=NotificationType.comment_added,
                    title="New Comment",
                    message=f"{event.commenter_name} commented on card '{event.card_title}'",
                    reference_id=event.card_id,
                    reference_type="card",
                )
                logger.info(f"Notification created for comment: {event.card_id}")

        elif isinstance(event, ChecklistToggledEvent):
            target_id, _ = _get_notification_target(event)
            if target_id and target_id != event.toggled_by_id:
                status = "completed" if event.is_completed else "uncompleted"
                notifications_repo.create_notification(
                    session=session,
                    user_id=target_id,
                    notification_type=NotificationType.checklist_toggled,
                    title="Checklist Item Updated",
                    message=f"{event.toggled_by_name} marked '{event.item_title}' as {status} on card '{event.card_title}'",
                    reference_id=event.card_id,
                    reference_type="card",
                )
                logger.info(f"Notification created for checklist toggle: {event.card_id}")

        elif isinstance(event, CardAssignedEvent):
            notifications_repo.create_notification(
                session=session,
                user_id=event.assignee_id,
                notification_type=NotificationType.card_assigned,
                title="Card Assigned",
                message=f"{event.assigned_by_name} assigned you to card '{event.card_title}'",
                reference_id=event.card_id,
                reference_type="card",
            )
            logger.info(f"Notification created for card assignment: {event.card_id}")

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
    from app.core.config import settings
    from app.utils import render_email_template, send_email

    if isinstance(event, CardMovedEvent):
        _, target_email = _get_notification_target(event)
        if target_email and _get_notification_target(event)[0] != event.moved_by_id:
            html_content = render_email_template(
                template_name="card_moved.html",
                context={
                    "moved_by_name": event.moved_by_name,
                    "card_title": event.card_title,
                    "old_list_name": event.old_list_name,
                    "new_list_name": event.new_list_name,
                    "link": settings.FRONTEND_HOST,
                },
            )
            send_email(
                email_to=target_email,
                subject=f"Card '{event.card_title}' was moved",
                html_content=html_content,
                use_queue=True,
            )
            logger.info(f"Email queued for card move: {target_email}")

    elif isinstance(event, CommentAddedEvent):
        _, target_email = _get_notification_target(event)
        if target_email and _get_notification_target(event)[0] != event.commenter_id:
            content_preview = event.comment_content[:500]
            if len(event.comment_content) > 500:
                content_preview += "..."
            html_content = render_email_template(
                template_name="comment_added.html",
                context={
                    "commenter_name": event.commenter_name,
                    "card_title": event.card_title,
                    "comment_content": content_preview,
                    "link": settings.FRONTEND_HOST,
                },
            )
            send_email(
                email_to=target_email,
                subject=f"New comment on '{event.card_title}'",
                html_content=html_content,
                use_queue=True,
            )
            logger.info(f"Email queued for comment: {target_email}")

    elif isinstance(event, ChecklistToggledEvent):
        _, target_email = _get_notification_target(event)
        if target_email and _get_notification_target(event)[0] != event.toggled_by_id:
            status = "completed" if event.is_completed else "uncompleted"
            status_emoji = "✅" if event.is_completed else "⬜"
            html_content = render_email_template(
                template_name="checklist_toggled.html",
                context={
                    "toggled_by_name": event.toggled_by_name,
                    "card_title": event.card_title,
                    "item_title": event.item_title,
                    "status": status,
                    "status_emoji": status_emoji,
                    "link": settings.FRONTEND_HOST,
                },
            )
            send_email(
                email_to=target_email,
                subject=f"Checklist item updated on '{event.card_title}'",
                html_content=html_content,
                use_queue=True,
            )
            logger.info(f"Email queued for checklist toggle: {target_email}")

    elif isinstance(event, CardAssignedEvent):
        html_content = render_email_template(
            template_name="card_assigned.html",
            context={
                "assigned_by_name": event.assigned_by_name,
                "card_title": event.card_title,
                "link": settings.FRONTEND_HOST,
            },
        )
        send_email(
            email_to=event.assignee_email,
            subject=f"You were assigned to '{event.card_title}'",
            html_content=html_content,
            use_queue=True,
        )
        logger.info(f"Email queued for card assignment: {event.assignee_email}")

    elif isinstance(event, WelcomeEmailSentEvent):
        html_content = render_email_template(
            template_name="welcome.html",
            context={
                "project_name": settings.PROJECT_NAME,
                "link": settings.FRONTEND_HOST,
            },
        )
        send_email(
            email_to=event.user_email,
            subject=f"Welcome to {settings.PROJECT_NAME}! 🎉",
            html_content=html_content,
            use_queue=True,
        )
        logger.info(f"Email queued for welcome: {event.user_email}")

