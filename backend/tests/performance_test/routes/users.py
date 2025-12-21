"""
Users endpoint tests.
Covers: /users/*
"""
from locust import task, tag, between

from .base import AuthenticatedBaseUser, BaseUser, random_email, random_string


class UserAPIUser(AuthenticatedBaseUser):
    """Tests for user endpoints."""
    wait_time = between(1, 2)
    weight = 3

    @task(5)
    @tag('users')
    def get_current_user(self):
        """Test GET /users/me"""
        self.auth_get("/api/v1/users/me", name="[Users] Get Me")

    @task(2)
    @tag('users', 'admin')
    def list_users(self):
        """Test GET /users/ (admin only)"""
        self.auth_get("/api/v1/users/", name="[Users] List All")

    @task(1)
    @tag('users')
    def get_user_by_id(self):
        """Test GET /users/{id} - get own user by ID"""
        response = self.auth_get("/api/v1/users/me", name="[Users] Get Me for ID")
        if response and response.status_code == 200:
            try:
                user_id = response.json().get("id")
                if user_id:
                    self.auth_get(f"/api/v1/users/{user_id}", name="[Users] Get by ID")
            except Exception:
                pass


class UserSignupUser(BaseUser):
    """Tests for user signup endpoint (no auth required)."""
    wait_time = between(1, 2)
    weight = 1

    @task
    @tag('users', 'signup')
    def signup_user(self):
        """Test POST /users/signup"""
        self.client.post(
            "/api/v1/users/signup",
            json={
                "email": random_email(),
                "password": "testpassword123",
                "full_name": f"Load Test User {random_string(5)}"
            },
            name="[Users] Signup"
        )


class UserUpdateUser(AuthenticatedBaseUser):
    """Tests for user update endpoints."""
    wait_time = between(2, 4)
    weight = 1

    @task(2)
    @tag('users', 'update')
    def update_me(self):
        """Test PATCH /users/me"""
        self.auth_patch(
            "/api/v1/users/me",
            name="[Users] Update Me",
            json={"full_name": f"Updated User {random_string(5)}"}
        )
