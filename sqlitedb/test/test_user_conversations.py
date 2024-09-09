"""Test User Conversation."""

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from sqlitedb.models import Conversation, User, UserConversations
from sqlitedb.utils import test_message


@pytest.mark.django_db
def test_user_conversation_creation(user: User, conversation: Conversation) -> None:
    """Test creating a user conversation."""
    # Create a user conversation
    message = test_message
    from_bot = False
    user_conversation = UserConversations.objects.create(
        user=user,
        message=message,
        from_bot=from_bot,
        conversation=conversation,
    )

    # Check that the user conversation was created
    assert user_conversation.id is not None
    assert user_conversation.user == user
    assert user_conversation.message == message
    assert user_conversation.from_bot == from_bot
    assert user_conversation.conversation == conversation

    assert user_conversation.message_date <= timezone.now()

    # Clean up the user conversation
    user_conversation.delete()


@pytest.mark.django_db
def test_user_conversation_str(user: User, conversation: Conversation) -> None:
    """Test the string representation of a user conversation."""
    user_conversation = UserConversations.objects.create(
        user=user,
        message=test_message,
        from_bot=False,
        conversation=conversation,
    )
    assert (
        str(user_conversation)
        == f"""
        UserConversations(id={user_conversation.id}, user={user}, message=Test message, from_bot=False,
        conversation={conversation}, message_date={user_conversation.message_date})
        """
    )


@pytest.mark.django_db
def test_user_conversation_from_bot(user: User, conversation: Conversation) -> None:
    """Test that the 'from_bot' attribute is required."""
    with pytest.raises(IntegrityError):
        UserConversations.objects.create(
            user=user,
            message=test_message,
            conversation=conversation,
        )


@pytest.mark.django_db
def test_user_conversation_message_required(
    user: User,
    conversation: Conversation,
) -> None:
    """Test that the 'message' attribute is required."""
    user_conversation = UserConversations(
        user=user,
        from_bot=False,
        conversation=conversation,
    )
    with pytest.raises(ValidationError):
        user_conversation.full_clean()  # Trigger the validation error


@pytest.mark.django_db
def test_user_conversation_message_date_auto_generated(
    user: User,
    conversation: Conversation,
) -> None:
    """Test that the message date is auto-generated if not provided."""
    user_conversation = UserConversations.objects.create(
        user=user,
        message=test_message,
        from_bot=False,
        conversation=conversation,
    )
    assert user_conversation.message_date is not None


@pytest.mark.django_db
def test_user_conversation_update(user: User, conversation: Conversation) -> None:
    """Test that we can update a user conversation."""
    user_conversation = UserConversations.objects.create(
        user=user,
        message=test_message,
        from_bot=False,
        conversation=conversation,
    )
    user_conversation.message = "New message"
    user_conversation.save()
    assert user_conversation.message == "New message"


@pytest.mark.django_db
def test_user_conversation_delete_cascade(
    user: User,
    conversation: Conversation,
) -> None:
    """Test that deleting a conversation also deletes associated user conversations."""
    user_conversation = UserConversations.objects.create(
        user=user,
        message=test_message,
        from_bot=False,
        conversation=conversation,
    )
    conversation.delete()
    assert UserConversations.objects.filter(id=user_conversation.id).count() == 0
