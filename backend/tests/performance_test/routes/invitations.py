"""
Invitations endpoint tests.
Covers: /invitations/*
"""
import random

from locust import task, tag, between

from .base import AuthenticatedBaseUser


class InvitationAPIUser(AuthenticatedBaseUser):
    """Tests for invitation endpoints."""
    wait_time = between(1, 2)
    weight = 1

    invitation_ids = []
    workspace_ids = []

    def on_start(self):
        """Login and get resources."""
        super().on_start()
        # Get workspaces for context
        response = self.auth_get("/api/v1/workspaces/", name="[Invitations] Init Workspaces")
        if response and response.status_code == 200:
            try:
                data = response.json()
                self.workspace_ids = [w["id"] for w in data.get("data", [])]
            except Exception:
                pass

    @task(5)
    @tag('invitations')
    def list_my_invitations(self):
        """Test GET /invitations/"""
        response = self.auth_get("/api/v1/invitations/", name="[Invitations] My List")
        if response and response.status_code == 200:
            try:
                data = response.json()
                if isinstance(data, list):
                    self.invitation_ids = [i["id"] for i in data if i.get("status") == "pending"]
            except Exception:
                pass

    @task(3)
    @tag('invitations')
    def list_sent_invitations(self):
        """Test GET /invitations/sent"""
        self.auth_get("/api/v1/invitations/sent", name="[Invitations] Sent List")

    @task(2)
    @tag('invitations')
    def list_sent_by_workspace(self):
        """Test GET /invitations/sent?workspace_id={id}"""
        if self.workspace_ids:
            workspace_id = random.choice(self.workspace_ids)
            self.auth_get(
                f"/api/v1/invitations/sent?workspace_id={workspace_id}",
                name="[Invitations] Sent By WS"
            )

    @task(1)
    @tag('invitations')
    def list_pending_invitations(self):
        """Test GET /invitations/?status=pending"""
        self.auth_get(
            "/api/v1/invitations/?status=pending",
            name="[Invitations] Pending Only"
        )
