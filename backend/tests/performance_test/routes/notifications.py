"""
Notifications endpoint tests.
Covers: /notifications/*
"""
import random

from locust import task, tag, between

from .base import AuthenticatedBaseUser


class NotificationAPIUser(AuthenticatedBaseUser):
    """Tests for notification endpoints."""
    wait_time = between(1, 2)
    weight = 2

    notification_ids = []

    @task(5)
    @tag('notifications')
    def list_notifications(self):
        """Test GET /notifications/"""
        response = self.auth_get("/api/v1/notifications/", name="[Notifications] List")
        if response and response.status_code == 200:
            try:
                data = response.json()
                self.notification_ids = [n["id"] for n in data.get("data", [])]
            except Exception:
                pass

    @task(3)
    @tag('notifications')
    def list_unread_only(self):
        """Test GET /notifications/?unread_only=true"""
        self.auth_get(
            "/api/v1/notifications/?unread_only=true",
            name="[Notifications] Unread Only"
        )

    @task(4)
    @tag('notifications')
    def get_unread_count(self):
        """Test GET /notifications/unread-count"""
        self.auth_get(
            "/api/v1/notifications/unread-count",
            name="[Notifications] Unread Count"
        )

    @task(2)
    @tag('notifications')
    def get_notification(self):
        """Test GET /notifications/{id}"""
        if self.notification_ids:
            notification_id = random.choice(self.notification_ids)
            self.auth_get(
                f"/api/v1/notifications/{notification_id}",
                name="[Notifications] Get One"
            )

    @task(2)
    @tag('notifications', 'read')
    def mark_as_read(self):
        """Test PUT /notifications/{id}/read"""
        if self.notification_ids:
            notification_id = random.choice(self.notification_ids)
            self.auth_put(
                f"/api/v1/notifications/{notification_id}/read",
                name="[Notifications] Mark Read"
            )

    @task(1)
    @tag('notifications', 'read')
    def mark_all_as_read(self):
        """Test PUT /notifications/read-all"""
        self.auth_put(
            "/api/v1/notifications/read-all",
            name="[Notifications] Mark All Read"
        )
