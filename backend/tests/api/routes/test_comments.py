"""
Tests for the comments API endpoints.
"""
import uuid
import pytest

from sqlmodel import Session, select
from fastapi.testclient import TestClient

from app.core.config import settings
from app.models import CardComment


class TestCommentsAPI:
    """Tests for comment endpoints."""

    def test_create_comment(
        self, client: TestClient, superuser_token_headers: dict, test_card: dict
    ) -> None:
        """Test creating a new comment."""
        data = {
            "content": "This is a test comment",
            "card_id": test_card["id"],
        }
        response = client.post(
            f"{settings.API_V1_STR}/comments/",
            headers=superuser_token_headers,
            json=data,
        )
        assert response.status_code == 200
        content = response.json()
        assert content["content"] == data["content"]
        assert content["card_id"] == test_card["id"]
        assert "id" in content
        assert "user_id" in content

    def test_read_comments(
        self, client: TestClient, superuser_token_headers: dict, test_card: dict
    ) -> None:
        """Test reading comments for a card."""
        # First create a comment
        data = {
            "content": "Test comment",
            "card_id": test_card["id"],
        }
        client.post(
            f"{settings.API_V1_STR}/comments/",
            headers=superuser_token_headers,
            json=data,
        )

        # Now read comments
        response = client.get(
            f"{settings.API_V1_STR}/comments/",
            headers=superuser_token_headers,
            params={"card_id": test_card["id"]},
        )
        assert response.status_code == 200
        content = response.json()
        assert "data" in content
        assert "count" in content
        assert content["count"] >= 1

    def test_read_comment_by_id(
        self, client: TestClient, superuser_token_headers: dict, test_card: dict
    ) -> None:
        """Test reading a specific comment."""
        # Create comment
        data = {
            "content": "Comment for read test",
            "card_id": test_card["id"],
        }
        create_response = client.post(
            f"{settings.API_V1_STR}/comments/",
            headers=superuser_token_headers,
            json=data,
        )
        comment_id = create_response.json()["id"]

        # Read by ID
        response = client.get(
            f"{settings.API_V1_STR}/comments/{comment_id}",
            headers=superuser_token_headers,
        )
        assert response.status_code == 200
        content = response.json()
        assert content["id"] == comment_id
        assert content["content"] == data["content"]

    def test_update_comment(
        self, client: TestClient, superuser_token_headers: dict, test_card: dict
    ) -> None:
        """Test updating a comment."""
        # Create comment
        data = {
            "content": "Original content",
            "card_id": test_card["id"],
        }
        create_response = client.post(
            f"{settings.API_V1_STR}/comments/",
            headers=superuser_token_headers,
            json=data,
        )
        comment_id = create_response.json()["id"]

        # Update comment
        update_data = {"content": "Updated content"}
        response = client.patch(
            f"{settings.API_V1_STR}/comments/{comment_id}",
            headers=superuser_token_headers,
            json=update_data,
        )
        assert response.status_code == 200
        content = response.json()
        assert content["content"] == "Updated content"

    def test_delete_comment(
        self, client: TestClient, superuser_token_headers: dict, test_card: dict
    ) -> None:
        """Test deleting a comment."""
        # Create comment
        data = {
            "content": "Comment to delete",
            "card_id": test_card["id"],
        }
        create_response = client.post(
            f"{settings.API_V1_STR}/comments/",
            headers=superuser_token_headers,
            json=data,
        )
        comment_id = create_response.json()["id"]

        # Delete comment
        response = client.delete(
            f"{settings.API_V1_STR}/comments/{comment_id}",
            headers=superuser_token_headers,
        )
        assert response.status_code == 200

        # Verify deleted
        response = client.get(
            f"{settings.API_V1_STR}/comments/{comment_id}",
            headers=superuser_token_headers,
        )
        assert response.status_code == 404

    def test_create_comment_nonexistent_card(
        self, client: TestClient, superuser_token_headers: dict
    ) -> None:
        """Test creating a comment for nonexistent card fails."""
        data = {
            "content": "Test comment",
            "card_id": str(uuid.uuid4()),
        }
        response = client.post(
            f"{settings.API_V1_STR}/comments/",
            headers=superuser_token_headers,
            json=data,
        )
        assert response.status_code == 404

    def test_read_nonexistent_comment(
        self, client: TestClient, superuser_token_headers: dict
    ) -> None:
        """Test reading nonexistent comment returns 404."""
        response = client.get(
            f"{settings.API_V1_STR}/comments/{uuid.uuid4()}",
            headers=superuser_token_headers,
        )
        assert response.status_code == 404

    def test_comment_includes_user_info(
        self, client: TestClient, superuser_token_headers: dict, test_card: dict
    ) -> None:
        """Test that comments include user info."""
        data = {
            "content": "Comment with user info",
            "card_id": test_card["id"],
        }
        create_response = client.post(
            f"{settings.API_V1_STR}/comments/",
            headers=superuser_token_headers,
            json=data,
        )
        assert create_response.status_code == 200
        content = create_response.json()
        # Should include user info
        assert "user_full_name" in content or "user_email" in content

    def test_comment_html_sanitization(
        self, client: TestClient, superuser_token_headers: dict, test_card: dict
    ) -> None:
        """Test that dangerous HTML is sanitized but safe HTML is preserved."""
        malicious_content = "<script>alert('xss')</script><p>Hello <strong>World</strong></p>"
        data = {
            "content": malicious_content,
            "card_id": test_card["id"],
        }
        response = client.post(
            f"{settings.API_V1_STR}/comments/",
            headers=superuser_token_headers,
            json=data,
        )
        assert response.status_code == 200
        content = response.json()["content"]
        # Script should be stripped
        assert "<script>" not in content
        assert "alert" not in content
        # Safe HTML may be preserved (depending on implementation)
        assert "Hello" in content
        assert "World" in content

    def test_comment_xss_event_handler(
        self, client: TestClient, superuser_token_headers: dict, test_card: dict
    ) -> None:
        """Test that event handlers are stripped from comments."""
        malicious_content = '<img src="x" onerror="alert(1)">Some text'
        data = {
            "content": malicious_content,
            "card_id": test_card["id"],
        }
        response = client.post(
            f"{settings.API_V1_STR}/comments/",
            headers=superuser_token_headers,
            json=data,
        )
        assert response.status_code == 200
        content = response.json()["content"]
        # Event handler should be stripped
        assert "onerror" not in content
