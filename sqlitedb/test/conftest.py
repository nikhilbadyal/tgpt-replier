"""Fixtures."""
from datetime import timedelta
from typing import Any, Generator, no_type_check_decorator

import pytest
from django.utils import timezone

from sqlitedb.models import Conversation, CurrentConversation, User, UserConversations


@pytest.fixture
def user() -> Generator[User, None, None]:
    """Fixture for creating a user."""
    user = User.objects.create(name="John", telegram_id=1234)
    yield user


@pytest.fixture
def conversation(user: User) -> Conversation:
    """Create a test conversation."""
    conversation = Conversation.objects.create(
        user=user,
        title="Test Conversation",
        start_time=timezone.now(),
    )
    return conversation


@pytest.fixture
def user_with_messages(db: Any) -> User:
    """Dummy user with messages for test cases."""
    user: User = User.objects.create(telegram_id=12345)
    conversation = Conversation.objects.create(user=user)
    CurrentConversation.objects.create(user=user, conversation=conversation)
    UserConversations.objects.create(
        user=user, message="Hello", from_bot=False, conversation=conversation
    )
    UserConversations.objects.create(
        user=user, message="Hi", from_bot=True, conversation=conversation
    )
    return user


@pytest.fixture
def user_without_messages(db: Any) -> User:
    """Dummy user without messages for test cases."""
    user: User = User.objects.create(telegram_id=23456)
    conversation = Conversation.objects.create(user=user)
    CurrentConversation.objects.create(user=user, conversation=conversation)
    return user


@no_type_check_decorator
@pytest.fixture
def user_no_conversation(db: Any) -> User:
    """Dummy user without messages for test cases."""
    user: User = User.objects.create(telegram_id=34567)
    return user


@pytest.fixture
def user_with_ordered_messages(db: Any) -> User:
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
