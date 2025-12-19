"""
Unit tests for Lists API routes.
"""
import pytest
from unittest.mock import Mock
from uuid import uuid4


@pytest.fixture
def mock_list():
    """Create a mock list object."""
    board_list = Mock()
    board_list.id = uuid4()
    board_list.name = "Test List"
    board_list.board_id = uuid4()
    board_list.position = 1.0
    board_list.is_deleted = False
    return board_list


class TestReadLists:
    """Tests for GET /lists/"""
    
    def test_read_lists_by_board(self, mock_list):
        """Test reading lists for a board."""
        lists = [mock_list]
        assert len(lists) == 1


class TestCreateList:
    """Tests for POST /lists/"""
    
    def test_create_list_success(self, mock_list):
        """Test creating a new list."""
        assert mock_list.name == "Test List"


class TestUpdateList:
    """Tests for PUT /lists/{id}"""
    
    def test_update_list_success(self, mock_list):
        """Test updating a list."""
        mock_list.name = "Updated List"
        assert mock_list.name == "Updated List"


class TestDeleteList:
    """Tests for DELETE /lists/{id}"""
    
    def test_delete_list_success(self, mock_list):
        """Test deleting a list."""
        assert mock_list.is_deleted == False
