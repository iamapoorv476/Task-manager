"""Shared pytest fixtures.

Sets required environment variables BEFORE any app module is imported,
so `app.core.config.get_settings()` picks up test values (a dedicated
test database, a throwaway secret key) rather than reading `.env`. This
means the test suite is self-contained and doesn't depend on the
developer's local `.env` file existing or having any particular values.
"""

import os
import uuid
from collections.abc import Generator

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5432/task_manager_test",
)
os.environ.setdefault("SECRET_KEY", "test-only-secret-key-not-used-anywhere-real-1234567890")
os.environ.setdefault("ENVIRONMENT", "testing")
os.environ.setdefault("CORS_ORIGINS", '["http://localhost:5173"]')

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402

from app.db.base import Base  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.main import create_app  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402

import app.models  # noqa: E402,F401  (registers all models on Base.metadata)

_engine = create_engine(os.environ["DATABASE_URL"])
_TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


@pytest.fixture(scope="session", autouse=True)
def _create_test_schema() -> Generator[None, None, None]:
    """Creates all tables once for the whole test session, drops them at
    the end. Assumes the `task_manager_test` database itself already
    exists (see README testing instructions) -- creating/dropping the
    *database* is a one-time manual step, not something tests do."""
    Base.metadata.create_all(bind=_engine)
    yield
    Base.metadata.drop_all(bind=_engine)


@pytest.fixture
def db() -> Generator[Session, None, None]:
    """A fresh session per test. Tables are wiped at the START of each
    test (not the end) so a failed test's leftover data doesn't cause
    the NEXT test to fail confusingly -- you always start from a known
    empty state, and a failure's data is left in place for inspection.
    """
    session = _TestSessionLocal()
    session.execute(app.models.task.Task.__table__.delete())
    session.execute(app.models.user.User.__table__.delete())
    session.commit()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db: Session) -> Generator[TestClient, None, None]:
    """TestClient wired to use the SAME db session as the test itself,
    via FastAPI's dependency_overrides. This means assertions in the
    test can query `db` directly and see exactly what the API call
    just wrote, with no session/connection mismatch."""
    app = create_app()
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _unique_email(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}@example.com"


@pytest.fixture
def make_user(client: TestClient, db: Session):
    """Factory fixture: register + log in a user, return (user, headers).
    Using a factory (rather than one fixed fixture) lets a single test
    create multiple distinct users, which is essential for testing
    ownership rules.
    """

    def _make(*, role: UserRole = UserRole.USER, password: str = "SecurePass123") -> tuple[User, dict[str, str]]:
        email = _unique_email("user")
        client.post(
            "/api/v1/auth/register",
            json={"name": "Test User", "email": email, "password": password},
        )
        login = client.post("/api/v1/auth/login", data={"username": email, "password": password})
        token = login.json()["data"]["access_token"]

        user = db.query(User).filter(User.email == email).one()
        if role == UserRole.ADMIN:
            user.role = UserRole.ADMIN
            db.commit()
            db.refresh(user)

        return user, {"Authorization": f"Bearer {token}"}

    return _make


@pytest.fixture
def regular_user(make_user):
    return make_user(role=UserRole.USER)


@pytest.fixture
def admin_user(make_user):
    return make_user(role=UserRole.ADMIN)