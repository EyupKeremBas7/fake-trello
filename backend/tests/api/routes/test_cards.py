"""
Test cases for Card API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from tests.utils.utils import random_lower_string


class TestCardsAPI:
    """Test suite for /cards endpoints."""

    @pytest.fixture
    def list_with_board(
        self, client: TestClient, superuser_token_headers: dict[str, str]
    ) -> dict:
        """Create a workspace, board, and list for testing cards."""
        # Create workspace
        workspace_data = {"name": f"Card Test Workspace {random_lower_string()[:8]}"}
        r = client.post(
            f"{settings.API_V1_STR}/workspaces/",
            headers=superuser_token_headers,
            json=workspace_data,
        )
        workspace = r.json()

        # Create board
        board_data = {
            "name": f"Card Test Board {random_lower_string()[:8]}",
            "workspace_id": workspace["id"],
        }
        r = client.post(
            f"{settings.API_V1_STR}/boards/",
            headers=superuser_token_headers,
            json=board_data,
        )
        board = r.json()

        # Create list
        list_data = {
            "name": "To Do",
            "board_id": board["id"],
        }
        r = client.post(
            f"{settings.API_V1_STR}/lists/",
            headers=superuser_token_headers,
            json=list_data,
        )
        return r.json()

    def test_create_card(
        self,
        client: TestClient,
        superuser_token_headers: dict[str, str],
        list_with_board: dict,
    ) -> None:
        """Test creating a new card."""
        card_data = {
            "title": "Test Card",
            "list_id": list_with_board["id"],
        }
        r = client.post(
            f"{settings.API_V1_STR}/cards/",
            headers=superuser_token_headers,
            json=card_data,
        )
        assert r.status_code == 200
        card = r.json()
        assert card["title"] == "Test Card"
        assert card["list_id"] == list_with_board["id"]

    def test_create_card_with_description(
        self,
        client: TestClient,
        superuser_token_headers: dict[str, str],
        list_with_board: dict,
    ) -> None:
        """Test creating a card with description."""
        card_data = {
            "title": "Card with Description",
            "description": "This is a detailed description of the card.",
            "list_id": list_with_board["id"],
        }
        r = client.post(
            f"{settings.API_V1_STR}/cards/",
            headers=superuser_token_headers,
            json=card_data,
        )
        assert r.status_code == 200
        card = r.json()
        assert card["description"] == "This is a detailed description of the card."

    def test_create_card_sanitizes_title(
        self,
        client: TestClient,
        superuser_token_headers: dict[str, str],
        list_with_board: dict,
    ) -> None:
        """Test that card titles are sanitized."""
        card_data = {
            "title": "<script>alert('xss')</script>My Card",
            "list_id": list_with_board["id"],
        }
        r = client.post(
            f"{settings.API_V1_STR}/cards/",
            headers=superuser_token_headers,
            json=card_data,
        )
        assert r.status_code == 200
        card = r.json()
        assert "<script>" not in card["title"]
        assert "My Card" in card["title"]

    def test_create_card_sanitizes_description_allows_safe_html(
        self,
        client: TestClient,
        superuser_token_headers: dict[str, str],
        list_with_board: dict,
    ) -> None:
        """Test that card descriptions allow safe HTML but strip dangerous tags."""
        card_data = {
            "title": "Card with HTML",
            "description": "<p>This is <strong>bold</strong> and <script>alert('xss')</script>safe.</p>",
            "list_id": list_with_board["id"],
        }
        r = client.post(
            f"{settings.API_V1_STR}/cards/",
            headers=superuser_token_headers,
            json=card_data,
        )
        assert r.status_code == 200
        card = r.json()
        # Script should be stripped, but p and strong should remain
        assert "<script>" not in card["description"]
        assert "<strong>" in card["description"] or "bold" in card["description"]

    def test_read_cards(
        self,
        client: TestClient,
        superuser_token_headers: dict[str, str],
    ) -> None:
        """Test listing all cards."""
        r = client.get(
            f"{settings.API_V1_STR}/cards/",
            headers=superuser_token_headers,
        )
        assert r.status_code == 200
        data = r.json()
        assert "data" in data
        assert "count" in data

    def test_update_card(
        self,
        client: TestClient,
        superuser_token_headers: dict[str, str],
        list_with_board: dict,
    ) -> None:
        """Test updating a card."""
        # Create card
        card_data = {
            "title": "Original Title",
            "list_id": list_with_board["id"],
        }
        r = client.post(
            f"{settings.API_V1_STR}/cards/",
            headers=superuser_token_headers,
            json=card_data,
        )
        card = r.json()

        # Update card
        update_data = {
            "title": "Updated Title",
            "description": "Added description",
        }
        r = client.patch(
            f"{settings.API_V1_STR}/cards/{card['id']}",
            headers=superuser_token_headers,
            json=update_data,
        )
        assert r.status_code == 200
        updated_card = r.json()
        assert updated_card["title"] == "Updated Title"
        assert updated_card["description"] == "Added description"

    def test_update_card_position(
        self,
        client: TestClient,
        superuser_token_headers: dict[str, str],
        list_with_board: dict,
    ) -> None:
        """Test updating card position (for drag and drop)."""
        # Create two cards
        card1_data = {"title": "Card 1", "list_id": list_with_board["id"], "position": 65535}
        card2_data = {"title": "Card 2", "list_id": list_with_board["id"], "position": 131070}

        r = client.post(
            f"{settings.API_V1_STR}/cards/",
            headers=superuser_token_headers,
            json=card1_data,
        )
        card1 = r.json()

        r = client.post(
            f"{settings.API_V1_STR}/cards/",
            headers=superuser_token_headers,
            json=card2_data,
        )
        card2 = r.json()

        # Move card2 before card1
        update_data = {"position": 32767.5}  # Between 0 and card1's position
        r = client.patch(
            f"{settings.API_V1_STR}/cards/{card2['id']}",
            headers=superuser_token_headers,
            json=update_data,
        )
        assert r.status_code == 200
        updated_card2 = r.json()
        assert updated_card2["position"] < card1["position"]

    def test_move_card_to_different_list(
        self,
        client: TestClient,
        superuser_token_headers: dict[str, str],
        list_with_board: dict,
    ) -> None:
        """Test moving a card to a different list."""
        # Create another list
        list2_data = {
            "name": "Done",
            "board_id": list_with_board["board_id"],
        }
        r = client.post(
            f"{settings.API_V1_STR}/lists/",
            headers=superuser_token_headers,
            json=list2_data,
        )
        list2 = r.json()

        # Create card in first list
        card_data = {"title": "Card to Move", "list_id": list_with_board["id"]}
        r = client.post(
            f"{settings.API_V1_STR}/cards/",
            headers=superuser_token_headers,
            json=card_data,
        )
        card = r.json()

        # Move card to second list
        update_data = {"list_id": list2["id"]}
        r = client.patch(
            f"{settings.API_V1_STR}/cards/{card['id']}",
            headers=superuser_token_headers,
            json=update_data,
        )
        assert r.status_code == 200
        updated_card = r.json()
        assert updated_card["list_id"] == list2["id"]

    def test_delete_card(
        self,
        client: TestClient,
        superuser_token_headers: dict[str, str],
        list_with_board: dict,
    ) -> None:
        """Test deleting a card."""
        # Create card
        card_data = {"title": "Card to Delete", "list_id": list_with_board["id"]}
        r = client.post(
            f"{settings.API_V1_STR}/cards/",
            headers=superuser_token_headers,
            json=card_data,
        )
        card = r.json()

        # Delete card
        r = client.delete(
            f"{settings.API_V1_STR}/cards/{card['id']}",
            headers=superuser_token_headers,
        )
        assert r.status_code == 200

    def test_create_card_unauthorized(self, client: TestClient) -> None:
        """Test that unauthorized users cannot create cards."""
        card_data = {"title": "Unauthorized Card", "list_id": "some-uuid"}
        r = client.post(f"{settings.API_V1_STR}/cards/", json=card_data)
        assert r.status_code == 401
