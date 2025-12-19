# Unit Tests

This directory contains unit tests for the Fake Trello API.

## Prerequisites

Install pytest:
```bash
pip install pytest pytest-cov
```

## Running Tests

### Run All Tests
```bash
cd backend
pytest tests/unit_test -v
```

### Run with Coverage
```bash
pytest tests/unit_test -v --cov=app --cov-report=html
```

### Run Specific Test File
```bash
pytest tests/unit_test/test_users.py -v
```

### Run Specific Test Class
```bash
pytest tests/unit_test/test_users.py::TestCreateUser -v
```

## Test Structure

| File | Description |
|------|-------------|
| `conftest.py` | Shared fixtures and configuration |
| `test_login.py` | Login and authentication tests |
| `test_users.py` | User CRUD operation tests |
| `test_workspaces.py` | Workspace operation tests |
| `test_boards.py` | Board operation tests |
| `test_lists.py` | List operation tests |
| `test_cards.py` | Card operation tests |
| `test_comments.py` | Comment operation tests |
| `test_checklists.py` | Checklist operation tests |
| `test_notifications.py` | Notification tests |
| `test_invitations.py` | Invitation tests |
| `test_oauth.py` | OAuth authentication tests |
| `test_utils.py` | Utility endpoint tests |

## Fixtures

Available fixtures in `conftest.py`:
- `mock_session`: Mock database session
- `mock_user`: Mock regular user
- `mock_superuser`: Mock admin user
- `mock_workspace`: Mock workspace
- `mock_board`: Mock board
- `mock_list`: Mock list
- `mock_card`: Mock card
- `sample_user_data`: Sample user creation data
- `sample_workspace_data`: Sample workspace creation data
- `sample_board_data`: Sample board creation data
- `sample_card_data`: Sample card creation data
