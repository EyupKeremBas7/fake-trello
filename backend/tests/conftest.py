from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, delete

from app.core.config import settings
from app.core.db import engine, init_db
from app.main import app
from app.models import User, Workspace, Board, BoardList, Card, ChecklistItem, CardComment
from app.models.workspace_members import WorkspaceMember
from tests.utils.user import authentication_token_from_email, create_random_user
from tests.utils.utils import get_superuser_token_headers


@pytest.fixture(scope="session", autouse=True)
def db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        init_db(session)
        yield session
        # Cleanup in reverse order of dependencies
        session.execute(delete(CardComment))
        session.execute(delete(ChecklistItem))
        session.execute(delete(Card))
        session.execute(delete(BoardList))
        session.execute(delete(Board))
        session.execute(delete(WorkspaceMember))
        session.execute(delete(Workspace))
        session.execute(delete(User))
        session.commit()


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def superuser_token_headers(client: TestClient) -> dict[str, str]:
    return get_superuser_token_headers(client)


@pytest.fixture(scope="module")
def normal_user_token_headers(client: TestClient, db: Session) -> dict[str, str]:
    return authentication_token_from_email(
        client=client, email=settings.EMAIL_TEST_USER, db=db
    )


@pytest.fixture(scope="function")
def test_user(db: Session) -> User:
    """Create a fresh test user for each test function."""
    return create_random_user(db)


@pytest.fixture(scope="module")
def test_workspace(client: TestClient, superuser_token_headers: dict) -> dict:
    """Create a test workspace for the module."""
    data = {"name": "Test Workspace", "description": "A test workspace"}
    response = client.post(
        f"{settings.API_V1_STR}/workspaces/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    return response.json()


@pytest.fixture(scope="module")
def test_board(
    client: TestClient, superuser_token_headers: dict, test_workspace: dict
) -> dict:
    """Create a test board for the module."""
    data = {
        "name": "Test Board",
        "description": "A test board",
        "workspace_id": test_workspace["id"],
    }
    response = client.post(
        f"{settings.API_V1_STR}/boards/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    return response.json()


@pytest.fixture(scope="module")
def test_list(
    client: TestClient, superuser_token_headers: dict, test_board: dict
) -> dict:
    """Create a test list for the module."""
    data = {
        "name": "Test List",
        "board_id": test_board["id"],
    }
    response = client.post(
        f"{settings.API_V1_STR}/lists/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    return response.json()


@pytest.fixture(scope="module")
def test_card(
    client: TestClient, superuser_token_headers: dict, test_list: dict
) -> dict:
    """Create a test card for the module."""
    data = {
        "title": "Test Card",
        "description": "A test card",
        "list_id": test_list["id"],
    }
    response = client.post(
        f"{settings.API_V1_STR}/cards/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    return response.json()
