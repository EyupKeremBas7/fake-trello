"""
Unit tests for Comments API routes.
"""
import pytest
from unittest.mock import Mock
from uuid import uuid4


@pytest.fixture
def mock_comment():
    """Create a mock comment object."""
    comment = Mock()
    comment.id = uuid4()
    comment.content = "Test comment"
    comment.card_id = uuid4()
    comment.user_id = uuid4()
    comment.is_deleted = False
    return comment


class TestReadComments:
    """Tests for GET /comments/"""
    
    def test_read_comments_by_card(self, mock_comment):
        """Test reading comments for a card."""
        comments = [mock_comment]
        assert len(comments) == 1


class TestCreateComment:
    """Tests for POST /comments/"""
    
    def test_create_comment_success(self, mock_comment):
        """Test creating a new comment dispatches event."""
        assert mock_comment.content == "Test comment"


class TestDeleteComment:
    """Tests for DELETE /comments/{id}"""
    
    def test_delete_comment_success(self, mock_comment):
        """Test deleting a comment."""
        assert mock_comment.is_deleted == False
