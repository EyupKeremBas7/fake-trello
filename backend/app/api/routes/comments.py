"""
Comments API Routes - Clean routes without direct database queries.
"""
import uuid

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, SessionDep
from app.models.comments import (
    CardCommentCreate,
    CardCommentsWithUserPublic,
    CardCommentUpdate,
    CardCommentWithUser,
)
from app.repository import comments as comments_repo

router = APIRouter(prefix="/comments", tags=["comments"])

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

    result = comments_repo.get_comments_with_users(session, comments)
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

    return comments_repo.enrich_comment_with_user(session, comment)


@router.post("/", response_model=CardCommentWithUser)
def create_comment(
    session: SessionDep,
    current_user: CurrentUser,
    comment_in: CardCommentCreate,
) -> CardCommentWithUser:
    """Create a new comment."""
    card = comments_repo.get_card_by_id(session=session, card_id=comment_in.card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    comment = comments_repo.create_comment(
        session=session,
        content=comment_in.content,
        card_id=comment_in.card_id,
        user_id=current_user.id
    )

    # Dispatch CommentAddedEvent (Observer pattern)
    card_owner = None
    card_owner_email = None
    if card.created_by:
        owner = comments_repo.get_user_by_id(session=session, user_id=card.created_by)
        if owner and not owner.is_deleted:
            card_owner = owner.id
            card_owner_email = owner.email

    # Get assignee info (notifications go to assignee if set)
    card_assignee = None
    card_assignee_email = None
    if card.assigned_to:
        assignee = comments_repo.get_user_by_id(session=session, user_id=card.assigned_to)
        if assignee and not assignee.is_deleted:
            card_assignee = assignee.id
            card_assignee_email = assignee.email

    from app.events import CommentAddedEvent, EventDispatcher
    EventDispatcher.dispatch(CommentAddedEvent(
        card_id=card.id,
        card_title=card.title,
        comment_content=comment_in.content,
        commenter_id=current_user.id,
        commenter_name=current_user.full_name or current_user.email,
        card_owner_id=card_owner,
        card_owner_email=card_owner_email,
        card_assignee_id=card_assignee,
        card_assignee_email=card_assignee_email,
    ))

    return comments_repo.enrich_comment_with_user(session, comment)


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
    if comment.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized to update this comment")

    comment = comments_repo.update_comment(session=session, comment=comment, comment_in=comment_in)

    return comments_repo.enrich_comment_with_user(session, comment)


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
