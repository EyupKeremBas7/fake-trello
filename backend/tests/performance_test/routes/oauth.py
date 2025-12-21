"""
OAuth endpoint tests.
Covers: /oauth/*
"""
from locust import task, tag, between

from .base import BaseUser


class OAuthStatusUser(BaseUser):
    """Tests for OAuth status endpoint (public)."""
    wait_time = between(1, 2)
    weight = 1

    @task
    @tag('oauth', 'public')
    def oauth_status(self):
        """Test GET /oauth/status"""
        self.client.get("/api/v1/oauth/status", name="[OAuth] Status")

    @task
    @tag('oauth')
    def oauth_google_login_check(self):
        """Test GET /oauth/google/login - should redirect or return error if not configured."""
        with self.client.get(
            "/api/v1/oauth/google/login",
            name="[OAuth] Google Login",
            catch_response=True,
            allow_redirects=False
        ) as response:
            # 302 redirect or 400 if not configured - both are valid
            if response.status_code in [302, 400]:
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")
