"""
Unit tests for Comments Repository.
Tests all database operations for CardComment model.
"""
import pytest
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch
from uuid import uuid4


class TestCommentCRUD:
    """Tests for comment CRUD operations."""

    def test_create_comment(self, mock_session):
        """Test creating a comment."""
        from app.repository import comments as comments_repo

        card_id = uuid4()
        user_id = uuid4()
        content = "Test comment"

        result = comments_repo.create_comment(
            session=mock_session,
            content=content,
            card_id=card_id,
            user_id=user_id
        )

        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    def test_get_comment_by_id(self, mock_session):
        """Test getting comment by ID."""
        from app.repository import comments as comments_repo

        mock_comment = Mock()
        mock_comment.id = uuid4()
        mock_session.get.return_value = mock_comment

        result = comments_repo.get_comment_by_id(
            session=mock_session,
            comment_id=mock_comment.id
        )

        assert result == mock_comment

    def test_update_comment(self, mock_session):
        """Test updating comment."""
        from app.models.comments import CardCommentUpdate
        from app.repository import comments as comments_repo

        mock_comment = Mock()
        mock_comment.sqlmodel_update = Mock()
        comment_in = CardCommentUpdate(content="Updated comment")

        result = comments_repo.update_comment(
            session=mock_session,
            comment=mock_comment,
            comment_in=comment_in
        )

        mock_comment.sqlmodel_update.assert_called_once()
        mock_session.commit.assert_called_once()

    def test_soft_delete_comment(self, mock_session):
        """Test soft deleting comment."""
        from app.repository import comments as comments_repo

        mock_comment = Mock()
        mock_comment.is_deleted = False
        deleted_by = uuid4()

        result = comments_repo.soft_delete_comment(
            session=mock_session,
            comment=mock_comment,
            deleted_by=deleted_by
        )

        assert mock_comment.is_deleted is True
        assert mock_comment.deleted_by == str(deleted_by)


class TestGetComments:
    """Tests for comment retrieval."""

    def test_get_comments_by_card(self, mock_session):
        """Test getting comments for a card."""
        from app.repository import comments as comments_repo

        mock_comments = [Mock(), Mock()]
        mock_session.exec.return_value.all.return_value = mock_comments

        comments, count = comments_repo.get_comments_by_card(
            session=mock_session,
            card_id=uuid4()
        )

        assert len(comments) == 2

    def test_get_comments_all(self, mock_session):
        """Test getting all comments without filter."""
        from app.repository import comments as comments_repo

        mock_comments = [Mock()]
        mock_session.exec.return_value.all.return_value = mock_comments

        comments, count = comments_repo.get_comments_by_card(
            session=mock_session,
            card_id=None
        )

        assert len(comments) == 1


class TestEnrichComment:
    """Tests for comment enrichment functions."""

    def test_enrich_comment_with_user(self, mock_session, mock_user):
        """Test enriching comment with user info."""
        from app.repository import comments as comments_repo

        mock_comment = Mock()
        mock_comment.id = uuid4()
        mock_comment.content = "Test comment"
        mock_comment.card_id = uuid4()
        mock_comment.user_id = mock_user.id
        mock_comment.created_at = datetime.utcnow()
        mock_comment.updated_at = datetime.utcnow()

        mock_session.get.return_value = mock_user

        result = comments_repo.enrich_comment_with_user(mock_session, mock_comment)

        assert result.user_full_name == mock_user.full_name
        assert result.user_email == mock_user.email

    def test_get_comments_with_users(self, mock_session, mock_user):
        """Test enriching multiple comments with user info."""
        from app.repository import comments as comments_repo

        mock_comment = Mock()
        mock_comment.id = uuid4()
        mock_comment.content = "Test"
        mock_comment.card_id = uuid4()
        mock_comment.user_id = mock_user.id
        mock_comment.created_at = datetime.utcnow()
        mock_comment.updated_at = datetime.utcnow()

        mock_session.get.return_value = mock_user

        result = comments_repo.get_comments_with_users(mock_session, [mock_comment])

        assert len(result) == 1
        assert result[0].user_full_name == mock_user.full_name
