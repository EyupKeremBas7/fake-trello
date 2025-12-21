"""
Auth (Login/Password) endpoint tests.
Covers: /login/*, /password-recovery/*, /reset-password/
"""
from locust import task, tag, between

from .base import BaseUser, AuthenticatedBaseUser, ADMIN_EMAIL, ADMIN_PASSWORD


class LoginUser(BaseUser):
    """Tests for login endpoints."""
    wait_time = between(1, 2)
    weight = 2

    @task(3)
    @tag('auth', 'login')
    def login_valid(self):
        """Test login with valid credentials."""
        self.client.post(
            "/api/v1/login/access-token",
            data={
                "username": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            },
            name="[Auth] Login Valid"
        )

    @task(1)
    @tag('auth', 'login')
    def login_invalid(self):
        """Test login with invalid credentials (expected to fail with 400)."""
        with self.client.post(
            "/api/v1/login/access-token",
            data={
                "username": "invalid@example.com",
                "password": "wrongpassword"
            },
            name="[Auth] Login Invalid",
            catch_response=True
        ) as response:
            if response.status_code == 400:
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")


class TokenTestUser(AuthenticatedBaseUser):
    """Tests for token validation endpoints."""
    wait_time = between(1, 2)
    weight = 1

    @task
    @tag('auth', 'token')
    def test_token(self):
        """Test POST /login/test-token"""
        self.auth_post("/api/v1/login/test-token", name="[Auth] Test Token")


class PasswordRecoveryUser(BaseUser):
    """Tests for password recovery endpoints (simulated, not actual recovery)."""
    wait_time = between(2, 4)
    weight = 1

    @task
    @tag('auth', 'password')
    def password_recovery_invalid(self):
        """Test password recovery with non-existent email (expected 404)."""
        with self.client.post(
            "/api/v1/password-recovery/nonexistent@test.com",
            name="[Auth] Password Recovery",
            catch_response=True
        ) as response:
            if response.status_code == 404:
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")
