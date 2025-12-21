"""
Boards endpoint tests.
Covers: /boards/*
"""
import random

from locust import task, tag, between

from .base import AuthenticatedBaseUser, random_string


class BoardAPIUser(AuthenticatedBaseUser):
    """Tests for board endpoints."""
    wait_time = between(1, 2)
    weight = 3

    def on_start(self):
        """Login and get resources."""
        self.board_ids = []
        self.workspace_ids = []
        super().on_start()
        if not self.login_success:
            return
        # Get workspaces for board creation
        response = self.auth_get("/api/v1/workspaces/", name="[Boards] Init Workspaces")
        if response and response.status_code == 200:
            try:
                data = response.json()
                self.workspace_ids = [w["id"] for w in data.get("data", [])]
            except Exception:
                pass

    @task(5)
    @tag('boards')
    def list_boards(self):
        """Test GET /boards/"""
        response = self.auth_get("/api/v1/boards/", name="[Boards] List")
        if response and response.status_code == 200:
            try:
                data = response.json()
                self.board_ids = [b["id"] for b in data.get("data", [])]
            except Exception:
                pass

    @task(3)
    @tag('boards')
    def get_board(self):
        """Test GET /boards/{id}"""
        if self.board_ids:
            board_id = random.choice(self.board_ids)
            self.auth_get(f"/api/v1/boards/{board_id}", name="[Boards] Get One")

    @task(2)
    @tag('boards', 'lists')
    def get_board_lists(self):
        """Test GET /lists/board/{board_id}"""
        if self.board_ids:
            board_id = random.choice(self.board_ids)
            self.auth_get(
                f"/api/v1/lists/board/{board_id}",
                name="[Boards] Get Lists"
            )

    @task(1)
    @tag('boards', 'create')
    def create_board(self):
        """Test POST /boards/"""
        if self.workspace_ids:
            workspace_id = random.choice(self.workspace_ids)
            response = self.auth_post(
                "/api/v1/boards/",
                name="[Boards] Create",
                json={
                    "name": f"Load Test Board {random_string(5)}",
                    "workspace_id": workspace_id
                }
            )
            if response and response.status_code == 200:
                try:
                    board_id = response.json().get("id")
                    if board_id and board_id not in self.board_ids:
                        self.board_ids.append(board_id)
                except Exception:
                    pass


class BoardUpdateUser(AuthenticatedBaseUser):
    """Tests for board update operations."""
    wait_time = between(2, 4)
    weight = 1

    def on_start(self):
        """Login and get boards."""
        self.board_ids = []
        super().on_start()
        if not self.login_success:
            return
        response = self.auth_get("/api/v1/boards/", name="[Boards] Init List")
        if response and response.status_code == 200:
            try:
                data = response.json()
                self.board_ids = [b["id"] for b in data.get("data", [])]
            except Exception:
                pass

    @task
    @tag('boards', 'update')
    def update_board(self):
        """Test PUT /boards/{id}"""
        if self.board_ids:
            board_id = random.choice(self.board_ids)
            self.auth_put(
                f"/api/v1/boards/{board_id}",
                name="[Boards] Update",
                json={"name": f"Updated Board {random_string(5)}"}
            )
