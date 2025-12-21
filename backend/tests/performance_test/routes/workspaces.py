"""
Workspaces endpoint tests.
Covers: /workspaces/*
"""
import random

from locust import task, tag, between

from .base import AuthenticatedBaseUser, random_string


class WorkspaceAPIUser(AuthenticatedBaseUser):
    """Tests for workspace endpoints."""
    wait_time = between(1, 2)
    weight = 3

    def on_start(self):
        """Login and initialize."""
        self.workspace_ids = []
        super().on_start()

    @task(5)
    @tag('workspaces')
    def list_workspaces(self):
        """Test GET /workspaces/"""
        response = self.auth_get("/api/v1/workspaces/", name="[Workspaces] List")
        if response and response.status_code == 200:
            try:
                data = response.json()
                self.workspace_ids = [w["id"] for w in data.get("data", [])]
            except Exception:
                pass

    @task(3)
    @tag('workspaces')
    def get_workspace(self):
        """Test GET /workspaces/{id}"""
        if self.workspace_ids:
            workspace_id = random.choice(self.workspace_ids)
            self.auth_get(
                f"/api/v1/workspaces/{workspace_id}",
                name="[Workspaces] Get One"
            )

    @task(2)
    @tag('workspaces', 'members')
    def get_workspace_members(self):
        """Test GET /workspaces/{id}/members"""
        if self.workspace_ids:
            workspace_id = random.choice(self.workspace_ids)
            self.auth_get(
                f"/api/v1/workspaces/{workspace_id}/members",
                name="[Workspaces] Get Members"
            )

    @task(1)
    @tag('workspaces', 'create')
    def create_workspace(self):
        """Test POST /workspaces/"""
        response = self.auth_post(
            "/api/v1/workspaces/",
            name="[Workspaces] Create",
            json={
                "name": f"Load Test WS {random_string(5)}",
                "description": "Created by Locust load test"
            }
        )
        if response and response.status_code == 200:
            try:
                ws_id = response.json().get("id")
                if ws_id and ws_id not in self.workspace_ids:
                    self.workspace_ids.append(ws_id)
            except Exception:
                pass


class WorkspaceUpdateUser(AuthenticatedBaseUser):
    """Tests for workspace update/delete operations."""
    wait_time = between(2, 4)
    weight = 1

    def on_start(self):
        """Login and get workspaces."""
        self.workspace_ids = []
        super().on_start()
        if not self.login_success:
            return
        response = self.auth_get("/api/v1/workspaces/", name="[Workspaces] Init List")
        if response and response.status_code == 200:
            try:
                data = response.json()
                self.workspace_ids = [w["id"] for w in data.get("data", [])]
            except Exception:
                pass

    @task(2)
    @tag('workspaces', 'update')
    def update_workspace(self):
        """Test PUT /workspaces/{id}"""
        if self.workspace_ids:
            workspace_id = random.choice(self.workspace_ids)
            self.auth_put(
                f"/api/v1/workspaces/{workspace_id}",
                name="[Workspaces] Update",
                json={"description": f"Updated by load test {random_string(5)}"}
            )
