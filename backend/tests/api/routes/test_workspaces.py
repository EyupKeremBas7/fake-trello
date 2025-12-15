"""
Test cases for Workspace API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from tests.utils.utils import random_lower_string


class TestWorkspacesAPI:
    """Test suite for /workspaces endpoints."""

    def test_create_workspace(
        self, client: TestClient, superuser_token_headers: dict[str, str]
    ) -> None:
        """Test creating a new workspace."""
        workspace_data = {
            "name": f"Test Workspace {random_lower_string()[:8]}",
            "description": "A test workspace for our team.",
        }
        r = client.post(
            f"{settings.API_V1_STR}/workspaces/",
            headers=superuser_token_headers,
            json=workspace_data,
        )
        assert r.status_code == 200
        workspace = r.json()
        assert workspace["name"] == workspace_data["name"]
        assert workspace["description"] == workspace_data["description"]
        assert "id" in workspace
        assert "owner_id" in workspace

    def test_create_workspace_sanitizes_input(
        self, client: TestClient, superuser_token_headers: dict[str, str]
    ) -> None:
        """Test that workspace names are sanitized."""
        workspace_data = {
            "name": "<script>alert('xss')</script>My Workspace",
            "description": "<script>evil()</script><p>This is <strong>valid</strong></p>",
        }
        r = client.post(
            f"{settings.API_V1_STR}/workspaces/",
            headers=superuser_token_headers,
            json=workspace_data,
        )
        assert r.status_code == 200
        workspace = r.json()
        # Script tags should be stripped
        assert "<script>" not in workspace["name"]
        assert "<script>" not in workspace["description"]
        # Valid HTML should remain in description
        assert "valid" in workspace["description"]

    def test_read_workspaces(
        self, client: TestClient, superuser_token_headers: dict[str, str]
    ) -> None:
        """Test listing workspaces."""
        r = client.get(
            f"{settings.API_V1_STR}/workspaces/",
            headers=superuser_token_headers,
        )
        assert r.status_code == 200
        data = r.json()
        assert "data" in data
        assert "count" in data
        assert isinstance(data["data"], list)

    def test_read_workspace_by_id(
        self, client: TestClient, superuser_token_headers: dict[str, str]
    ) -> None:
        """Test reading a specific workspace."""
        # Create workspace first
        workspace_data = {"name": f"Specific Workspace {random_lower_string()[:8]}"}
        r = client.post(
            f"{settings.API_V1_STR}/workspaces/",
            headers=superuser_token_headers,
            json=workspace_data,
        )
        workspace = r.json()

        # Read it
        r = client.get(
            f"{settings.API_V1_STR}/workspaces/{workspace['id']}",
            headers=superuser_token_headers,
        )
        assert r.status_code == 200
        fetched = r.json()
        assert fetched["id"] == workspace["id"]
        assert fetched["name"] == workspace["name"]

    def test_update_workspace(
        self, client: TestClient, superuser_token_headers: dict[str, str]
    ) -> None:
        """Test updating a workspace."""
        # Create workspace
        workspace_data = {"name": "Original Workspace Name"}
        r = client.post(
            f"{settings.API_V1_STR}/workspaces/",
            headers=superuser_token_headers,
            json=workspace_data,
        )
        workspace = r.json()

        # Update it
        update_data = {"name": "Updated Workspace Name", "description": "New description"}
        r = client.patch(
            f"{settings.API_V1_STR}/workspaces/{workspace['id']}",
            headers=superuser_token_headers,
            json=update_data,
        )
        assert r.status_code == 200
        updated = r.json()
        assert updated["name"] == "Updated Workspace Name"
        assert updated["description"] == "New description"

    def test_delete_workspace(
        self, client: TestClient, superuser_token_headers: dict[str, str]
    ) -> None:
        """Test deleting a workspace."""
        # Create workspace
        workspace_data = {"name": "Workspace to Delete"}
        r = client.post(
            f"{settings.API_V1_STR}/workspaces/",
            headers=superuser_token_headers,
            json=workspace_data,
        )
        workspace = r.json()

        # Delete it
        r = client.delete(
            f"{settings.API_V1_STR}/workspaces/{workspace['id']}",
            headers=superuser_token_headers,
        )
        assert r.status_code == 200

        # Verify it's deleted
        r = client.get(
            f"{settings.API_V1_STR}/workspaces/{workspace['id']}",
            headers=superuser_token_headers,
        )
        assert r.status_code == 404

    def test_create_workspace_unauthorized(self, client: TestClient) -> None:
        """Test that unauthorized users cannot create workspaces."""
        workspace_data = {"name": "Unauthorized Workspace"}
        r = client.post(
            f"{settings.API_V1_STR}/workspaces/",
            json=workspace_data,
        )
        assert r.status_code == 401

    def test_read_workspace_not_found(
        self, client: TestClient, superuser_token_headers: dict[str, str]
    ) -> None:
        """Test reading a non-existent workspace."""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        r = client.get(
            f"{settings.API_V1_STR}/workspaces/{fake_uuid}",
            headers=superuser_token_headers,
        )
        assert r.status_code == 404

    def test_workspace_with_boards_cascade_delete(
        self, client: TestClient, superuser_token_headers: dict[str, str]
    ) -> None:
        """Test that deleting a workspace cascades to its boards."""
        # Create workspace
        workspace_data = {"name": "Workspace with Boards"}
        r = client.post(
            f"{settings.API_V1_STR}/workspaces/",
            headers=superuser_token_headers,
            json=workspace_data,
        )
        workspace = r.json()

        # Create board
        board_data = {"name": "Board in Workspace", "workspace_id": workspace["id"]}
        r = client.post(
            f"{settings.API_V1_STR}/boards/",
            headers=superuser_token_headers,
            json=board_data,
        )
        board = r.json()

        # Delete workspace
        r = client.delete(
            f"{settings.API_V1_STR}/workspaces/{workspace['id']}",
            headers=superuser_token_headers,
        )
        assert r.status_code == 200

        # Verify board is also deleted
        r = client.get(
            f"{settings.API_V1_STR}/boards/{board['id']}",
            headers=superuser_token_headers,
        )
        assert r.status_code == 404
