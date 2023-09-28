"""Fixtures."""
from datetime import timedelta
from typing import Generator, no_type_check_decorator

import pytest
from django.utils import timezone

from sqlitedb.models import Conversation, CurrentConversation, User, UserConversations
from sqlitedb.utils import test_conversation


@pytest.fixture()
def user() -> Generator[User, None, None]:
    """Fixture for creating a user."""
    return User.objects.create(name="John", telegram_id=1234)


@pytest.fixture()
def conversation(user: User) -> Conversation:
    """Create a test conversation."""
    return Conversation.objects.create(
        user=user,
        title=test_conversation,
        start_time=timezone.now(),
    )


@pytest.fixture()
def user_with_messages() -> User:
    """Dummy user with messages for test cases."""
    user: User = User.objects.create(telegram_id=12345)
    conversation = Conversation.objects.create(user=user)
    CurrentConversation.objects.create(user=user, conversation=conversation)
    UserConversations.objects.create(
        user=user,
        message="Hello",
        from_bot=False,
        conversation=conversation,
    )
    UserConversations.objects.create(
        user=user,
        message="Hi",
        from_bot=True,
        conversation=conversation,
    )
    return user


@pytest.fixture()
def user_without_messages() -> User:
    """Dummy user without messages for test cases."""
    user: User = User.objects.create(telegram_id=23456)
    conversation = Conversation.objects.create(user=user)
    CurrentConversation.objects.create(user=user, conversation=conversation)
    return user


@no_type_check_decorator
@pytest.fixture()
def user_no_conversation() -> User:
    """Dummy user without messages for test cases."""
    user: User = User.objects.create(telegram_id=34567)
    return user


@pytest.fixture()
def user_with_ordered_messages() -> User:
    """User with multiple messages."""
    user: User = User.objects.create(telegram_id=45678)
    conversation = Conversation.objects.create(user=user)
    CurrentConversation.objects.create(user=user, conversation=conversation)

    now = timezone.now()
    UserConversations.objects.create(
        user=user,
        message="First message",
        from_bot=False,
        conversation=conversation,
        message_date=now - timedelta(minutes=5),
    )
    UserConversations.objects.create(
        user=user,
        message="Second message",
        from_bot=True,
        conversation=conversation,
        message_date=now - timedelta(minutes=3),
    )
    UserConversations.objects.create(
        user=user,
        message="Third message",
        from_bot=False,
        conversation=conversation,
        message_date=now - timedelta(minutes=1),
    )

    return user
