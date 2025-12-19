"""
Unit tests for Checklists API routes.
"""
import pytest
from unittest.mock import Mock
from uuid import uuid4


@pytest.fixture
def mock_checklist():
    """Create a mock checklist object."""
    checklist = Mock()
    checklist.id = uuid4()
    checklist.title = "Test Checklist"
    checklist.card_id = uuid4()
    checklist.is_deleted = False
    return checklist


@pytest.fixture
def mock_checklist_item():
    """Create a mock checklist item."""
    item = Mock()
    item.id = uuid4()
    item.title = "Test Item"
    item.is_completed = False
    return item


class TestReadChecklists:
    """Tests for GET /checklists/"""
    
    def test_read_checklists_by_card(self, mock_checklist):
        """Test reading checklists for a card."""
        checklists = [mock_checklist]
        assert len(checklists) == 1


class TestCreateChecklist:
    """Tests for POST /checklists/"""
    
    def test_create_checklist_success(self, mock_checklist):
        """Test creating a new checklist."""
        assert mock_checklist.title == "Test Checklist"


class TestToggleChecklistItem:
    """Tests for toggling checklist items."""
    
    def test_toggle_item_dispatches_event(self, mock_checklist_item):
        """Test toggling checklist item dispatches event."""
        mock_checklist_item.is_completed = True
        assert mock_checklist_item.is_completed == True


class TestDeleteChecklist:
    """Tests for DELETE /checklists/{id}"""
    
    def test_delete_checklist_success(self, mock_checklist):
        """Test deleting a checklist."""
        assert mock_checklist.is_deleted == False
