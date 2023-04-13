"""Test Conversation."""
from datetime import datetime

import pytest
from django.utils import timezone

from sqlitedb.models import Conversation, User


@pytest.mark.django_db
def test_conversation_creation(user: User) -> None:
    """Test creating a conversation for a user."""
    # Create a conversation
    title = "Test Conversation"
    conversation = Conversation.objects.create(user=user, title=title)

    # Check that the conversation was created
    assert conversation.id is not None
    assert conversation.user == user
    assert conversation.title == title

    assert conversation.start_time <= timezone.now()
    assert isinstance(conversation.start_time, datetime)

    # Clean up the conversation
    conversation.delete()


@pytest.mark.django_db
def test_conversation_str(user: User) -> None:
    """Test the string representation of a conversation."""
    conversation = Conversation.objects.create(user=user, title="Test Conversation")
    assert (
        str(conversation) == f"Conversation(id={conversation.id}, user={user}, "
        f"title=Test Conversation, start_time={conversation.start_time})"
    )


@pytest.mark.django_db
def test_conversation_title_optional(user: User) -> None:
    """Test that a conversation can be created without a title."""
    conversation = Conversation.objects.create(user=user)
    assert conversation.title is None


@pytest.mark.django_db
def test_conversation_start_time_immutable(user: User) -> None:
    """Test that the start time of a conversation is immutable."""
    conversation = Conversation.objects.create(user=user)
    start_time = conversation.start_time
    conversation.title = "Test Conversation"
    conversation.save()
    assert conversation.start_time == start_time


@pytest.mark.django_db
def test_conversation_start_time_auto_generated(user: User) -> None:
    """Test that the start time of a conversation is auto-generated if not
    provided."""
    conversation1 = Conversation.objects.create(user=user)
    conversation2 = Conversation.objects.create(user=user)
    assert conversation1.start_time < conversation2.start_time


@pytest.mark.django_db
def test_conversation_update(conversation: Conversation) -> None:
    """Test updating the title of a conversation."""
    conversation.title = "New Title"
    conversation.save()
    assert conversation.title == "New Title"


@pytest.mark.django_db
def test_conversation_start_time_default(conversation: Conversation) -> None:
    """Test that the start time is auto-generated if not provided."""
    conversation = Conversation.objects.create(
        user=conversation.user,
        title="New Conversation",
    )
    assert conversation.start_time is not None
