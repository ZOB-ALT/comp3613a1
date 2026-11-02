import pytest
from app.repositories.user import UserRepository
from app.schemas.user import RegularUserCreate
from app.utilities.security import encrypt_password


def test_create_user(session):
    """Test that a user is saved to the database."""
    repo = UserRepository(session)
    user_data = RegularUserCreate(
        username="integrationuser",
        email="integration@mail.com",
        password=encrypt_password("intpass"),
        role="regular_user",
    )
    user = repo.create(user_data)

    assert user.id is not None
    assert user.username == "integrationuser"
    assert user.email == "integration@mail.com"


def test_get_by_username(session):
    """Test that a saved user can be retrieved by username."""
    repo = UserRepository(session)
    repo.create(RegularUserCreate(
        username="findme", email="find@mail.com",
        password=encrypt_password("pass"), role="regular_user",
    ))

    found = repo.get_by_username("findme")

    assert found is not None
    assert found.email == "find@mail.com"


def test_get_by_username_not_found(session):
    """Test that an unknown username returns None."""
    repo = UserRepository(session)
    found = repo.get_by_username("doesnotexist")
    assert found is None


def test_get_all_users(session):
    """Test that all users are returned."""
    repo = UserRepository(session)
    repo.create(RegularUserCreate(
        username="user1", email="u1@mail.com",
        password=encrypt_password("p"), role="regular_user",
    ))
    repo.create(RegularUserCreate(
        username="user2", email="u2@mail.com",
        password=encrypt_password("p"), role="regular_user",
    ))

    users = repo.get_all_users()
    assert len(users) >= 2
    usernames = [u.username for u in users]
    assert "user1" in usernames
    assert "user2" in usernames