"""User Test cases."""
from datetime import datetime

import pytest
from django.db import IntegrityError

from sqlitedb.models import User
from sqlitedb.utils import UserStatus


class TestUserModel:
    @pytest.mark.django_db  # type: ignore
    def test_create_user(self) -> None:
        """Test creating a new user."""
        user = User.objects.create(name="John Doe", telegram_id=123456789)
        assert user.id is not None
        assert user.name == "John Doe"
        assert user.telegram_id == 123456789
        assert user.status == UserStatus.ACTIVE.value
        assert isinstance(user.joining_date, datetime)
        assert isinstance(user.last_updated, datetime)

    @pytest.mark.django_db  # type: ignore
    def test_create_duplicate_telegram_id(self) -> None:
        """Test creating a user with a duplicate telegram_id."""
        User.objects.create(name="John Doe", telegram_id=123456789)
        with pytest.raises(IntegrityError):
            User.objects.create(
                name="Jane Doe", telegram_id=123456789
            )  # raises IntegrityError

    @pytest.mark.django_db  # type: ignore
    def test_update_user(self) -> None:
        """Test updating user's details."""
        user = User.objects.create(name="John Doe", telegram_id=123456789)
        user.name = "Jane Doe"
        user.status = UserStatus.SUSPENDED.value
        user.save()
        updated_user = User.objects.get(id=user.id)
        assert updated_user.name == "Jane Doe"
        assert updated_user.status == UserStatus.SUSPENDED.value
        assert updated_user.last_updated > user.joining_date

    @pytest.mark.django_db  # type: ignore
    def test_delete_user(self) -> None:
        """Test deleting a user."""
        user = User.objects.create(name="John Doe", telegram_id=123456789)
        user_id = user.id
        user.delete()
        # noinspection PyTypeChecker
        with pytest.raises(User.DoesNotExist):
            User.objects.get(id=user_id)

    @pytest.mark.django_db  # type: ignore
    def test_str_method(self) -> None:
        """Test the __str__() method."""
        user = User.objects.create(name="John Doe", telegram_id=123456789)
        assert (
            str(user)
            == f"""User(id={user.id}, name=John Doe, telegram_id=123456789, status={UserStatus.ACTIVE.value})"""
        )
