"""
Test cases for List (BoardList) API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from tests.utils.utils import random_lower_string


class TestListsAPI:
    """Test suite for /lists endpoints."""

    @pytest.fixture
    def board_with_workspace(
        self, client: TestClient, superuser_token_headers: dict[str, str]
    ) -> dict:
        """Create a workspace and board for testing lists."""
        # Create workspace
        workspace_data = {"name": f"List Test Workspace {random_lower_string()[:8]}"}
        r = client.post(
            f"{settings.API_V1_STR}/workspaces/",
            headers=superuser_token_headers,
            json=workspace_data,
        )
        workspace = r.json()

        # Create board
        board_data = {
            "name": f"List Test Board {random_lower_string()[:8]}",
            "workspace_id": workspace["id"],
        }
        r = client.post(
            f"{settings.API_V1_STR}/boards/",
            headers=superuser_token_headers,
            json=board_data,
        )
        return r.json()

    def test_create_list(
        self,
        client: TestClient,
        superuser_token_headers: dict[str, str],
        board_with_workspace: dict,
    ) -> None:
        """Test creating a new list."""
        list_data = {
            "name": "To Do",
            "board_id": board_with_workspace["id"],
        }
        r = client.post(
            f"{settings.API_V1_STR}/lists/",
            headers=superuser_token_headers,
            json=list_data,
        )
        assert r.status_code == 200
        created_list = r.json()
        assert created_list["name"] == "To Do"
        assert created_list["board_id"] == board_with_workspace["id"]

    def test_create_multiple_lists_with_positions(
        self,
        client: TestClient,
        superuser_token_headers: dict[str, str],
        board_with_workspace: dict,
    ) -> None:
        """Test creating multiple lists with positions."""
        lists = ["To Do", "In Progress", "Done"]
        created_lists = []

        for i, name in enumerate(lists):
            list_data = {
                "name": name,
                "board_id": board_with_workspace["id"],
                "position": (i + 1) * 65535,
            }
            r = client.post(
                f"{settings.API_V1_STR}/lists/",
                headers=superuser_token_headers,
                json=list_data,
            )
            assert r.status_code == 200
            created_lists.append(r.json())

        # Verify positions are correct
        assert created_lists[0]["position"] < created_lists[1]["position"]
        assert created_lists[1]["position"] < created_lists[2]["position"]

    def test_read_lists(
        self,
        client: TestClient,
        superuser_token_headers: dict[str, str],
    ) -> None:
        """Test listing all lists."""
        r = client.get(
            f"{settings.API_V1_STR}/lists/",
            headers=superuser_token_headers,
        )
        assert r.status_code == 200
        data = r.json()
        assert "data" in data
        assert "count" in data

    def test_update_list(
        self,
        client: TestClient,
        superuser_token_headers: dict[str, str],
        board_with_workspace: dict,
    ) -> None:
        """Test updating a list."""
        # Create list
        list_data = {
            "name": "Original Name",
            "board_id": board_with_workspace["id"],
        }
        r = client.post(
            f"{settings.API_V1_STR}/lists/",
            headers=superuser_token_headers,
            json=list_data,
        )
        created_list = r.json()

        # Update list
        update_data = {"name": "Updated Name", "position": 100.0}
        r = client.patch(
            f"{settings.API_V1_STR}/lists/{created_list['id']}",
            headers=superuser_token_headers,
            json=update_data,
        )
        assert r.status_code == 200
        updated_list = r.json()
        assert updated_list["name"] == "Updated Name"
        assert updated_list["position"] == 100.0

    def test_delete_list(
        self,
        client: TestClient,
        superuser_token_headers: dict[str, str],
        board_with_workspace: dict,
    ) -> None:
        """Test deleting a list."""
        # Create list
        list_data = {
            "name": "List To Delete",
            "board_id": board_with_workspace["id"],
        }
        r = client.post(
            f"{settings.API_V1_STR}/lists/",
            headers=superuser_token_headers,
            json=list_data,
        )
        created_list = r.json()

        # Delete list
        r = client.delete(
            f"{settings.API_V1_STR}/lists/{created_list['id']}",
            headers=superuser_token_headers,
        )
        assert r.status_code == 200

    def test_create_list_sanitizes_input(
        self,
        client: TestClient,
        superuser_token_headers: dict[str, str],
        board_with_workspace: dict,
    ) -> None:
        """Test that list names are sanitized."""
        list_data = {
            "name": "<script>alert('xss')</script>My List",
            "board_id": board_with_workspace["id"],
        }
        r = client.post(
            f"{settings.API_V1_STR}/lists/",
            headers=superuser_token_headers,
            json=list_data,
        )
        assert r.status_code == 200
        created_list = r.json()
        assert "<script>" not in created_list["name"]

    def test_create_list_unauthorized(self, client: TestClient) -> None:
        """Test that unauthorized users cannot create lists."""
        list_data = {
            "name": "Unauthorized List",
            "board_id": "some-uuid",
        }
        r = client.post(
            f"{settings.API_V1_STR}/lists/",
            json=list_data,
        )
        assert r.status_code == 401
