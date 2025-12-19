"""
Pytest configuration and fixtures for unit tests.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from uuid import uuid4
from datetime import datetime

from fastapi.testclient import TestClient
from sqlmodel import Session


@pytest.fixture
def mock_session():
    """Create a mock database session."""
    session = MagicMock(spec=Session)
    return session


@pytest.fixture
def mock_user():
    """Create a mock user object."""
    user = Mock()
    user.id = uuid4()
    user.email = "test@example.com"
    user.full_name = "Test User"
    user.is_active = True
    user.is_superuser = False
    user.is_deleted = False
    user.hashed_password = "hashed_password"
    return user


@pytest.fixture
def mock_superuser():
    """Create a mock superuser object."""
    user = Mock()
    user.id = uuid4()
    user.email = "admin@example.com"
    user.full_name = "Admin User"
    user.is_active = True
    user.is_superuser = True
    user.is_deleted = False
    return user


@pytest.fixture
def mock_workspace():
    """Create a mock workspace object."""
    workspace = Mock()
    workspace.id = uuid4()
    workspace.name = "Test Workspace"
    workspace.description = "Test Description"
    workspace.owner_id = uuid4()
    workspace.is_deleted = False
    return workspace


@pytest.fixture
def mock_board():
    """Create a mock board object."""
    board = Mock()
    board.id = uuid4()
    board.name = "Test Board"
    board.workspace_id = uuid4()
    board.owner_id = uuid4()
    board.is_deleted = False
    return board


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


@pytest.fixture
def sample_user_data():
    """Sample user data for creation."""
    return {
        "email": "newuser@example.com",
        "password": "password123",
        "full_name": "New User"
    }


@pytest.fixture
def sample_workspace_data():
    """Sample workspace data for creation."""
    return {
        "name": "New Workspace",
        "description": "New workspace description"
    }


@pytest.fixture
def sample_board_data():
    """Sample board data for creation."""
    return {
        "name": "New Board",
        "workspace_id": str(uuid4())
    }


@pytest.fixture
def sample_card_data():
    """Sample card data for creation."""
    return {
        "title": "New Card",
        "description": "New card description",
        "list_id": str(uuid4())
    }
