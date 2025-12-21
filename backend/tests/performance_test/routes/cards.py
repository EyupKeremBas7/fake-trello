"""
Cards endpoint tests.
Covers: /cards/*
"""
import random

from locust import task, tag, between

from .base import AuthenticatedBaseUser, random_string


class CardAPIUser(AuthenticatedBaseUser):
    """Tests for card endpoints."""
    wait_time = between(1, 2)
    weight = 3

    def on_start(self):
        """Login and get resources."""
        # Initialize instance-level lists
        self.card_ids = []
        self.list_ids = []
        
        # First login
        super().on_start()
        
        if not self.login_success:
            print("[Cards] Login failed, skipping resource fetch")
            return
            
        # Get lists for card creation
        response = self.auth_get("/api/v1/lists/", name="[Cards] Init Lists")
        if response and response.status_code == 200:
            try:
                data = response.json()
                self.list_ids = [lst["id"] for lst in data.get("data", [])]
                print(f"[Cards] Found {len(self.list_ids)} lists")
            except Exception as e:
                print(f"[Cards] Error parsing lists: {e}")

    @task(5)
    @tag('cards')
    def list_cards(self):
        """Test GET /cards/"""
        response = self.auth_get("/api/v1/cards/", name="[Cards] List")
        if response and response.status_code == 200:
            try:
                data = response.json()
                self.card_ids = [c["id"] for c in data.get("data", [])]
            except Exception:
                pass

    @task(3)
    @tag('cards')
    def get_card(self):
        """Test GET /cards/{id}"""
        if not self.card_ids:
            return  # Skip if no cards
        card_id = random.choice(self.card_ids)
        self.auth_get(f"/api/v1/cards/{card_id}", name="[Cards] Get One")

    @task(1)
    @tag('cards', 'create')
    def create_card(self):
        """Test POST /cards/"""
        if not self.list_ids:
            print("[Cards] No lists available for card creation")
            return  # Skip if no lists
        list_id = random.choice(self.list_ids)
        response = self.auth_post(
            "/api/v1/cards/",
            name="[Cards] Create",
            json={
                "title": f"Load Test Card {random_string(5)}",
                "list_id": list_id,
                "position": random.randint(1, 100)
            }
        )
        if response and response.status_code == 200:
            try:
                card_id = response.json().get("id")
                if card_id and card_id not in self.card_ids:
                    self.card_ids.append(card_id)
            except Exception:
                pass


class CardUpdateUser(AuthenticatedBaseUser):
    """Tests for card update operations."""
    wait_time = between(2, 4)
    weight = 1

    def on_start(self):
        """Login and get cards."""
        self.card_ids = []
        
        super().on_start()
        
        if not self.login_success:
            return
            
        response = self.auth_get("/api/v1/cards/", name="[Cards] Init List")
        if response and response.status_code == 200:
            try:
                data = response.json()
                self.card_ids = [c["id"] for c in data.get("data", [])]
            except Exception:
                pass

    @task
    @tag('cards', 'update')
    def update_card(self):
        """Test PUT /cards/{id}"""
        if not self.card_ids:
            return
        card_id = random.choice(self.card_ids)
        self.auth_put(
            f"/api/v1/cards/{card_id}",
            name="[Cards] Update",
            json={
                "title": f"Updated Card {random_string(5)}",
                "description": f"Updated description {random_string(10)}"
            }
        )


class CardAssigneeUser(AuthenticatedBaseUser):
    """
    Tests for card assignee feature.
    Simulates assigning cards to workspace members.
    """
    wait_time = between(2, 5)
    weight = 2

    def on_start(self):
        """Login and get cards and workspace members."""
        self.card_ids = []
        self.member_ids = []
        self.workspace_ids = []
        
        super().on_start()
        
        if not self.login_success:
            return
        
        # Get cards
        response = self.auth_get("/api/v1/cards/", name="[Assignee] Init Cards")
        if response and response.status_code == 200:
            try:
                data = response.json()
                self.card_ids = [c["id"] for c in data.get("data", [])]
            except Exception:
                pass
        
        # Get workspaces
        response = self.auth_get("/api/v1/workspaces/", name="[Assignee] Init Workspaces")
        if response and response.status_code == 200:
            try:
                data = response.json()
                self.workspace_ids = [w["id"] for w in data.get("data", [])]
            except Exception:
                pass
        
        # Get members from first workspace
        if self.workspace_ids:
            ws_id = self.workspace_ids[0]
            response = self.auth_get(f"/api/v1/workspaces/{ws_id}/members", name="[Assignee] Init Members")
            if response and response.status_code == 200:
                try:
                    data = response.json()
                    self.member_ids = [m["user_id"] for m in data.get("data", [])]
                except Exception:
                    pass

    @task(5)
    @tag('cards', 'assignee')
    def assign_card(self):
        """Test PUT /cards/{id} with assigned_to field."""
        if not self.card_ids or not self.member_ids:
            return
        
        card_id = random.choice(self.card_ids)
        member_id = random.choice(self.member_ids)
        
        self.auth_put(
            f"/api/v1/cards/{card_id}",
            name="[Assignee] Assign Card",
            json={
                "assigned_to": member_id
            }
        )

    @task(3)
    @tag('cards', 'assignee')
    def unassign_card(self):
        """Test PUT /cards/{id} with null assigned_to to remove assignment."""
        if not self.card_ids:
            return
        
        card_id = random.choice(self.card_ids)
        
        self.auth_put(
            f"/api/v1/cards/{card_id}",
            name="[Assignee] Unassign Card",
            json={
                "assigned_to": None
            }
        )

    @task(2)
    @tag('cards', 'assignee')
    def get_card_with_assignee(self):
        """Test GET /cards/{id} to verify assignee info is returned."""
        if not self.card_ids:
            return
        
        card_id = random.choice(self.card_ids)
        response = self.auth_get(f"/api/v1/cards/{card_id}", name="[Assignee] Get Card")
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                # Verify assignee fields are present
                assert "assigned_to" in data
                assert "assignee_full_name" in data
                assert "assignee_email" in data
            except AssertionError:
                response.failure("Card missing assignee fields")
            except Exception:
                pass
