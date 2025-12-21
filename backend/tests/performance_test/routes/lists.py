"""
Lists endpoint tests.
Covers: /lists/*
"""
import random

from locust import task, tag, between

from .base import AuthenticatedBaseUser, random_string


class ListAPIUser(AuthenticatedBaseUser):
    """Tests for list endpoints."""
    wait_time = between(1, 2)
    weight = 3

    def on_start(self):
        """Login and get resources."""
        self.list_ids = []
        self.board_ids = []
        super().on_start()
        if not self.login_success:
            return
        # Get boards for list creation
        response = self.auth_get("/api/v1/boards/", name="[Lists] Init Boards")
        if response and response.status_code == 200:
            try:
                data = response.json()
                self.board_ids = [b["id"] for b in data.get("data", [])]
            except Exception:
                pass

    @task(5)
    @tag('lists')
    def list_all_lists(self):
        """Test GET /lists/"""
        response = self.auth_get("/api/v1/lists/", name="[Lists] List All")
        if response and response.status_code == 200:
            try:
                data = response.json()
                self.list_ids = [lst["id"] for lst in data.get("data", [])]
            except Exception:
                pass

    @task(3)
    @tag('lists')
    def get_lists_by_board(self):
        """Test GET /lists/board/{board_id}"""
        if self.board_ids:
            board_id = random.choice(self.board_ids)
            self.auth_get(
                f"/api/v1/lists/board/{board_id}",
                name="[Lists] By Board"
            )

    @task(2)
    @tag('lists')
    def get_list(self):
        """Test GET /lists/{id}"""
        if self.list_ids:
            list_id = random.choice(self.list_ids)
            self.auth_get(f"/api/v1/lists/{list_id}", name="[Lists] Get One")

    @task(1)
    @tag('lists', 'create')
    def create_list(self):
        """Test POST /lists/"""
        if self.board_ids:
            board_id = random.choice(self.board_ids)
            response = self.auth_post(
                "/api/v1/lists/",
                name="[Lists] Create",
                json={
                    "name": f"Load Test List {random_string(5)}",
                    "board_id": board_id,
                    "position": random.randint(1, 100)
                }
            )
            if response and response.status_code == 200:
                try:
                    list_id = response.json().get("id")
                    if list_id and list_id not in self.list_ids:
                        self.list_ids.append(list_id)
                except Exception:
                    pass


class ListUpdateUser(AuthenticatedBaseUser):
    """Tests for list update operations."""
    wait_time = between(2, 4)
    weight = 1

    def on_start(self):
        """Login and get lists."""
        self.list_ids = []
        super().on_start()
        if not self.login_success:
            return
        response = self.auth_get("/api/v1/lists/", name="[Lists] Init List")
        if response and response.status_code == 200:
            try:
                data = response.json()
                self.list_ids = [lst["id"] for lst in data.get("data", [])]
            except Exception:
                pass

    @task
    @tag('lists', 'update')
    def update_list(self):
        """Test PUT /lists/{id}"""
        if self.list_ids:
            list_id = random.choice(self.list_ids)
            self.auth_put(
                f"/api/v1/lists/{list_id}",
                name="[Lists] Update",
                json={"name": f"Updated List {random_string(5)}"}
            )
