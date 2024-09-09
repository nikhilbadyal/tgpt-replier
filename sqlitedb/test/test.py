"""Test Cases."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from django.test import TestCase
from django.utils.crypto import get_random_string
from typing_extensions import Self

from sqlitedb.models import (
    Conversation,
    CurrentConversation,
    User,
    UserConversations,
    UserImages,
)
from sqlitedb.sqlite import SQLiteDatabase
from sqlitedb.utils import ErrorCodes, test_message, test_title

fixture_name = "test_fixtures.json"


class CustomTest(TestCase):
    """Custom test case settings."""

    def setUp(self: Self) -> None:
        """Setup the test case."""
        self.telegram_id = 123456789
        self.user = User.objects.get(telegram_id=self.telegram_id)
        self.another_telegram_id = 5432198760
        self.another_user = User.objects.get(telegram_id=self.another_telegram_id)
        self.controller = SQLiteDatabase()
        self.non_existing_telegram_id = 111


class GetMessagesByUserTestCase(CustomTest):
    """Test message from user."""

    fixtures = [fixture_name]

    def test_get_messages_by_user(self: Self) -> None:
        # Get the user from the fixture

        # Call the get_messages_by_user function
        messages = self.controller.get_messages_by_user(self.user.telegram_id)

        current_conversation = CurrentConversation.objects.get(user=self.user)

        # Get the expected messages from the fixture
        expected_messages = (
            UserConversations.objects.filter(
                user=self.user,
                conversation=current_conversation.conversation,
            )
            .values("from_bot", "message")
            .order_by("message_date")
        )

        # Compare the messages returned by the function with the expected messages
        assert list(messages) == list(expected_messages)

    def test_get_messages_by_user_from_fixture(self: Self) -> None:
        # Create a user

        # Load the fixture data
        fixture_dir = Path(__file__).resolve().parent.parent
        fixture_path = Path(f"{fixture_dir}/fixtures/test_fixtures.json")
        with fixture_path.open() as f:
            fixture_data = json.load(f)

        # Extract expected messages from the fixture
        expected_messages = [obj["fields"] for obj in fixture_data if obj["model"] == "sqlitedb.userconversations"]

        # Call the get_messages_by_user function
        actual_messages = self.controller.get_messages_by_user(self.user.telegram_id)

        # Check that the function returns the correct actual messages
        for idx, message in enumerate(actual_messages):
            assert message["from_bot"] == expected_messages[idx]["from_bot"]
            assert message["message"] == expected_messages[idx]["message"]

    def test_get_messages_by_user_multiple_conversations(self: Self) -> None:
        # Create a user

        fixture_dir = Path(__file__).resolve().parent.parent
        fixture_path = Path(f"{fixture_dir}/fixtures/test_fixtures.json")
        with fixture_path.open() as f:
            fixture_data = json.load(f)

        # Extract expected messages from the fixture
        expected_messages = [
            obj["fields"]
            for obj in fixture_data
            if obj["model"] == "sqlitedb.userconversations" and obj["fields"]["conversation"] == 1
        ]

        # Call the get_messages_by_user function
        messages = self.controller.get_messages_by_user(self.user.telegram_id)

        # Check that the function returns the correct messages from the current conversation
        for idx, message in enumerate(messages):
            assert message["from_bot"] == expected_messages[idx]["from_bot"]
            assert message["message"] == expected_messages[idx]["message"]

    def test_get_messages_by_user_no_current_conversation(self: Self) -> None:
        # Create a user

        # Call the get_messages_by_user function
        messages = self.controller.get_messages_by_user(self.another_user.telegram_id)

        # Check that the function returns an empty list since there is no current conversation
        assert len(messages) == 0


class GetUserTestCase(CustomTest):
    """Test User test casesp."""

    fixtures = [fixture_name]

    def test_get_user_existing_user(self: Self) -> None:
        """Test if the _get_user method retrieves an existing user correctly."""
        # Call the _get_user function
        retrieved_user = self.controller.get_user(self.user.telegram_id)

        # Check that the function returns the correct user
        assert retrieved_user == self.user

    def test_get_user_create_new_user(self: Self) -> None:
        """Test if the _get_user method creates a new user when the user does not exist."""
        # Set a non-existing user telegram_id

        # Call the _get_user function
        new_user = self.controller.get_user(self.non_existing_telegram_id)

        # Check that the function returns a User object
        assert isinstance(new_user, User)
        if isinstance(new_user, ErrorCodes):  # To Silence mypy error
            return
        # Check that the function creates and returns a new user
        assert new_user.telegram_id == self.non_existing_telegram_id
        assert new_user.name == f"User {self.non_existing_telegram_id}"

        # Cleanup: delete the created user
        new_user.delete()

    def test_get_user_creation_error(self: Self) -> None:
        """Test if the _get_user method returns an error code when there's an issue creating a new user."""
        # Set a non-existing user telegram_id

        # Patch the User.save() method to raise an exception
        with patch.object(User, "save", side_effect=Exception("Error creating user")):
            # Call the _get_user function
            result = self.controller.get_user(self.non_existing_telegram_id)

            # Check that the function returns the error code
            assert result == ErrorCodes.exceptions


class GetCurrentConversation(CustomTest):
    """Test current conversation."""

    fixtures = [fixture_name]

    def test_get_current_conversation_new(self: Self) -> None:
        """Test if the _get_current_conversation method creates a new conversation and returns its ID when the user
        doesn't have a current conversation in the database."""
        # Mock the ChatGPT.send_text_completion_request method
        with patch(
            "chatgpt.chatgpt.ChatGPT.send_text_completion_request",
        ) as mock_send_text_completion_request:
            mock_send_text_completion_request.return_value = {
                "choices": [{"text": "Mocked Conversation"}],
            }

            # Call the _get_current_conversation function
            conversation_id = self.controller._get_current_conversation(
                self.another_user,
                "Hello",
            )

            # Check that a new conversation has been created
            new_conversation = Conversation.objects.get(id=conversation_id)
            assert new_conversation is not None

            # Check that the new conversation has the correct title and user
            assert new_conversation.title == "Mocked Conversation"
            assert new_conversation.user == self.another_user

            # Cleanup: delete the created user and conversation
            new_conversation.delete()

    @patch("chatgpt.chatgpt.ChatGPT.send_text_completion_request")
    def test_send_text_completion_request_failure(
        self: Self,
        mock_send_text_completion_request: MagicMock,
    ) -> None:
        # Mock the send_text_completion_request method to return an error code
        mock_send_text_completion_request.return_value = ErrorCodes.exceptions

        # Call the _get_current_conversation method and check if it returns the error code
        conversation_id = self.controller._get_current_conversation(
            self.another_user,
            "Hello",
        )
        assert conversation_id == ErrorCodes.exceptions

    @patch("chatgpt.chatgpt.ChatGPT.send_text_completion_request")
    @patch("sqlitedb.models.Conversation.save")
    def test_exception_in_get_current_conversation(
        self: Self,
        mock_send_text_completion_request: MagicMock,
        mock_conversation_save: MagicMock,
    ) -> None:
        # Mock the send_text_completion_request method to return a valid response
        mock_send_text_completion_request.return_value = {
            "choices": [{"text": "Sample Chat Title"}],
        }

        # Mock the Conversation.save method to raise an exception
        mock_conversation_save.side_effect = Exception()

        # Call the _get_current_conversation method and check if it returns the error code
        conversation_id = self.controller._get_current_conversation(
            self.another_user,
            "hello",
        )
        assert conversation_id == ErrorCodes.exceptions

    def test_get_current_conversation_existing(self: Self) -> None:
        """Test if the _get_current_conversation method returns the correct conversation ID when the user already has a
        current conversation in the database."""
        conversation = Conversation.objects.get(pk=1)

        # Call the _get_current_conversation function
        conversation_id = self.controller._get_current_conversation(self.user, "Hello")

        # Check that the function returns the correct conversation ID
        assert conversation_id == conversation.id


class CreateConversation(CustomTest):
    """Test Create conversation."""

    fixtures = [fixture_name]

    def test_create_conversation_success(self: Self) -> None:
        """Test if the _create_conversation method successfully creates and saves a new conversation."""
        # Call the _create_conversation function
        result = self.controller._create_conversation(
            self.user.telegram_id,
            test_message,
            False,
        )

        # Check if the conversation was created successfully
        assert result is None

        # Verify if the conversation was saved in the database
        saved_conversation = UserConversations.objects.get(
            user=self.user,
            message=test_message,
            from_bot=False,
        )
        assert saved_conversation is not None

    def test_create_conversation_fail(self: Self) -> None:
        """Test if the _create_conversation method returns an error code when it fails to get the current
        conversation."""
        # Use patch to modify the behavior of _get_current_conversation
        with patch.object(
            self.controller,
            "_get_current_conversation",
        ) as mock_get_current_conversation:
            mock_get_current_conversation.return_value = ErrorCodes.exceptions

            # Call the _create_conversation function
            result = self.controller._create_conversation(
                self.user.telegram_id,
                test_message,
                False,
            )

            # Check if the function returns an error code
            assert result == ErrorCodes.exceptions

    @patch("sqlitedb.models.UserConversations.save")
    def test_exception_in_get_create_conversation(
        self: Self,
        mock_conversation_save: MagicMock,
    ) -> None:
        # Mock the send_text_completion_request method to return a valid response

        # Mock the Conversation.save method to raise an exception
        mock_conversation_save.side_effect = Exception()

        # Call the _get_current_conversation method and check if it returns the error code
        conversation_id = self.controller._create_conversation(
            1234567890,
            test_message,
            False,
        )
        assert conversation_id == ErrorCodes.exceptions

    def test_create_conversation_get_user_error(self: Self) -> None:
        """Test if the _create_conversation method returns an error code when the _get_user method returns an error
        code."""
        # Use patch to modify the behavior of _get_user
        with patch.object(self.controller, "get_user") as mock_get_user:
            mock_get_user.return_value = ErrorCodes.exceptions

            # Call the _create_conversation function
            result = self.controller._create_conversation(
                1234567890,
                test_message,
                False,
            )

            # Check if the function returns an error code
            assert result == ErrorCodes.exceptions

    def test_create_conversation_get_current_conversation_error(self: Self) -> None:
        """Test if the _create_conversation method returns an error code when the _get_current_conversation method
        returns an error code."""
        with patch.object(
            self.controller,
            "_get_current_conversation",
        ) as mock_get_current_conversation:
            mock_get_current_conversation.return_value = ErrorCodes.exceptions

            # Call the _create_conversation function
            result = self.controller._create_conversation(
                self.user.telegram_id,
                test_message,
                False,
            )

            # Check if the function returns an error code
            assert result == ErrorCodes.exceptions

    def test_insert_message_from_user(self: Self) -> None:
        """Test if the message from user is inserted."""
        # Monkey patch the _get_current_conversation method to return an error code
        messages_by_user_before = UserConversations.objects.filter(
            user__telegram_id=self.user.telegram_id,
            from_bot=False,
        )
        messages_by_bot_before = UserConversations.objects.filter(
            user__telegram_id=self.telegram_id,
            from_bot=True,
        )
        total_messages_by_user_before = len(messages_by_user_before)
        total_messages_by_bot_before = len(messages_by_bot_before)
        status = self.controller.insert_message_from_user(
            "From User",
            self.user.telegram_id,
        )
        assert status is None
        messages_by_user_after = UserConversations.objects.filter(
            user__telegram_id=self.user.telegram_id,
            from_bot=False,
        )
        messages_by_bot_after = UserConversations.objects.filter(
            user__telegram_id=self.user.telegram_id,
            from_bot=True,
        )
        total_messages_by_user_after = len(messages_by_user_after)
        total_messages_by_bot_after = len(messages_by_bot_after)
        assert total_messages_by_user_before + 1 == total_messages_by_user_after
        assert total_messages_by_bot_before == total_messages_by_bot_after

    def test_insert_message_from_bot(self: Self) -> None:
        """Test if the message from user is inserted."""
        # Monkey patch the _get_current_conversation method to return an error code
        messages_by_user_before = UserConversations.objects.filter(
            user__telegram_id=self.user.telegram_id,
            from_bot=False,
        )
        messages_by_bot_before = UserConversations.objects.filter(
            user__telegram_id=self.user.telegram_id,
            from_bot=True,
        )
        total_messages_by_user_before = len(messages_by_user_before)
        total_messages_by_bot_before = len(messages_by_bot_before)
        status = self.controller.insert_message_from_gpt(
            "From GPT",
            self.user.telegram_id,
        )
        assert status is None
        messages_by_user_after = UserConversations.objects.filter(
            user__telegram_id=self.user.telegram_id,
            from_bot=False,
        )
        messages_by_bot_after = UserConversations.objects.filter(
            user__telegram_id=self.user.telegram_id,
            from_bot=True,
        )
        total_messages_by_user_after = len(messages_by_user_after)
        total_messages_by_bot_after = len(messages_by_bot_after)
        assert total_messages_by_user_before == total_messages_by_user_after
        assert total_messages_by_bot_before + 1 == total_messages_by_bot_after


class DeleteAllUserMessagesTest(CustomTest):
    """Delete all messages."""

    fixtures = [fixture_name]

    def test_delete_all_user_messages(self: Self) -> None:
        """Test if the delete_all_user_messages method successfully deletes all conversations for a user."""
        # Create a few conversations for the user
        conversations = [Conversation(user=self.user, title=f"Sample Conversation {i}") for i in range(1, 4)]
        Conversation.objects.bulk_create(conversations)

        # Call the delete_all_user_messages function
        self.controller.delete_all_user_messages(self.user.telegram_id)

        # Check if the conversations are deleted
        remaining_conversations = Conversation.objects.filter(
            user__telegram_id=self.user.telegram_id,
        )
        assert not remaining_conversations.exists()

    @patch("sqlitedb.models.Conversation.objects.filter")
    def test_exception_in_delete_all_user_messages(
        self: Self,
        mock_conversations_filter: MagicMock,
    ) -> None:
        # Mock the Conversation.objects.filter method to raise an exception
        mock_conversations_filter.side_effect = Exception()

        # Call the delete_all_user_messages method and check if it returns the error code
        result = self.controller.delete_all_user_messages(self.user.telegram_id)
        assert result == ErrorCodes.exceptions


class TestInitiateNewConversation(CustomTest):
    """Test conversation creation."""

    fixtures = [fixture_name]

    def test_initiate_new_conversation_success(self: Self) -> None:
        """Test if the initiate_new_conversation method successfully creates a new conversation."""
        # Call the initiate_new_conversation method
        result = self.controller.initiate_new_conversation(
            self.user.telegram_id,
            test_title,
        )

        # Check if the function returns a success value
        assert result is None

        # Check if the new conversation is created in the database
        conversation = Conversation.objects.get(user=self.user, title=test_title)
        assert conversation is not None

        # Check if the current conversation is set to the new conversation
        current_conversation = CurrentConversation.objects.get(user=self.user)
        assert current_conversation.conversation == conversation

    @patch("sqlitedb.models.CurrentConversation.save")
    def test_initiate_new_conversation_save_current_conversation_exception(
        self: Self,
        mock_save: MagicMock,
    ) -> None:
        """Test if the initiate_new_conversation method handles an exception raised."""
        mock_save.side_effect = Exception()

        # Call the initiate_new_conversation method

        result = self.controller.initiate_new_conversation(
            self.user.telegram_id,
            test_title,
        )

        # Check if the function returns an error value
        assert result == ErrorCodes.exceptions

        # Check if the conversation is deleted from the database
        # noinspection PyTypeChecker
        with pytest.raises(Conversation.DoesNotExist):
            Conversation.objects.get(user=self.user, title=test_title)

    @patch("sqlitedb.models.Conversation.save")
    def test_initiate_new_conversation_save_conversation_exception(
        self: Self,
        mock_save: MagicMock,
    ) -> None:
        """Test if the initiate_new_conversation method handles an exception raised during saving the Conversation
        object."""
        mock_save.side_effect = Exception()

        # Call the initiate_new_conversation method

        result = self.controller.initiate_new_conversation(
            self.user.telegram_id,
            test_title,
        )

        # Check if the function returns an error value
        assert result == ErrorCodes.exceptions

    def test_initiate_new_conversation_new_user(self: Self) -> None:
        """Test if the initiate_new_conversation method handles an exception raised during saving the Conversation
        object."""
        user = User.objects.create(name="John", telegram_id=1234)

        # Call the initiate_new_conversation method

        result = self.controller.initiate_new_conversation(1234, test_title)
        user.delete()

        assert result is None

    def test_initiate_empty_new_conversation_success(self: Self) -> None:
        # Create a user

        # Create a conversation
        conversation = Conversation.objects.create(
            user=self.another_user,
            title=test_title,
        )

        # Create a current conversation
        CurrentConversation.objects.create(
            user=self.another_user,
            conversation=conversation,
        )

        # Call the method

        self.controller.initiate_empty_new_conversation(self.another_user.telegram_id)

        # Check that the current conversation was deleted
        # noinspection PyTypeChecker
        with pytest.raises(CurrentConversation.DoesNotExist):
            CurrentConversation.objects.get(user=self.another_user)

    def test_initiate_empty_new_conversation_success_alt(self: Self) -> None:
        # Create a user

        # Call the method

        self.controller.initiate_empty_new_conversation(self.another_user.telegram_id)

        # Check that the current conversation was deleted
        # noinspection PyTypeChecker
        with pytest.raises(CurrentConversation.DoesNotExist):
            CurrentConversation.objects.get(user=self.another_user)


class GetImageByUser(CustomTest):
    """Test case class for getting images by user."""

    fixtures = [fixture_name]

    def test_insert_images_from_gpt(self: Self) -> None:
        """Test if the insert_images_from_gpt method inserts image data for the specified user."""
        # Define image data
        image_caption = get_random_string(10)
        image_url = get_random_string(30)
        from_bot = True

        # Call function to insert image data
        result = self.controller.insert_images_from_gpt(
            image_caption,
            image_url,
            self.user.telegram_id,
        )

        # Check that the result is None (successful insertion)
        assert result is None

        # Check that the image was saved to the database
        saved_image = UserImages.objects.last()
        assert isinstance(saved_image, UserImages)
        assert saved_image.user == self.user
        assert saved_image.image_caption == image_caption
        assert saved_image.image_url == image_url
        assert saved_image.from_bot == from_bot

    @patch("sqlitedb.sqlite.UserImages.save")
    def test_insert_images_from_gpt_exception_handling(
        self: Self,
        mock_conversation_save: MagicMock,
    ) -> None:
        """Test that the insert_images_from_gpt function returns an error code when an exception is raised."""
        mock_conversation_save.side_effect = Exception()

        image_caption = get_random_string(10)
        image_url = get_random_string(30)

        # Call function to insert image data
        result = self.controller.insert_images_from_gpt(
            image_caption,
            image_url,
            self.user.telegram_id,
        )
        assert result == ErrorCodes.exceptions

    def test_delete_all_user_images(self: Self) -> None:
        """Test that all images for a user can be deleted using the delete_all_user_images method."""
        num_images = 2

        # Check that the images were created
        assert UserImages.objects.filter(user=self.user).count() == num_images

        # Delete the images for the user

        num_deleted = self.controller.delete_all_user_images(self.user.telegram_id)

        # Check that the images were deleted
        assert num_deleted == num_images
        assert UserImages.objects.filter(user=self.user).count() == 0

    def test_delete_all_user_images_exception_handling(self: Self) -> None:
        """Test that the delete_all_user_images function returns an error code when an exception is raised."""
        image = UserImages.objects.create(
            user=self.user,
            image_caption="Test Image",
            image_url="https://example.com/test.png",
            from_bot=True,
        )
        # Delete the images for the user
        with patch.object(image.__class__.objects, "filter") as mock_filter:
            mock_filter.return_value.delete.side_effect = Exception()

            result = self.controller.delete_all_user_images(self.user.telegram_id)
            assert result == ErrorCodes.exceptions

    def test_delete_all_user_data(self: Self) -> None:
        """Test deleting all user data."""
        images, convo = self.controller.delete_all_user_data(self.user.telegram_id)
        assert isinstance(images, int)
        assert isinstance(convo, int)


class TestGetUserConversations(CustomTest):
    """Add the following test methods to the existing class."""

    fixtures = [fixture_name]

    def test_get_user_conversations_success(self: Self) -> None:
        """Test get_user_conversations with a valid user and valid pagination parameters."""
        page_size = 2
        result = self.controller.get_user_conversations(
            self.user.telegram_id,
            page=1,
            per_page=page_size,
        )
        # Check the result
        assert len(result["data"]) == page_size
        assert result["has_next"] is True
        assert result["has_previous"] is False
        result = self.controller.get_user_conversations(
            self.user.telegram_id,
            page=2,
            per_page=page_size,
        )
        assert len(result["data"]) == 1
        assert result["has_next"] is False
        assert result["has_previous"] is True

    def test_get_user_conversations_invalid_page_number(self: Self) -> None:
        """test_get_user_conversations_invalid_page_number."""
        result = self.controller.get_user_conversations(self.user.telegram_id, page="a", per_page=2)  # type: ignore
        # Check the result
        assert len(result["data"]) == 2
        assert result["has_next"] is True
        assert result["has_previous"] is False
        assert result["current_page"] == 1

    def test_get_user_conversations_invalid_empty_page(self: Self) -> None:
        # Set up test data

        result = self.controller.get_user_conversations(
            self.user.telegram_id,
            page=10,
            per_page=2,
        )
        # Check the result
        assert len(result["data"]) == 1
        assert result["has_next"] is False
        assert result["has_previous"] is True
        assert result["current_page"] == 2


class TestGetConversation(CustomTest):
    """Test Get conversation."""

    fixtures = [fixture_name]

    def test_get_conversation_success(self: Self) -> None:
        """Test getting a conversation by its ID."""
        conversation = Conversation.objects.get(id=1)

        result = self.controller.get_conversation(conversation.id, self.user)
        assert result == conversation

    def test_get_conversation_does_not_exist(self: Self) -> None:
        """Test getting a conversation that does not exist."""
        result = self.controller.get_conversation(234, self.user)
        assert result is None


class TestSetActiveConversation(CustomTest):
    """Test Set Active Conversation."""

    fixtures = [fixture_name]

    def test_set_active_conversation_success(self: Self) -> None:
        """Test setting an active conversation."""
        conversation = Conversation.objects.get(id=3)

        self.controller.set_active_conversation(self.user, conversation)
        assert CurrentConversation.objects.get(user=self.user).conversation == conversation


class TestGetConversationMessages(CustomTest):
    """Test user conversation retrieval."""

    fixtures = [fixture_name]

    def test_get_conversation_messages_pagination(self: Self) -> None:
        conversation_id = 1
        per_page = 2

        # Test with valid page number
        page = 1
        result = self.controller.get_conversation_messages(
            conversation_id,
            self.user.telegram_id,
            page,
            per_page,
        )

        # Check if the result contains the expected keys
        assert "data" in result
        assert "total_data" in result
        assert "total_pages" in result
        assert "current_page" in result
        assert "has_previous" in result
        assert "has_next" in result
        assert result["has_next"] is True
        assert result["has_previous"] is False

        # Check if the current_page matches the requested page
        assert result["current_page"] == page

        # Check if the number of returned conversations matches the per_page setting
        assert len(result["data"]) == per_page

        # Test with an invalid page number (less than 1)
        page = 0
        result = self.controller.get_conversation_messages(
            conversation_id,
            self.user.telegram_id,
            page,
            per_page,
        )
        assert result["current_page"] == 3  # Should default to the last page

        # Test with an invalid page number (greater than the total number of pages)
        page = result["total_pages"] + 1
        result = self.controller.get_conversation_messages(
            conversation_id,
            self.user.telegram_id,
            page,
            per_page,
        )
        assert result["current_page"] == result["total_pages"]  # Should default to the last page

        per_page = 2

        # Test with valid page number
        page = 3
        result = self.controller.get_conversation_messages(
            conversation_id,
            self.user.telegram_id,
            page,
            per_page,
        )
        assert result["has_next"] is False
        assert result["has_previous"] is True

        # Test with valid page number
        result = self.controller.get_conversation_messages(
            conversation_id,
            self.user.telegram_id,
            "a",
            per_page,  # type: ignore
        )
        assert result["current_page"] == 1  # Should default to the first page
