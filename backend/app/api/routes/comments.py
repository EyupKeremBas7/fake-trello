from fastapi import APIRouter, HTTPException
from sqlmodel import select
from datetime import datetime
import uuid

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    CardComment,
    CardCommentCreate,
    CardCommentPublic,
    CardCommentsPublic,
    CardCommentUpdate,
    Card,
    User,
)

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
    query = select(CardComment)
    
    if card_id:
        query = query.where(CardComment.card_id == card_id)
    
    query = query.order_by(CardComment.created_at.desc()).offset(skip).limit(limit)
    comments = session.exec(query).all()
    
    # Enrich with user info
    result = []
    for comment in comments:
        user = session.get(User, comment.user_id)
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
    
    # Count query
    count_query = select(CardComment)
    if card_id:
        count_query = count_query.where(CardComment.card_id == card_id)
    count = len(session.exec(count_query).all())
    
    return CardCommentsWithUserPublic(data=result, count=count)


@router.get("/{id}", response_model=CardCommentWithUser)
def read_comment(
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
) -> CardCommentWithUser:
    """Get a specific comment by ID."""
    comment = session.get(CardComment, id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    user = session.get(User, comment.user_id)
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
    card = session.get(Card, comment_in.card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    comment = CardComment(
        content=comment_in.content,
        card_id=comment_in.card_id,
        user_id=current_user.id,
    )
    session.add(comment)
    session.commit()
    session.refresh(comment)
    
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
    comment = session.get(CardComment, id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Only the author can update their comment
    if comment.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized to update this comment")
    
    update_data = comment_in.model_dump(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()
    comment.sqlmodel_update(update_data)
    session.add(comment)
    session.commit()
    session.refresh(comment)
    
    user = session.get(User, comment.user_id)
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
    comment = session.get(CardComment, id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Only the author or superuser can delete
    if comment.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized to delete this comment")
    
    session.delete(comment)
    session.commit()
    return {"ok": True}
