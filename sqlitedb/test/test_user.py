"""User Test cases."""

from datetime import datetime, timedelta

import pytest
from django.db import IntegrityError

from sqlitedb.models import User
from sqlitedb.utils import UserStatus


@pytest.fixture  # type: ignore
def user() -> User:
    """A fixture that generates a sample user object with pre-defined
    values."""
    user = {
        "name": "John",
        "telegram_id": 123456,
        "status": UserStatus.ACTIVE.value,
    }
    return User.objects.create(**user)  # type: ignore


@pytest.mark.django_db  # type: ignore
def test_create_user(user: User) -> None:
    """Test creating a new user and saving it to the database.

    Args:
        user: A user object generated by the fixture.

    Raises:
        AssertionError: If any of the assertions fail.
    """
    assert user.id is not None
    assert user.name == "John"
    assert user.telegram_id == 123456
    assert user.status == UserStatus.ACTIVE.value
    assert isinstance(user.joining_date, datetime)
    assert isinstance(user.last_updated, datetime)


@pytest.mark.django_db  # type: ignore
def test_unique_telegram_id(user: User) -> None:
    """Test that creating a user with a non-unique Telegram ID raises an
    IntegrityError.

    Args:
        user: A user object generated by the fixture.

    Raises:
        AssertionError: If the expected IntegrityError is not raised.
    """
    with pytest.raises(IntegrityError):
        User.objects.create(
            name="Jane", telegram_id=123456, status=UserStatus.ACTIVE.value
        )


@pytest.mark.django_db  # type: ignore
def test_update_user(user: User) -> None:
    """Test updating a user's details and saving the changes to the database.

    Args:
        user: A user object generated by the fixture.

    Raises:
        AssertionError: If any of the assertions fail.
    """
    new_name = "Jane"
    new_status = UserStatus.TEMP_BANNED.value
    user.name = new_name
    user.status = new_status
    user.save()
    updated_user = User.objects.get(id=user.id)
    assert updated_user.name == new_name
    assert updated_user.status == new_status
    assert updated_user.last_updated > user.joining_date


@pytest.mark.django_db  # type: ignore
def test_delete_user(user: User) -> None:
    """Test deleting a user from the database.

    Args:
        user: A user object generated by the fixture.

    Raises:
        AssertionError: If the deleted user can still be retrieved from the database.
    """
    user_id = user.id
    user.delete()
    # noinspection PyTypeChecker
    with pytest.raises(User.DoesNotExist):
        User.objects.get(id=user_id)


@pytest.mark.django_db  # type: ignore
def test_string_representation(user: User) -> None:
    """Test the string representation of a user object.

    Args:
        user: A user object generated by the fixture.

    Raises:
        AssertionError: If the string representation of the user object is not as expected.
    """
    assert (
        str(user)
        == f"User(id={user.id}, name={user.name}, telegram_id={user.telegram_id}, status={user.status})"
    )


@pytest.mark.django_db  # type: ignore
def test_get_active_users(user: User) -> None:
    """Test getting all active users from the database.

    Args:
        user: A user object generated by the fixture.

    Raises:
        AssertionError: If the number of active users returned is not 1.
    """
    active_users = User.objects.filter(status=UserStatus.ACTIVE.value)
    assert len(active_users) == 1
    assert active_users[0].id == user.id


@pytest.mark.django_db  # type: ignore
def test_get_suspended_users(user: User) -> None:
    """Test getting all suspended users from the database.

    Args:
        user: A user object generated by the fixture.

    Raises:
        AssertionError: If the number of suspended users returned is not 0.
    """
    suspended_users = User.objects.filter(status=UserStatus.SUSPENDED.value)
    assert len(suspended_users) == 0


@pytest.mark.django_db  # type: ignore
def test_get_temporarily_banned_users(user: User) -> None:
    """Test getting all temporarily banned users from the database.

    Args:
        user: A user object generated by the fixture.

    Raises:
        AssertionError: If the number of temporarily banned users returned is not 0.
    """
    temporarily_banned_users = User.objects.filter(status=UserStatus.TEMP_BANNED.value)
    assert len(temporarily_banned_users) == 0


@pytest.mark.django_db  # type: ignore
def test_last_updated_auto_now(user: User) -> None:
    """Test that the 'last_updated' field is automatically updated when a user
    object is modified and saved.

    Args:
        user: A user object generated by the fixture.

    Raises:
        AssertionError: If the 'last_updated' field is not updated after the user object is modified and saved.
    """
    original_last_updated = user.last_updated
    user.name = "Jane"
    user.save()
    updated_user = User.objects.get(id=user.id)
    assert updated_user.last_updated > original_last_updated


@pytest.mark.django_db  # type: ignore
def test_joining_date_auto_now_add(user) -> None:
    """Test that the 'joining_date' field is automatically set when a new user
    object is created and saved.

    Args:
        user: A dictionary of sample user data.

    Raises:
        AssertionError: If the 'joining_date' field is not set after a new user object is created and saved.
    """
    now = datetime.now()
    assert (
        (now - timedelta(seconds=1))
        <= user.joining_date
        <= (now + timedelta(seconds=1))
    )
