"""
Locust Performance Tests for Fake Trello API.

This is the main entry point that imports all endpoint test modules.
Locust will automatically discover all HttpUser subclasses from the imports.

Run with:
    locust -f locustfile.py --host=http://backend:8000

Or headless mode:
    locust -f locustfile.py --host=http://backend:8000 --headless -u 10 -r 2 -t 30s

Available tags for selective testing:
    locust -f locustfile.py --tags health
    locust -f locustfile.py --tags auth
    locust -f locustfile.py --tags users workspaces
    locust -f locustfile.py --tags boards cards
"""

# Import all route modules - Locust will auto-discover HttpUser classes
from routes.auth import LoginUser, TokenTestUser, PasswordRecoveryUser
from routes.oauth import OAuthStatusUser
from routes.users import UserAPIUser, UserSignupUser, UserUpdateUser
from routes.workspaces import WorkspaceAPIUser, WorkspaceUpdateUser
from routes.boards import BoardAPIUser, BoardUpdateUser
from routes.lists import ListAPIUser, ListUpdateUser
from routes.cards import CardAPIUser, CardUpdateUser, CardAssigneeUser
from routes.checklists import ChecklistAPIUser
from routes.comments import CommentAPIUser
from routes.notifications import NotificationAPIUser
from routes.invitations import InvitationAPIUser
from routes.activity import ActivityAPIUser
from routes.uploads import UploadsAPIUser, UploadImageUser

# Also import base utilities for direct access if needed
from routes.base import (
    BaseUser,
    AuthenticatedBaseUser,
    random_email,
    random_string,
    ADMIN_EMAIL,
    ADMIN_PASSWORD,
)

# Health check user (public endpoint, no auth)
from locust import task, tag, between
from routes.base import BaseUser


class HealthCheckUser(BaseUser):
    """Tests for public health check endpoint."""
    wait_time = between(0.5, 1)
    weight = 3

    @task
    @tag('health', 'public')
    def health_check(self):
        """Test GET /utils/health-check/"""
        self.client.get("/api/v1/utils/health-check/", name="[Health] Check")


class MixedLoadUser(AuthenticatedBaseUser):
    """
    Simulates realistic user behavior with mixed endpoint usage.
    Weights reflect typical usage patterns.
    """
    wait_time = between(1, 3)
    weight = 5

    @task(10)
    @tag('mixed')
    def browse_workspaces(self):
        """Browse workspaces - common action."""
        self.auth_get("/api/v1/workspaces/", name="[Mixed] Workspaces")

    @task(8)
    @tag('mixed')
    def browse_boards(self):
        """Browse boards - common action."""
        self.auth_get("/api/v1/boards/", name="[Mixed] Boards")

    @task(6)
    @tag('mixed')
    def browse_cards(self):
        """Browse cards - common action."""
        self.auth_get("/api/v1/cards/", name="[Mixed] Cards")

    @task(5)
    @tag('mixed')
    def check_notifications(self):
        """Check notifications - frequent action."""
        self.auth_get("/api/v1/notifications/", name="[Mixed] Notifications")

    @task(3)
    @tag('mixed')
    def get_profile(self):
        """Get own profile."""
        self.auth_get("/api/v1/users/me", name="[Mixed] Profile")

    @task(1)
    @tag('mixed', 'health')
    def health_check(self):
        """Occasional health check."""
        self.client.get("/api/v1/utils/health-check/", name="[Mixed] Health")
