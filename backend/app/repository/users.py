"""
Users Repository - All database operations for User model.
"""
import uuid
from datetime import datetime
from typing import Any

from sqlmodel import Session, select, func

from app.core.security import get_password_hash, verify_password
from app.models.users import User, UserCreate, UserUpdate


def create_user(*, session: Session, user_create: UserCreate) -> User:
    """Create a new user with hashed password."""
    db_obj = User.model_validate(
        user_create, update={"hashed_password": get_password_hash(user_create.password)}
    )
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def update_user(*, session: Session, db_user: User, user_in: UserUpdate) -> Any:
    """Update user data including password if provided."""
    user_data = user_in.model_dump(exclude_unset=True)
    extra_data = {}
    if "password" in user_data:
        password = user_data["password"]
        hashed_password = get_password_hash(password)
        extra_data["hashed_password"] = hashed_password
    db_user.sqlmodel_update(user_data, update=extra_data)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


def get_user_by_email(*, session: Session, email: str) -> User | None:
    """Get user by email (excludes soft-deleted users)."""
    statement = select(User).where(User.email == email, User.is_deleted == False)
    session_user = session.exec(statement).first()
    return session_user


def get_user_by_id(*, session: Session, user_id: uuid.UUID) -> User | None:
    """Get user by ID."""
    return session.get(User, user_id)


def authenticate(*, session: Session, email: str, password: str) -> User | None:
    """Authenticate user with email and password."""
    db_user = get_user_by_email(session=session, email=email)
    if not db_user:
        return None
    if db_user.is_deleted:
        return None
    if not verify_password(password, db_user.hashed_password):
        return None
    return db_user


def get_users_list(
    *, session: Session, skip: int = 0, limit: int = 100
) -> tuple[list[User], int]:
    """Get list of users with count (excludes soft-deleted)."""
    count_statement = select(func.count()).select_from(User).where(User.is_deleted == False)
    count = session.exec(count_statement).one()
    
    statement = select(User).where(User.is_deleted == False).offset(skip).limit(limit)
    users = session.exec(statement).all()
    
    return list(users), count


def check_email_exists(*, session: Session, email: str) -> bool:
    """Check if email exists (including soft-deleted users)."""
    existing = session.exec(
        select(User).where(User.email == email)
    ).first()
    return existing is not None


def soft_delete_user(
    *, session: Session, user: User, deleted_by: uuid.UUID
) -> User:
    """Soft delete a user and modify email to free up unique constraint."""
    user.is_deleted = True
    user.deleted_at = datetime.utcnow()
    user.deleted_by = str(deleted_by)
    # Append deletion timestamp to email to free up the email for new registrations
    user.email = f"{user.email}__deleted_{int(user.deleted_at.timestamp())}"
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def update_user_password(*, session: Session, user: User, new_password: str) -> User:
    """Update user's password."""
    hashed_password = get_password_hash(new_password)
    user.hashed_password = hashed_password
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def delete_user_hard(*, session: Session, user: User) -> None:
    """Hard delete a user (permanent)."""
    session.delete(user)
    session.commit()
