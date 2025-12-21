"""
Activity endpoint tests.
Covers: /activity/*
"""
import random

from locust import task, tag, between

from .base import AuthenticatedBaseUser


class ActivityAPIUser(AuthenticatedBaseUser):
    """Tests for activity log endpoints."""
    wait_time = between(1, 2)
    weight = 1

    def on_start(self):
        """Login and get resources."""
        # Initialize instance-level lists
        self.workspace_ids = []
        self.board_ids = []
        self.card_ids = []
        
        # First login
        super().on_start()
        
        if not self.login_success:
            print("[Activity] Login failed, skipping resource fetch")
            return

        # Get workspaces
        response = self.auth_get("/api/v1/workspaces/", name="[Activity] Init Workspaces")
        if response and response.status_code == 200:
            try:
                data = response.json()
                self.workspace_ids = [w["id"] for w in data.get("data", [])]
                print(f"[Activity] Found {len(self.workspace_ids)} workspaces")
            except Exception as e:
                print(f"[Activity] Error parsing workspaces: {e}")

        # Get boards
        response = self.auth_get("/api/v1/boards/", name="[Activity] Init Boards")
        if response and response.status_code == 200:
            try:
                data = response.json()
                self.board_ids = [b["id"] for b in data.get("data", [])]
                print(f"[Activity] Found {len(self.board_ids)} boards")
            except Exception as e:
                print(f"[Activity] Error parsing boards: {e}")

        # Get cards
        response = self.auth_get("/api/v1/cards/", name="[Activity] Init Cards")
        if response and response.status_code == 200:
            try:
                data = response.json()
                self.card_ids = [c["id"] for c in data.get("data", [])]
                print(f"[Activity] Found {len(self.card_ids)} cards")
            except Exception as e:
                print(f"[Activity] Error parsing cards: {e}")

    @task(3)
    @tag('activity')
    def get_board_activity(self):
        """Test GET /activity/board/{board_id}"""
        if not self.board_ids:
            return  # Skip if no boards
        board_id = random.choice(self.board_ids)
        self.auth_get(
            f"/api/v1/activity/board/{board_id}",
            name="[Activity] Board"
        )

    @task(2)
    @tag('activity')
    def get_workspace_activity(self):
        """Test GET /activity/workspace/{workspace_id}"""
        if not self.workspace_ids:
            return  # Skip if no workspaces
        workspace_id = random.choice(self.workspace_ids)
        self.auth_get(
            f"/api/v1/activity/workspace/{workspace_id}",
            name="[Activity] Workspace"
        )

    @task(2)
    @tag('activity')
    def get_card_activity(self):
        """Test GET /activity/card/{card_id}"""
        if not self.card_ids:
            return  # Skip if no cards
        card_id = random.choice(self.card_ids)
        self.auth_get(
            f"/api/v1/activity/card/{card_id}",
            name="[Activity] Card"
        )
