
import os
import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlmodel.pool import StaticPool

from app.main import app
from app.database import get_session
from app.models.user import User
from app.utilities.security import encrypt_password


# --- Database fixture 
@pytest.fixture(name="session")
def session_fixture():
    """
    Create a fresh in-memory SQLite database for each test.
    Ensures tests are isolated — one test's data doesn't leak into another.
    """
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    import app.models  # noqa: F401
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)


# --- code to Test client fixture 
@pytest.fixture(name="client")
def client_fixture(session):
    """
    FastAPI test client that uses the in-memory test DB instead of the real one.
    This is the standard pattern for testing FastAPI apps.
    """
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


# ---code for Seed data fixtures ---
@pytest.fixture(name="test_user")
def test_user_fixture(session):
    """A regular user ready to sign in."""
    user = User(
        username="testbob",
        email="testbob@mail.com",
        password=encrypt_password("testpass"),
        role="regular_user",
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture(name="test_author")
def test_author_fixture(session):
    """An author user (linked to an Author profile)."""
    from app.models.publication import Author

    user = User(
        username="testauthor",
        email="testauthor@mail.com",
        password=encrypt_password("authpass"),
        role="author",
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    author = Author(
        user_id=user.id,
        first_name="Test",
        last_name="Author",
        affiliation="Test University",
        email="testauthor@mail.com",
    )
    session.add(author)
    session.commit()
    session.refresh(author)
    return author



@pytest.fixture(autouse=True)
def set_test_env(monkeypatch):
    """Ensure tests use a test secret and don't hit production."""
    monkeypatch.setenv("ENV", "testing")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-for-pytest-only")