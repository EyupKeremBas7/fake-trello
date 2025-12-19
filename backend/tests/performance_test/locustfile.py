"""
Locust Performance Tests for Fake Trello API.

Run with:
    locust -f locustfile.py --host=http://backend:8000

Or headless mode:
    locust -f locustfile.py --host=http://backend:8000 --headless -u 10 -r 2 -t 30s

Available tags for selective testing:
    locust -f locustfile.py --tags health
    locust -f locustfile.py --tags auth
    locust -f locustfile.py --tags users workspaces
"""
from locust import HttpUser, task, between, tag
import random
import string
import os

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


# =============================================================================
# BASE CLASSES
# =============================================================================

class BaseUser(HttpUser):
    """Base class with common utilities."""
    abstract = True
    
    def safe_request(self, method, url, name=None, **kwargs):
        """Make a request with automatic error handling."""
        try:
            if method == "GET":
                return self.client.get(url, name=name, **kwargs)
            elif method == "POST":
                return self.client.post(url, name=name, **kwargs)
            elif method == "PUT":
                return self.client.put(url, name=name, **kwargs)
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
    
    def auth_delete(self, url, name=None):
        """Authenticated DELETE request."""
        if not self.login_success:
            return None
        return self.client.delete(url, headers=self.headers, name=name)


# =============================================================================
# PUBLIC ENDPOINT TESTS (No Auth Required)
# =============================================================================

class HealthCheckUser(BaseUser):
    """Tests for public health check endpoint."""
    wait_time = between(0.5, 1)
    weight = 3
    
    @task
    @tag('health', 'public')
    def health_check(self):
        """Test GET /utils/health-check/"""
        self.client.get("/api/v1/utils/health-check/", name="[Health] Check")


class OAuthStatusUser(BaseUser):
    """Tests for OAuth status endpoint."""
    wait_time = between(1, 2)
    weight = 1
    
    @task
    @tag('oauth', 'public')
    def oauth_status(self):
        """Test GET /oauth/status"""
        self.client.get("/api/v1/oauth/status", name="[OAuth] Status")


class LoginUser(BaseUser):
    """Tests for login endpoint."""
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
            # 400 is expected for invalid credentials
            if response.status_code == 400:
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")


# =============================================================================
# USER ENDPOINT TESTS
# =============================================================================

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


# =============================================================================
# WORKSPACE ENDPOINT TESTS
# =============================================================================

class WorkspaceAPIUser(AuthenticatedBaseUser):
    """Tests for workspace endpoints."""
    wait_time = between(1, 2)
    weight = 3
    
    workspace_ids = []
    
    @task(5)
    @tag('workspaces')
    def list_workspaces(self):
        """Test GET /workspaces/"""
        response = self.auth_get("/api/v1/workspaces/", name="[Workspaces] List")
        if response and response.status_code == 200:
            try:
                data = response.json()
                self.workspace_ids = [w["id"] for w in data.get("data", [])]
            except:
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
    @tag('workspaces')
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
        self.auth_post(
            "/api/v1/workspaces/",
            name="[Workspaces] Create",
            json={
                "name": f"Load Test WS {random_string(5)}",
                "description": "Created by Locust load test"
            }
        )


# =============================================================================
# BOARD ENDPOINT TESTS
# =============================================================================

class BoardAPIUser(AuthenticatedBaseUser):
    """Tests for board endpoints."""
    wait_time = between(1, 2)
    weight = 3
    
    board_ids = []
    workspace_ids = []
    
    @task(5)
    @tag('boards')
    def list_boards(self):
        """Test GET /boards/"""
        response = self.auth_get("/api/v1/boards/", name="[Boards] List")
        if response and response.status_code == 200:
            try:
                data = response.json()
                self.board_ids = [b["id"] for b in data.get("data", [])]
            except:
                pass
    
    @task(3)
    @tag('boards')
    def get_board(self):
        """Test GET /boards/{id}"""
        if self.board_ids:
            board_id = random.choice(self.board_ids)
            self.auth_get(f"/api/v1/boards/{board_id}", name="[Boards] Get One")
    
    @task(2)
    @tag('boards')
    def get_board_lists(self):
        """Test GET /lists/board/{board_id}"""
        if self.board_ids:
            board_id = random.choice(self.board_ids)
            self.auth_get(
                f"/api/v1/lists/board/{board_id}",
                name="[Boards] Get Lists"
            )


# =============================================================================
# CARD ENDPOINT TESTS
# =============================================================================

class CardAPIUser(AuthenticatedBaseUser):
    """Tests for card endpoints."""
    wait_time = between(1, 2)
    weight = 3
    
    card_ids = []
    
    @task(5)
    @tag('cards')
    def list_cards(self):
        """Test GET /cards/"""
        response = self.auth_get("/api/v1/cards/", name="[Cards] List")
        if response and response.status_code == 200:
            try:
                data = response.json()
                self.card_ids = [c["id"] for c in data.get("data", [])]
            except:
                pass
    
    @task(3)
    @tag('cards')
    def get_card(self):
        """Test GET /cards/{id}"""
        if self.card_ids:
            card_id = random.choice(self.card_ids)
            self.auth_get(f"/api/v1/cards/{card_id}", name="[Cards] Get One")


# =============================================================================
# NOTIFICATION ENDPOINT TESTS
# =============================================================================

class NotificationAPIUser(AuthenticatedBaseUser):
    """Tests for notification endpoints."""
    wait_time = between(1, 2)
    weight = 2
    
    @task(5)
    @tag('notifications')
    def list_notifications(self):
        """Test GET /notifications/"""
        self.auth_get("/api/v1/notifications/", name="[Notifications] List")
    
    @task(2)
    @tag('notifications')
    def get_unread_count(self):
        """Test GET /notifications/unread-count"""
        self.auth_get(
            "/api/v1/notifications/unread-count",
            name="[Notifications] Unread Count"
        )


# =============================================================================
# INVITATION ENDPOINT TESTS
# =============================================================================

class InvitationAPIUser(AuthenticatedBaseUser):
    """Tests for invitation endpoints."""
    wait_time = between(1, 2)
    weight = 1
    
    @task
    @tag('invitations')
    def list_invitations(self):
        """Test GET /invitations/"""
        self.auth_get("/api/v1/invitations/", name="[Invitations] List")


# =============================================================================
# MIXED LOAD USER (Simulates Real Usage)
# =============================================================================

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
