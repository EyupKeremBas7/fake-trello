"""
Base classes and utilities for Locust performance tests.
"""
import os
import random
import string

from locust import HttpUser, between

# Get credentials from environment or use defaults
ADMIN_EMAIL = os.getenv("FIRST_SUPERUSER", "admin@example.com")
ADMIN_PASSWORD = os.getenv("FIRST_SUPERUSER_PASSWORD", "changethis")


def random_email():
    """Generate a random email."""
    suffix = ''.join(random.choices(string.ascii_lowercase, k=8))
    return f"loadtest_{suffix}@example.com"


def random_string(length=10):
    """Generate a random string."""
    return ''.join(random.choices(string.ascii_letters, k=length))


class BaseUser(HttpUser):
    """Base class with common utilities."""
    abstract = True
    wait_time = between(1, 2)

    def safe_request(self, method, url, name=None, **kwargs):
        """Make a request with automatic error handling."""
        try:
            if method == "GET":
                return self.client.get(url, name=name, **kwargs)
            elif method == "POST":
                return self.client.post(url, name=name, **kwargs)
            elif method == "PUT":
                return self.client.put(url, name=name, **kwargs)
            elif method == "PATCH":
                return self.client.patch(url, name=name, **kwargs)
            elif method == "DELETE":
                return self.client.delete(url, name=name, **kwargs)
        except Exception as e:
            print(f"Request error: {e}")
            return None


class AuthenticatedBaseUser(BaseUser):
    """Base user that handles authentication."""
    abstract = True
    token = None
    headers = {}
    login_success = False

    def on_start(self):
        """Login and get token on start."""
        try:
            response = self.client.post(
                "/api/v1/login/access-token",
                data={
                    "username": ADMIN_EMAIL,
                    "password": ADMIN_PASSWORD
                },
                name="[Auth] Login"
            )
            if response.status_code == 200:
                self.token = response.json().get("access_token")
                self.headers = {"Authorization": f"Bearer {self.token}"}
                self.login_success = True
            else:
                print(f"Login failed: {response.status_code} - {response.text[:100]}")
                self.login_success = False
        except Exception as e:
            print(f"Login error: {e}")
            self.login_success = False

    def auth_get(self, url, name=None):
        """Authenticated GET request."""
        if not self.login_success:
            return None
        return self.client.get(url, headers=self.headers, name=name)

    def auth_post(self, url, name=None, **kwargs):
        """Authenticated POST request."""
        if not self.login_success:
            return None
        return self.client.post(url, headers=self.headers, name=name, **kwargs)

    def auth_put(self, url, name=None, **kwargs):
        """Authenticated PUT request."""
        if not self.login_success:
            return None
        return self.client.put(url, headers=self.headers, name=name, **kwargs)

    def auth_patch(self, url, name=None, **kwargs):
        """Authenticated PATCH request."""
        if not self.login_success:
            return None
        return self.client.patch(url, headers=self.headers, name=name, **kwargs)

    def auth_delete(self, url, name=None):
        """Authenticated DELETE request."""
        if not self.login_success:
            return None
        return self.client.delete(url, headers=self.headers, name=name)
