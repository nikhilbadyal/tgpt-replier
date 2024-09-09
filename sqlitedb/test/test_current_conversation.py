"""Test Current Conversation."""

from django.test import TestCase
from typing_extensions import Self

from sqlitedb.models import Conversation, CurrentConversation, User


class TestCurrentConversation(TestCase):
    """Check if current conversation is loaded properly."""

    fixtures = ["test_fixtures.json"]

    def test_create_current_conversation(self: Self) -> None:
        telegram_id = 123456789
        user = User.objects.get(telegram_id=telegram_id)
        conversation = Conversation.objects.get(pk=1)
        current_conversation = CurrentConversation.objects.get(user=user)

        # Check if the CurrentConversation object was created successfully
        assert current_conversation.user == user
        assert current_conversation.conversation == conversation

        # Check if the __str__ method returns the correct string representation
        expected_str = f"CurrentConversation(user={user}, conversation={conversation})"
        assert str(current_conversation) == expected_str
