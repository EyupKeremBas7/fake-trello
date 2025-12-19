# Performance Tests

This directory contains Locust performance/load tests for the Fake Trello API.

## Prerequisites

Install Locust:
```bash
pip install locust
```

## Running Tests

### Web UI Mode (Recommended)
```bash
cd backend/tests/performance_test
locust -f locustfile.py --host=http://localhost:8000
```
Then open http://localhost:8089 in your browser.

### Headless Mode
```bash
locust -f locustfile.py --host=http://localhost:8000 --headless -u 100 -r 10 -t 60s
```

Parameters:
- `-u 100`: 100 concurrent users
- `-r 10`: Spawn 10 users per second
- `-t 60s`: Run for 60 seconds

### Running Specific Tags
```bash
# Only authentication tests
locust -f locustfile.py --host=http://localhost:8000 --tags auth

# Only workspace tests
locust -f locustfile.py --host=http://localhost:8000 --tags workspaces
```

## Test Classes

| Class | Description | Endpoints |
|-------|-------------|-----------|
| `HealthCheckUser` | Health check endpoint | `/utils/health-check/` |
| `LoginUser` | Authentication | `/login/access-token` |
| `UserAPIUser` | User management | `/users/*` |
| `WorkspaceAPIUser` | Workspace operations | `/workspaces/*` |
| `BoardAPIUser` | Board operations | `/boards/*` |
| `CardAPIUser` | Card operations | `/cards/*` |
| `NotificationAPIUser` | Notifications | `/notifications/*` |
| `OAuthAPIUser` | OAuth endpoints | `/oauth/*` |
| `MixedLoadUser` | Realistic mixed workload | All major endpoints |

## Configuration

Default test user credentials (update in locustfile.py):
- Email: `admin@example.com`
- Password: `changethis`
