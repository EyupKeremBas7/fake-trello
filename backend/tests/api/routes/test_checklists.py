"""
Tests for the checklist items API endpoints.
"""
import uuid
import pytest

from sqlmodel import Session, select
from fastapi.testclient import TestClient

from app.core.config import settings
from app.models import ChecklistItem


class TestChecklistItemsAPI:
    """Tests for checklist items endpoints."""

    def test_create_checklist_item(
        self, client: TestClient, superuser_token_headers: dict, test_card: dict
    ) -> None:
        """Test creating a new checklist item."""
        data = {
            "title": "Test checklist item",
            "card_id": test_card["id"],
        }
        response = client.post(
            f"{settings.API_V1_STR}/checklists/",
            headers=superuser_token_headers,
            json=data,
        )
        assert response.status_code == 200
        content = response.json()
        assert content["title"] == data["title"]
        assert content["card_id"] == test_card["id"]
        assert content["is_completed"] is False
        assert "id" in content

    def test_read_checklist_items(
        self, client: TestClient, superuser_token_headers: dict, test_card: dict
    ) -> None:
        """Test reading checklist items for a card."""
        # First create a checklist item
        data = {
            "title": "Test item",
            "card_id": test_card["id"],
        }
        client.post(
            f"{settings.API_V1_STR}/checklists/",
            headers=superuser_token_headers,
            json=data,
        )

        # Now read items
        response = client.get(
            f"{settings.API_V1_STR}/checklists/",
            headers=superuser_token_headers,
            params={"card_id": test_card["id"]},
        )
        assert response.status_code == 200
        content = response.json()
        assert "data" in content
        assert "count" in content
        assert content["count"] >= 1

    def test_read_checklist_item_by_id(
        self, client: TestClient, superuser_token_headers: dict, test_card: dict
    ) -> None:
        """Test reading a specific checklist item."""
        # Create item
        data = {
            "title": "Test item for read",
            "card_id": test_card["id"],
        }
        create_response = client.post(
            f"{settings.API_V1_STR}/checklists/",
            headers=superuser_token_headers,
            json=data,
        )
        item_id = create_response.json()["id"]

        # Read by ID
        response = client.get(
            f"{settings.API_V1_STR}/checklists/{item_id}",
            headers=superuser_token_headers,
        )
        assert response.status_code == 200
        content = response.json()
        assert content["id"] == item_id
        assert content["title"] == data["title"]

    def test_update_checklist_item(
        self, client: TestClient, superuser_token_headers: dict, test_card: dict
    ) -> None:
        """Test updating a checklist item."""
        # Create item
        data = {
            "title": "Item to update",
            "card_id": test_card["id"],
        }
        create_response = client.post(
            f"{settings.API_V1_STR}/checklists/",
            headers=superuser_token_headers,
            json=data,
        )
        item_id = create_response.json()["id"]

        # Update item
        update_data = {"title": "Updated title", "is_completed": True}
        response = client.patch(
            f"{settings.API_V1_STR}/checklists/{item_id}",
            headers=superuser_token_headers,
            json=update_data,
        )
        assert response.status_code == 200
        content = response.json()
        assert content["title"] == "Updated title"
        assert content["is_completed"] is True

    def test_delete_checklist_item(
        self, client: TestClient, superuser_token_headers: dict, test_card: dict
    ) -> None:
        """Test deleting a checklist item."""
        # Create item
        data = {
            "title": "Item to delete",
            "card_id": test_card["id"],
        }
        create_response = client.post(
            f"{settings.API_V1_STR}/checklists/",
            headers=superuser_token_headers,
            json=data,
        )
        item_id = create_response.json()["id"]

        # Delete item
        response = client.delete(
            f"{settings.API_V1_STR}/checklists/{item_id}",
            headers=superuser_token_headers,
        )
        assert response.status_code == 200

        # Verify deleted
        response = client.get(
            f"{settings.API_V1_STR}/checklists/{item_id}",
            headers=superuser_token_headers,
        )
        assert response.status_code == 404

    def test_create_checklist_item_nonexistent_card(
        self, client: TestClient, superuser_token_headers: dict
    ) -> None:
        """Test creating a checklist item for nonexistent card fails."""
        data = {
            "title": "Test item",
            "card_id": str(uuid.uuid4()),
        }
        response = client.post(
            f"{settings.API_V1_STR}/checklists/",
            headers=superuser_token_headers,
            json=data,
        )
        assert response.status_code == 404

    def test_read_nonexistent_checklist_item(
        self, client: TestClient, superuser_token_headers: dict
    ) -> None:
        """Test reading nonexistent checklist item returns 404."""
        response = client.get(
            f"{settings.API_V1_STR}/checklists/{uuid.uuid4()}",
            headers=superuser_token_headers,
        )
        assert response.status_code == 404

    def test_checklist_item_xss_prevention(
        self, client: TestClient, superuser_token_headers: dict, test_card: dict
    ) -> None:
        """Test that XSS is prevented in checklist item titles."""
        malicious_title = "<script>alert('xss')</script>Normal title"
        data = {
            "title": malicious_title,
            "card_id": test_card["id"],
        }
        response = client.post(
            f"{settings.API_V1_STR}/checklists/",
            headers=superuser_token_headers,
            json=data,
        )
        assert response.status_code == 200
        content = response.json()
        # Script tag should be stripped
        assert "<script>" not in content["title"]
        assert "alert" not in content["title"]
        assert "Normal title" in content["title"]
