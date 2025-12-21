"""
Comments endpoint tests.
Covers: /comments/*
"""
import random

from locust import task, tag, between

from .base import AuthenticatedBaseUser, random_string


class CommentAPIUser(AuthenticatedBaseUser):
    """Tests for comment endpoints."""
    wait_time = between(1, 2)
    weight = 2

    comment_ids = []
    card_ids = []

    def on_start(self):
        """Login and get resources."""
        super().on_start()
        # Get cards for comment creation
        response = self.auth_get("/api/v1/cards/", name="[Comments] Init Cards")
        if response and response.status_code == 200:
            try:
                data = response.json()
                self.card_ids = [c["id"] for c in data.get("data", [])]
            except Exception:
                pass

    @task(5)
    @tag('comments')
    def list_comments(self):
        """Test GET /comments/"""
        response = self.auth_get("/api/v1/comments/", name="[Comments] List")
        if response and response.status_code == 200:
            try:
                data = response.json()
                self.comment_ids = [c["id"] for c in data.get("data", [])]
            except Exception:
                pass

    @task(3)
    @tag('comments')
    def list_by_card(self):
        """Test GET /comments/?card_id={card_id}"""
        if self.card_ids:
            card_id = random.choice(self.card_ids)
            self.auth_get(
                f"/api/v1/comments/?card_id={card_id}",
                name="[Comments] By Card"
            )

    @task(2)
    @tag('comments')
    def get_comment(self):
        """Test GET /comments/{id}"""
        if self.comment_ids:
            comment_id = random.choice(self.comment_ids)
            self.auth_get(
                f"/api/v1/comments/{comment_id}",
                name="[Comments] Get One"
            )

    @task(1)
    @tag('comments', 'create')
    def create_comment(self):
        """Test POST /comments/"""
        if self.card_ids:
            card_id = random.choice(self.card_ids)
            response = self.auth_post(
                "/api/v1/comments/",
                name="[Comments] Create",
                json={
                    "content": f"Load test comment {random_string(10)}",
                    "card_id": card_id
                }
            )
            if response and response.status_code == 200:
                try:
                    comment_id = response.json().get("id")
                    if comment_id and comment_id not in self.comment_ids:
                        self.comment_ids.append(comment_id)
                except Exception:
                    pass
