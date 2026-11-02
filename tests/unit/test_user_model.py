import pytest
from app.models.user import User
from app.utilities.security import encrypt_password, verify_password


def test_new_user():
    """Test that a new User has the expected default fields."""
    user = User(
        username="bob",
        email="bob@mail.com",
        password=encrypt_password("bobpass"),
        role="regular_user",
    )
    assert user.username == "bob"
    assert user.email == "bob@mail.com"
    assert user.role == "regular_user"
    assert user.id is None  # not yet persisted


def test_hashed_password():
    """Test that password is hashed at creation."""
    plaintext = "mypass"
    user = User(
        username="alice",
        email="alice@mail.com",
        password=encrypt_password(plaintext),
        role="regular_user",
    )
    assert user.password != plaintext
    assert len(user.password) > 20


def test_verify_password_success():
    """Test that the hashed password verifies correctly."""
    plaintext = "mypass"
    hashed = encrypt_password(plaintext)
    user = User(
        username="alice",
        email="alice@mail.com",
        password=hashed,
        role="regular_user",
    )
    assert verify_password(plaintext, user.password) is True


def test_verify_password_failure():
    """Test that a wrong password fails verification."""
    hashed = encrypt_password("correctpass")
    user = User(
        username="alice",
        email="alice@mail.com",
        password=hashed,
        role="regular_user",
    )
    assert verify_password("wrongpass", user.password) is False


def test_role_default_is_empty():
    """Test that role defaults to empty string."""
    user = User(
        username="nobody",
        email="nobody@mail.com",
        password=encrypt_password("pass"),
    )
    assert user.role == ""