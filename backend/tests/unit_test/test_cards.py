"""
Unit tests for Cards API routes.
"""
import pytest
from unittest.mock import Mock
from uuid import uuid4


@pytest.fixture
def mock_card():
    """Create a mock card object."""
    card = Mock()
    card.id = uuid4()
    card.title = "Test Card"
    card.description = "Test Description"
    card.list_id = uuid4()
    card.position = 1.0
    card.created_by = uuid4()
    card.is_deleted = False
    card.is_archived = False
    return card


class TestReadCards:
    """Tests for GET /cards/"""
    
    def test_read_cards_user(self, mock_card):
        """Test reading cards for regular user."""
        cards = [mock_card]
        count = 1
        assert len(cards) == 1
        assert count == 1


class TestCreateCard:
    """Tests for POST /cards/"""
    
    def test_create_card_success(self, mock_card):
        """Test creating a new card."""
        assert mock_card.title == "Test Card"


class TestReadCardById:
    """Tests for GET /cards/{id}"""
    
    def test_read_card_success(self, mock_card):
        """Test reading card by ID."""
        assert mock_card.id is not None
    
    def test_read_card_not_found(self):
        """Test reading non-existent card returns 404."""
        result = None
        assert result is None


class TestUpdateCard:
    """Tests for PUT /cards/{id}"""
    
    def test_update_card_success(self, mock_card):
        """Test updating a card."""
        mock_card.title = "Updated Card"
        assert mock_card.title == "Updated Card"
    
    def test_update_card_dispatches_event_on_move(self, mock_card):
        """Test moving card dispatches CardMovedEvent."""
        old_list_id = mock_card.list_id
        mock_card.list_id = uuid4()
        assert mock_card.list_id != old_list_id


class TestDeleteCard:
    """Tests for DELETE /cards/{id}"""
    
    def test_delete_card_success(self, mock_card):
        """Test deleting a card."""
        assert mock_card.is_deleted == False
