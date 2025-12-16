"""
Comments API Routes - Clean routes without direct database queries.
"""
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, SessionDep
from app.repository import comments as comments_repo
from app.models.comments import (
    CardComment,
    CardCommentCreate,
    CardCommentPublic,
    CardCommentsPublic,
    CardCommentUpdate,
)
from app.models.notifications import Notification, NotificationType
from app.utils import send_email

router = APIRouter(prefix="/comments", tags=["comments"])


# Extended public model to include user info
class CardCommentWithUser(CardCommentPublic):
    user_full_name: str | None = None
    user_email: str | None = None


class CardCommentsWithUserPublic(CardCommentsPublic):
    data: list[CardCommentWithUser]


@router.get("/", response_model=CardCommentsWithUserPublic)
def read_comments(
    session: SessionDep,
    current_user: CurrentUser,
    card_id: uuid.UUID | None = None,
    skip: int = 0,
    limit: int = 100,
) -> CardCommentsWithUserPublic:
    """Get all comments, optionally filtered by card_id."""
    comments, count = comments_repo.get_comments_by_card(
        session=session, card_id=card_id, skip=skip, limit=limit
    )
    
    result = []
    for comment in comments:
        user = comments_repo.get_user_by_id(session=session, user_id=comment.user_id)
        result.append(CardCommentWithUser(
            id=comment.id,
            content=comment.content,
            card_id=comment.card_id,
            user_id=comment.user_id,
            created_at=comment.created_at,
            updated_at=comment.updated_at,
            user_full_name=user.full_name if user else None,
            user_email=user.email if user else None,
        ))
    
    return CardCommentsWithUserPublic(data=result, count=count)


@router.get("/{id}", response_model=CardCommentWithUser)
def read_comment(
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
) -> CardCommentWithUser:
    """Get a specific comment by ID."""
    comment = comments_repo.get_comment_by_id(session=session, comment_id=id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    user = comments_repo.get_user_by_id(session=session, user_id=comment.user_id)
    return CardCommentWithUser(
        id=comment.id,
        content=comment.content,
        card_id=comment.card_id,
        user_id=comment.user_id,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
        user_full_name=user.full_name if user else None,
        user_email=user.email if user else None,
    )


@router.post("/", response_model=CardCommentWithUser)
def create_comment(
    session: SessionDep,
    current_user: CurrentUser,
    comment_in: CardCommentCreate,
) -> CardCommentWithUser:
    """Create a new comment."""
    # Verify card exists
    card = comments_repo.get_card_by_id(session=session, card_id=comment_in.card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    comment = comments_repo.create_comment(
        session=session,
        content=comment_in.content,
        card_id=comment_in.card_id,
        user_id=current_user.id
    )
    
    # Notify card owner if someone else comments
    if card.created_by and card.created_by != current_user.id:
        card_owner = comments_repo.get_user_by_id(session=session, user_id=card.created_by)
        if card_owner and not card_owner.is_deleted:
            # Create in-app notification
            notification = Notification(
                user_id=card_owner.id,
                type=NotificationType.comment_added,
                title="New Comment",
                message=f"{current_user.full_name or current_user.email} commented on your card '{card.title}'",
                reference_id=card.id,
                reference_type="card",
            )
            session.add(notification)
            session.commit()
            
            # Send email notification
            send_email(
                email_to=card_owner.email,
                subject=f"New comment on '{card.title}'",
                html_content=f"""
                <h2>New Comment on Your Card</h2>
                <p><strong>{current_user.full_name or current_user.email}</strong> commented on your card <strong>"{card.title}"</strong>:</p>
                <blockquote style="border-left: 3px solid #ccc; padding-left: 10px; color: #666;">
                    {comment_in.content[:500]}{'...' if len(comment_in.content) > 500 else ''}
                </blockquote>
                <p><a href="#">View Card</a></p>
                """,
                use_queue=True,
            )
    
    return CardCommentWithUser(
        id=comment.id,
        content=comment.content,
        card_id=comment.card_id,
        user_id=comment.user_id,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
        user_full_name=current_user.full_name,
        user_email=current_user.email,
    )


@router.patch("/{id}", response_model=CardCommentWithUser)
def update_comment(
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    comment_in: CardCommentUpdate,
) -> CardCommentWithUser:
    """Update a comment. Only the comment author can update it."""
    comment = comments_repo.get_comment_by_id(session=session, comment_id=id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Only the author can update their comment
    if comment.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized to update this comment")
    
    comment = comments_repo.update_comment(session=session, comment=comment, comment_in=comment_in)
    
    user = comments_repo.get_user_by_id(session=session, user_id=comment.user_id)
    return CardCommentWithUser(
        id=comment.id,
        content=comment.content,
        card_id=comment.card_id,
        user_id=comment.user_id,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
        user_full_name=user.full_name if user else None,
        user_email=user.email if user else None,
    )


@router.delete("/{id}")
def delete_comment(
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
) -> dict:
    """Delete a comment. Only the comment author or superuser can delete it."""
    comment = comments_repo.get_comment_by_id(session=session, comment_id=id)
    if not comment or comment.is_deleted:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    if comment.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized to delete this comment")
    
    comments_repo.soft_delete_comment(session=session, comment=comment, deleted_by=current_user.id)
    return {"ok": True}
