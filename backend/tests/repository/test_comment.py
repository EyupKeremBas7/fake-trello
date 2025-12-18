"""
Tests for Comment Repository.
"""
import uuid

from sqlmodel import Session

from app.repository import comments as comment_repo
from app.repository import cards as card_repo
from app.repository import lists as list_repo
from app.repository import boards as board_repo
from app.repository import workspaces as workspace_repo
from app.models.comments import CardCommentUpdate
from app.models.cards import CardCreate
from app.models.lists import ListCreate
from app.models.boards import BoardCreate
from app.models.workspaces import WorkspaceCreate
from tests.utils.utils import random_lower_string


def _create_test_card(db: Session, owner_id: uuid.UUID):
    """Helper to create a test card with full hierarchy."""
    workspace_in = WorkspaceCreate(
        name=f"Test Workspace {random_lower_string()[:8]}",
        description="Test workspace for comment tests"
    )
    workspace = workspace_repo.create_workspace(
        session=db, workspace_in=workspace_in, owner_id=owner_id
    )
    
    board_in = BoardCreate(
        name=f"Test Board {random_lower_string()[:8]}",
        description="Test board for comment tests",
        workspace_id=workspace.id
    )
    board = board_repo.create_board(
        session=db, board_in=board_in, owner_id=owner_id
    )
    
    list_in = ListCreate(
        name=f"Test List {random_lower_string()[:8]}",
        board_id=board.id
    )
    board_list = list_repo.create_list(session=db, list_in=list_in)
    
    card_in = CardCreate(
        title=f"Test Card {random_lower_string()[:8]}",
        description="Test card for comment tests",
        list_id=board_list.id
    )
    return card_repo.create_card(session=db, card_in=card_in, created_by=owner_id)


def test_create_comment(db: Session, test_user) -> None:
    """Test creating a new comment."""
    card = _create_test_card(db, test_user.id)
    
    content = f"This is a test comment {random_lower_string()[:8]}"
    comment = comment_repo.create_comment(
        session=db,
        content=content,
        card_id=card.id,
        user_id=test_user.id
    )
    assert comment.content == content
    assert comment.card_id == card.id
    assert comment.user_id == test_user.id


def test_get_comment_by_id(db: Session, test_user) -> None:
    """Test getting comment by ID."""
    card = _create_test_card(db, test_user.id)
    
    content = f"Test comment {random_lower_string()[:8]}"
    created = comment_repo.create_comment(
        session=db,
        content=content,
        card_id=card.id,
        user_id=test_user.id
    )
    
    fetched = comment_repo.get_comment_by_id(session=db, comment_id=created.id)
    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.content == created.content


def test_get_comments_by_card(db: Session, test_user) -> None:
    """Test getting comments for a card."""
    card = _create_test_card(db, test_user.id)
    
    # Create multiple comments
    for i in range(3):
        comment_repo.create_comment(
            session=db,
            content=f"Comment {i} {random_lower_string()[:8]}",
            card_id=card.id,
            user_id=test_user.id
        )
    
    comments, count = comment_repo.get_comments_by_card(
        session=db, card_id=card.id
    )
    assert len(comments) >= 3
    assert count >= 3


def test_update_comment(db: Session, test_user) -> None:
    """Test updating a comment."""
    card = _create_test_card(db, test_user.id)
    
    comment = comment_repo.create_comment(
        session=db,
        content=f"Original content {random_lower_string()[:8]}",
        card_id=card.id,
        user_id=test_user.id
    )
    
    update_in = CardCommentUpdate(content="Updated content")
    updated = comment_repo.update_comment(
        session=db, comment=comment, comment_in=update_in
    )
    assert updated.content == "Updated content"
    assert updated.updated_at is not None


def test_soft_delete_comment(db: Session, test_user) -> None:
    """Test soft deleting a comment."""
    card = _create_test_card(db, test_user.id)
    
    comment = comment_repo.create_comment(
        session=db,
        content=f"Delete me {random_lower_string()[:8]}",
        card_id=card.id,
        user_id=test_user.id
    )
    
    deleted = comment_repo.soft_delete_comment(
        session=db, comment=comment, deleted_by=test_user.id
    )
    assert deleted.is_deleted is True
    assert deleted.deleted_at is not None
    assert deleted.deleted_by == str(test_user.id)


def test_comments_ordered_by_created_at_desc(db: Session, test_user) -> None:
    """Test that comments are returned ordered by creation time descending."""
    card = _create_test_card(db, test_user.id)
    
    # Create multiple comments
    for i in range(3):
        comment_repo.create_comment(
            session=db,
            content=f"Comment {i}",
            card_id=card.id,
            user_id=test_user.id
        )
    
    comments, _ = comment_repo.get_comments_by_card(session=db, card_id=card.id)
    
    # Verify they're ordered by created_at descending (newest first)
    for i in range(len(comments) - 1):
        assert comments[i].created_at >= comments[i + 1].created_at


def test_get_comments_without_card_filter(db: Session, test_user) -> None:
    """Test getting all comments without card filter."""
    card = _create_test_card(db, test_user.id)
    
    comment_repo.create_comment(
        session=db,
        content=f"Test comment {random_lower_string()[:8]}",
        card_id=card.id,
        user_id=test_user.id
    )
    
    comments, count = comment_repo.get_comments_by_card(session=db, card_id=None)
    assert len(comments) >= 1
    assert count >= 1
