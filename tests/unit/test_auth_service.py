import pytest
from unittest.mock import MagicMock
from app.services.auth_service import AuthService
from app.models.user import User
from app.utilities.security import encrypt_password


@pytest.fixture
def mock_repo():
    """A mock repository (a stub) for the AuthService."""
    return MagicMock()


@pytest.fixture
def mock_user():
    """A fake user for authentication tests."""
    return User(
        id=1,
        username="bob",
        email="bob@mail.com",
        password=encrypt_password("bobpass"),
        role="regular_user",
    )


def test_authenticate_user_success(mock_repo, mock_user):
    """Test that valid credentials return a JWT token."""
    mock_repo.get_by_username.return_value = mock_user

    service = AuthService(mock_repo)
    token = service.authenticate_user("bob", "bobpass")

    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 20  # JWTs are long
    
    mock_repo.get_by_username.assert_called_once_with("bob")


def test_authenticate_user_wrong_password(mock_repo, mock_user):
    """Test that a wrong password returns None (no token)."""
    mock_repo.get_by_username.return_value = mock_user

    service = AuthService(mock_repo)
    token = service.authenticate_user("bob", "wrongpass")

    assert token is None


def test_authenticate_user_not_found(mock_repo):
    """Test that an unknown username returns None."""
    mock_repo.get_by_username.return_value = None  # user doesn't exist

    service = AuthService(mock_repo)
    token = service.authenticate_user("ghost", "anything")

    assert token is None


def test_register_user(mock_repo):
    """Test that register_user hashes the password and creates the user."""
    mock_repo.create.return_value = User(
        id=2, username="newuser", email="new@mail.com",
        password="hashed", role="regular_user",
    )

    service = AuthService(mock_repo)
    user = service.register_user("newuser", "new@mail.com", "newpass")

    # Verigfy the repo was called
    assert mock_repo.create.call_count == 1
    
    call_args = mock_repo.create.call_args
    payload = call_args[0][0]  # first positional arg
    assert payload.password != "newpass"
    assert user.username == "newuser"