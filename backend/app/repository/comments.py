"""
Comments Repository - All database operations for CardComment model.
"""
import uuid
from datetime import datetime
from typing import Any

from sqlmodel import Session, select

from app.models.comments import CardComment, CardCommentCreate, CardCommentUpdate, CardCommentWithUser
from app.models.cards import Card
from app.models.users import User


def enrich_comment_with_user(session: Session, comment: CardComment) -> CardCommentWithUser:
    """Add user info to comment."""
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


def get_comments_with_users(
    session: Session, comments: list[CardComment]
) -> list[CardCommentWithUser]:
    """Enrich a list of comments with user info."""
    return [enrich_comment_with_user(session, c) for c in comments]


def get_comment_by_id(*, session: Session, comment_id: uuid.UUID) -> CardComment | None:
    """Get comment by ID."""
    return session.get(CardComment, comment_id)


def get_card_by_id(*, session: Session, card_id: uuid.UUID) -> Card | None:
    """Get card by ID."""
    return session.get(Card, card_id)


def get_user_by_id(*, session: Session, user_id: uuid.UUID) -> User | None:
    """Get user by ID."""
    return session.get(User, user_id)


def get_comments_by_card(
    *, session: Session, card_id: uuid.UUID | None = None, skip: int = 0, limit: int = 100
) -> tuple[list[CardComment], int]:
    """Get comments, optionally filtered by card_id."""
    query = select(CardComment).where(CardComment.is_deleted == False)
    
    if card_id:
        query = query.where(CardComment.card_id == card_id)
    
    query = query.order_by(CardComment.created_at.desc()).offset(skip).limit(limit)
    comments = session.exec(query).all()
    
    # Count query
    count_query = select(CardComment).where(CardComment.is_deleted == False)
    if card_id:
        count_query = count_query.where(CardComment.card_id == card_id)
    count = len(session.exec(count_query).all())
    
    return list(comments), count


def create_comment(
    *, session: Session, content: str, card_id: uuid.UUID, user_id: uuid.UUID
) -> CardComment:
    """Create a new comment."""
    comment = CardComment(
        content=content,
        card_id=card_id,
        user_id=user_id,
    )
    session.add(comment)
    session.commit()
    session.refresh(comment)
    return comment


def update_comment(
    *, session: Session, comment: CardComment, comment_in: CardCommentUpdate
) -> CardComment:
    """Update a comment."""
    update_data = comment_in.model_dump(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()
    comment.sqlmodel_update(update_data)
    session.add(comment)
    session.commit()
    session.refresh(comment)
    return comment


def soft_delete_comment(
    *, session: Session, comment: CardComment, deleted_by: uuid.UUID
) -> CardComment:
    """Soft delete a comment."""
    comment.is_deleted = True
    comment.deleted_at = datetime.utcnow()
    comment.deleted_by = str(deleted_by)
    session.add(comment)
    session.commit()
    session.refresh(comment)
    return comment
