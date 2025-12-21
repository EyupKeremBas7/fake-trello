"""
Checklists endpoint tests.
Covers: /checklists/*
"""
import random

from locust import task, tag, between

from .base import AuthenticatedBaseUser, random_string


class ChecklistAPIUser(AuthenticatedBaseUser):
    """Tests for checklist endpoints."""
    wait_time = between(1, 2)
    weight = 2

    checklist_ids = []
    card_ids = []

    def on_start(self):
        """Login and get resources."""
        super().on_start()
        # Get cards for checklist creation
        response = self.auth_get("/api/v1/cards/", name="[Checklists] Init Cards")
        if response and response.status_code == 200:
            try:
                data = response.json()
                self.card_ids = [c["id"] for c in data.get("data", [])]
            except Exception:
                pass

    @task(5)
    @tag('checklists')
    def list_checklists(self):
        """Test GET /checklists/"""
        response = self.auth_get("/api/v1/checklists/", name="[Checklists] List")
        if response and response.status_code == 200:
            try:
                data = response.json()
                self.checklist_ids = [c["id"] for c in data.get("data", [])]
            except Exception:
                pass

    @task(3)
    @tag('checklists')
    def list_by_card(self):
        """Test GET /checklists/?card_id={card_id}"""
        if self.card_ids:
            card_id = random.choice(self.card_ids)
            self.auth_get(
                f"/api/v1/checklists/?card_id={card_id}",
                name="[Checklists] By Card"
            )

    @task(2)
    @tag('checklists')
    def get_checklist(self):
        """Test GET /checklists/{id}"""
        if self.checklist_ids:
            checklist_id = random.choice(self.checklist_ids)
            self.auth_get(
                f"/api/v1/checklists/{checklist_id}",
                name="[Checklists] Get One"
            )

    @task(1)
    @tag('checklists', 'create')
    def create_checklist(self):
        """Test POST /checklists/"""
        if self.card_ids:
            card_id = random.choice(self.card_ids)
            response = self.auth_post(
                "/api/v1/checklists/",
                name="[Checklists] Create",
                json={
                    "title": f"Load Test Item {random_string(5)}",
                    "card_id": card_id
                }
            )
            if response and response.status_code == 200:
                try:
                    item_id = response.json().get("id")
                    if item_id and item_id not in self.checklist_ids:
                        self.checklist_ids.append(item_id)
                except Exception:
                    pass

    @task(2)
    @tag('checklists', 'toggle')
    def toggle_checklist(self):
        """Test POST /checklists/{id}/toggle"""
        if self.checklist_ids:
            checklist_id = random.choice(self.checklist_ids)
            self.auth_post(
                f"/api/v1/checklists/{checklist_id}/toggle",
                name="[Checklists] Toggle"
            )
