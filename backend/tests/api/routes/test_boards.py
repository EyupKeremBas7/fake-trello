"""
Test cases for Board API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from tests.utils.utils import random_lower_string


class TestBoardsAPI:
    """Test suite for /boards endpoints."""

    def test_create_board(
        self, client: TestClient, superuser_token_headers: dict[str, str]
    ) -> None:
        """Test creating a new board."""
        # First create a workspace
        workspace_data = {"name": f"Test Workspace {random_lower_string()[:8]}"}
        r = client.post(
            f"{settings.API_V1_STR}/workspaces/",
            headers=superuser_token_headers,
            json=workspace_data,
        )
        assert r.status_code == 200
        workspace = r.json()

        # Create board
        board_data = {
            "name": f"Test Board {random_lower_string()[:8]}",
            "workspace_id": workspace["id"],
            "visibility": "private",
        }
        r = client.post(
            f"{settings.API_V1_STR}/boards/",
            headers=superuser_token_headers,
            json=board_data,
        )
        assert r.status_code == 200
        board = r.json()
        assert board["name"] == board_data["name"]
        assert board["workspace_id"] == workspace["id"]
        assert board["visibility"] == "private"

    def test_create_board_sanitizes_input(
        self, client: TestClient, superuser_token_headers: dict[str, str]
    ) -> None:
        """Test that XSS attempts are sanitized."""
        # First create a workspace
        workspace_data = {"name": "Sanitize Test Workspace"}
        r = client.post(
            f"{settings.API_V1_STR}/workspaces/",
            headers=superuser_token_headers,
            json=workspace_data,
        )
        workspace = r.json()

        # Try XSS in board name
        board_data = {
            "name": "<script>alert('xss')</script>Test Board",
            "workspace_id": workspace["id"],
        }
        r = client.post(
            f"{settings.API_V1_STR}/boards/",
            headers=superuser_token_headers,
            json=board_data,
        )
        assert r.status_code == 200
        board = r.json()
        # Script tags should be stripped
        assert "<script>" not in board["name"]
        assert "Test Board" in board["name"]

    def test_read_boards(
        self, client: TestClient, superuser_token_headers: dict[str, str]
    ) -> None:
        """Test listing boards."""
        r = client.get(
            f"{settings.API_V1_STR}/boards/",
            headers=superuser_token_headers,
        )
        assert r.status_code == 200
        data = r.json()
        assert "data" in data
        assert "count" in data
        assert isinstance(data["data"], list)

    def test_read_board_by_id(
        self, client: TestClient, superuser_token_headers: dict[str, str]
    ) -> None:
        """Test reading a specific board."""
        # Create workspace and board first
        workspace_data = {"name": f"Read Test Workspace {random_lower_string()[:8]}"}
        r = client.post(
            f"{settings.API_V1_STR}/workspaces/",
            headers=superuser_token_headers,
            json=workspace_data,
        )
        workspace = r.json()

        board_data = {
            "name": f"Read Test Board {random_lower_string()[:8]}",
            "workspace_id": workspace["id"],
        }
        r = client.post(
            f"{settings.API_V1_STR}/boards/",
            headers=superuser_token_headers,
            json=board_data,
        )
        board = r.json()

        # Read the board
        r = client.get(
            f"{settings.API_V1_STR}/boards/{board['id']}",
            headers=superuser_token_headers,
        )
        assert r.status_code == 200
        fetched_board = r.json()
        assert fetched_board["id"] == board["id"]
        assert fetched_board["name"] == board["name"]

    def test_update_board(
        self, client: TestClient, superuser_token_headers: dict[str, str]
    ) -> None:
        """Test updating a board."""
        # Create workspace and board
        workspace_data = {"name": f"Update Test Workspace {random_lower_string()[:8]}"}
        r = client.post(
            f"{settings.API_V1_STR}/workspaces/",
            headers=superuser_token_headers,
            json=workspace_data,
        )
        workspace = r.json()

        board_data = {
            "name": "Original Board Name",
            "workspace_id": workspace["id"],
        }
        r = client.post(
            f"{settings.API_V1_STR}/boards/",
            headers=superuser_token_headers,
            json=board_data,
        )
        board = r.json()

        # Update the board
        update_data = {"name": "Updated Board Name", "background_image": "blue"}
        r = client.patch(
            f"{settings.API_V1_STR}/boards/{board['id']}",
            headers=superuser_token_headers,
            json=update_data,
        )
        assert r.status_code == 200
        updated_board = r.json()
        assert updated_board["name"] == "Updated Board Name"
        assert updated_board["background_image"] == "blue"

    def test_delete_board(
        self, client: TestClient, superuser_token_headers: dict[str, str]
    ) -> None:
        """Test deleting a board."""
        # Create workspace and board
        workspace_data = {"name": f"Delete Test Workspace {random_lower_string()[:8]}"}
        r = client.post(
            f"{settings.API_V1_STR}/workspaces/",
            headers=superuser_token_headers,
            json=workspace_data,
        )
        workspace = r.json()

        board_data = {
            "name": "Board To Delete",
            "workspace_id": workspace["id"],
        }
        r = client.post(
            f"{settings.API_V1_STR}/boards/",
            headers=superuser_token_headers,
            json=board_data,
        )
        board = r.json()

        # Delete the board
        r = client.delete(
            f"{settings.API_V1_STR}/boards/{board['id']}",
            headers=superuser_token_headers,
        )
        assert r.status_code == 200

        # Verify it's deleted
        r = client.get(
            f"{settings.API_V1_STR}/boards/{board['id']}",
            headers=superuser_token_headers,
        )
        assert r.status_code == 404

    def test_create_board_unauthorized(self, client: TestClient) -> None:
        """Test that unauthorized users cannot create boards."""
        board_data = {
            "name": "Unauthorized Board",
            "workspace_id": "some-uuid",
        }
        r = client.post(
            f"{settings.API_V1_STR}/boards/",
            json=board_data,
        )
        assert r.status_code == 401

    def test_read_board_not_found(
        self, client: TestClient, superuser_token_headers: dict[str, str]
    ) -> None:
        """Test reading a non-existent board."""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        r = client.get(
            f"{settings.API_V1_STR}/boards/{fake_uuid}",
            headers=superuser_token_headers,
        )
        assert r.status_code == 404
