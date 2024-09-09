"""User Image test."""

import datetime

from django.test import TestCase
from typing_extensions import Self

from sqlitedb.models import User, UserImages


class TestUserImages(TestCase):
    """Test getting user images."""

    fixtures = ["test_fixtures.json"]

    def test_create_user_image(self: Self) -> None:
        user = User.objects.get(telegram_id=123456789)
        user_image = UserImages.objects.create(
            user=user,
            image_caption="Test Image Caption",
            image_url="https://example.com/test_image.jpg",
            from_bot=False,
        )

        # Check if the UserImages object was created successfully
        assert user_image.user == user
        assert user_image.image_caption == "Test Image Caption"
        assert user_image.image_url == "https://example.com/test_image.jpg"
        assert not user_image.from_bot
        assert isinstance(user_image.message_date, datetime.datetime)

        # Check if the __str__ method returns the correct string representation
        expected_str = f"""UserImages(id={user_image.id}, user={user}, image_caption={user_image.image_caption},
        image_url={user_image.image_url}, from_bot={user_image.from_bot}, message_date={user_image.message_date})"""
        assert str(user_image) == expected_str
