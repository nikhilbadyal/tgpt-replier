"""Test Cases."""
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from django.test import TestCase

from sqlitedb.models import Conversation, CurrentConversation, User, UserConversations
from sqlitedb.sqlite import SQLiteDatabase
from sqlitedb.utils import ErrorCodes


class GetMessagesByUserTestCase(TestCase):
    fixtures = ["test_fixtures.json"]

    def test_get_messages_by_user(self) -> None:
        # Get the user from the fixture
        user = User.objects.get(telegram_id=123456789)

        # Instantiate the class containing the function
        controller = SQLiteDatabase()

        # Call the get_messages_by_user function
        messages = controller.get_messages_by_user(user.telegram_id)

        current_conversation = CurrentConversation.objects.get(user=user)

        # Get the expected messages from the fixture
        expected_messages = (
            UserConversations.objects.filter(
                user=user, conversation=current_conversation.conversation
            )
            .values("from_bot", "message")
            .order_by("message_date")
        )

        # Compare the messages returned by the function with the expected messages
        self.assertEqual(list(messages), list(expected_messages))

    def test_get_messages_by_user_from_fixture(self) -> None:
        # Create a user
        user = User.objects.get(telegram_id=123456789)

        # Load the fixture data
        fixture_dir = Path(__file__).resolve().parent.parent
        fixture_path = Path(f"{fixture_dir}/fixtures/test_fixtures.json")
        with fixture_path.open() as f:
            fixture_data = json.load(f)

        # Extract expected messages from the fixture
        expected_messages = [
            obj["fields"]
            for obj in fixture_data
            if obj["model"] == "sqlitedb.userconversations"
        ]

        # Instantiate the class containing the function
        controller = SQLiteDatabase()

        # Call the get_messages_by_user function
        actual_messages = controller.get_messages_by_user(user.telegram_id)

        # Check that the function returns the correct actual messages
        for idx, message in enumerate(actual_messages):
            self.assertEqual(message["from_bot"], expected_messages[idx]["from_bot"])
            self.assertEqual(message["message"], expected_messages[idx]["message"])

    def test_get_messages_by_user_multiple_conversations(self) -> None:
        # Create a user
        user = User.objects.get(telegram_id=123456789)

        fixture_dir = Path(__file__).resolve().parent.parent
        fixture_path = Path(f"{fixture_dir}/fixtures/test_fixtures.json")
        with fixture_path.open() as f:
            fixture_data = json.load(f)

        # Extract expected messages from the fixture
        expected_messages = [
            obj["fields"]
            for obj in fixture_data
            if obj["model"] == "sqlitedb.userconversations"
            and obj["fields"]["conversation"] == 1
        ]

        # Instantiate the class containing the function
        controller = SQLiteDatabase()

        # Call the get_messages_by_user function
        messages = controller.get_messages_by_user(user.telegram_id)

        # Check that the function returns the correct messages from the current conversation
        for idx, message in enumerate(messages):
            print(message["message"])
            print(expected_messages[idx]["message"])
            self.assertEqual(message["from_bot"], expected_messages[idx]["from_bot"])
            self.assertEqual(message["message"], expected_messages[idx]["message"])

    def test_get_messages_by_user_no_current_conversation(self) -> None:
        # Create a user
        user = User.objects.get(telegram_id=5432198760)

        # Instantiate the class containing the function
        controller = SQLiteDatabase()

        # Call the get_messages_by_user function
        messages = controller.get_messages_by_user(user.telegram_id)

        # Check that the function returns an empty list since there is no current conversation
        self.assertEqual(len(messages), 0)


class GetUserTestCase(TestCase):
    fixtures = ["test_fixtures.json"]

    def test_get_user_existing_user(self) -> None:
        """Test if the _get_user method retrieves an existing user
        correctly."""
        telegram_id = 123456789
        user = User.objects.get(telegram_id=telegram_id)

        # Instantiate the class containing the function
        controller = SQLiteDatabase()

        # Call the _get_user function
        retrieved_user = controller.get_user(telegram_id)

        # Check that the function returns the correct user
        self.assertEqual(retrieved_user, user)

    def test_get_user_create_new_user(self) -> None:
        """Test if the _get_user method creates a new user when the user does
        not exist."""
        # Set a non-existing user telegram_id
        non_existing_telegram_id = 9876543210

        # Instantiate the class containing the function
        controller = SQLiteDatabase()

        # Call the _get_user function
        new_user = controller.get_user(non_existing_telegram_id)

        # Check that the function returns a User object
        self.assertIsInstance(new_user, User)
        if isinstance(new_user, int):  # To Silence mypy error
            return
        # Check that the function creates and returns a new user
        self.assertEqual(new_user.telegram_id, non_existing_telegram_id)
        self.assertEqual(new_user.name, f"User {non_existing_telegram_id}")

        # Cleanup: delete the created user
        new_user.delete()

    def test_get_user_creation_error(self) -> None:
        """Test if the _get_user method returns an error code when there's an
        issue creating a new user."""
        # Set a non-existing user telegram_id
        non_existing_telegram_id = 9876543210

        # Instantiate the class containing the function
        controller = SQLiteDatabase()

        # Patch the User.save() method to raise an exception
        with patch.object(User, "save", side_effect=Exception("Error creating user")):
            # Call the _get_user function
            result = controller.get_user(non_existing_telegram_id)

            # Check that the function returns the error code
            self.assertEqual(result, ErrorCodes.exceptions.value)


class GetCurrentConversation(TestCase):
    fixtures = ["test_fixtures.json"]

    def test_get_current_conversation_new(self) -> None:
        """Test if the _get_current_conversation method creates a new
        conversation and returns its ID when the user doesn't have a current
        conversation in the database."""
        telegram_id = 5432198760
        user = User.objects.get(telegram_id=telegram_id)

        # Mock the ChatGPT.send_text_completion_request method
        with patch(
            "chatgpt.chatgpt.ChatGPT.send_text_completion_request"
        ) as mock_send_text_completion_request:
            mock_send_text_completion_request.return_value = {
                "choices": [{"text": "Mocked Conversation"}]
            }

            # Instantiate the class containing the function
            controller = SQLiteDatabase()

            # Call the _get_current_conversation function
            conversation_id = controller._get_current_conversation(user, "Hello")

            # Check that a new conversation has been created
            new_conversation = Conversation.objects.get(id=conversation_id)
            self.assertIsNotNone(new_conversation)

            # Check that the new conversation has the correct title and user
            self.assertEqual(new_conversation.title, "Mocked Conversation")
            self.assertEqual(new_conversation.user, user)

            # Cleanup: delete the created user and conversation
            new_conversation.delete()
            user.delete()

    @patch("chatgpt.chatgpt.ChatGPT.send_text_completion_request")
    def test_send_text_completion_request_failure(
        self, mock_send_text_completion_request: MagicMock
    ) -> None:
        # Mock the send_text_completion_request method to return an error code
        telegram_id = 5432198760
        user = User.objects.get(telegram_id=telegram_id)
        mock_send_text_completion_request.return_value = ErrorCodes.exceptions.value

        # Instantiate the class containing the function
        controller = SQLiteDatabase()

        # Call the _get_current_conversation method and check if it returns the error code
        conversation_id = controller._get_current_conversation(user, "Hello")
        self.assertEqual(conversation_id, ErrorCodes.exceptions.value)

    @patch("chatgpt.chatgpt.ChatGPT.send_text_completion_request")
    @patch("sqlitedb.models.Conversation.save")
    def test_exception_in_get_current_conversation(
        self,
        mock_send_text_completion_request: MagicMock,
        mock_conversation_save: MagicMock,
    ) -> None:
        # Mock the send_text_completion_request method to return a valid response
        telegram_id = 5432198760
        user = User.objects.get(telegram_id=telegram_id)
        mock_send_text_completion_request.return_value = {
            "choices": [{"text": "Sample Chat Title"}]
        }

        # Mock the Conversation.save method to raise an exception
        mock_conversation_save.side_effect = Exception("Simulated exception")
        # Instantiate the class containing the function
        controller = SQLiteDatabase()

        # Call the _get_current_conversation method and check if it returns the error code
        conversation_id = controller._get_current_conversation(user, "hello")
        self.assertEqual(conversation_id, ErrorCodes.exceptions.value)

    def test_get_current_conversation_existing(self) -> None:
        """Test if the _get_current_conversation method returns the correct
        conversation ID when the user already has a current conversation in the
        database."""
        telegram_id = 123456789
        user = User.objects.get(telegram_id=telegram_id)

        conversation = Conversation.objects.get(pk=1)

        # Instantiate the class containing the function
        controller = SQLiteDatabase()

        # Call the _get_current_conversation function
        conversation_id = controller._get_current_conversation(user, "Hello")

        # Check that the function returns the correct conversation ID
        self.assertEqual(conversation_id, conversation.id)


class CreateConversation(TestCase):
    fixtures = ["test_fixtures.json"]

    def test_create_conversation_success(self) -> None:
        """Test if the _create_conversation method successfully creates and
        saves a new conversation."""
        telegram_id = 123456789
        user = User.objects.get(telegram_id=telegram_id)

        # Instantiate the class containing the function
        controller = SQLiteDatabase()

        # Call the _create_conversation function
        result = controller._create_conversation(
            user.telegram_id, "Test message", False
        )

        # Check if the conversation was created successfully
        self.assertEqual(result, ErrorCodes.success.value)

        # Verify if the conversation was saved in the database
        saved_conversation = UserConversations.objects.get(
            user=user, message="Test message", from_bot=False
        )
        self.assertIsNotNone(saved_conversation)

    def test_create_conversation_fail(self) -> None:
        """Test if the _create_conversation method returns an error code when
        it fails to get the current conversation."""
        telegram_id = 123456789
        user = User.objects.get(telegram_id=telegram_id)

        # Instantiate the class containing the function
        controller = SQLiteDatabase()

        # Use patch to modify the behavior of _get_current_conversation
        with patch.object(
            controller, "_get_current_conversation"
        ) as mock_get_current_conversation:
            mock_get_current_conversation.return_value = ErrorCodes.exceptions.value

            # Call the _create_conversation function
            result = controller._create_conversation(
                user.telegram_id, "Test message", False
            )

            # Check if the function returns an error code
            self.assertEqual(result, ErrorCodes.exceptions.value)

    @patch("sqlitedb.models.UserConversations.save")
    def test_exception_in_get_current_conversation(
        self, mock_conversation_save: MagicMock
    ) -> None:
        # Mock the send_text_completion_request method to return a valid response

        # Mock the Conversation.save method to raise an exception
        mock_conversation_save.side_effect = Exception("Simulated exception")
        # Instantiate the class containing the function
        controller = SQLiteDatabase()

        # Call the _get_current_conversation method and check if it returns the error code
        conversation_id = controller._create_conversation(
            1234567890, "Test message", False
        )
        self.assertEqual(conversation_id, ErrorCodes.exceptions.value)

    def test_create_conversation_get_user_error(self) -> None:
        """Test if the _create_conversation method returns an error code when
        the _get_user method returns an error code."""
        # Instantiate the class containing the function
        controller = SQLiteDatabase()

        # Use patch to modify the behavior of _get_user
        with patch.object(controller, "_get_user") as mock_get_user:
            mock_get_user.return_value = ErrorCodes.exceptions.value

            # Call the _create_conversation function
            result = controller._create_conversation(1234567890, "Test message", False)

            # Check if the function returns an error code
            self.assertEqual(result, ErrorCodes.exceptions.value)

    def test_create_conversation_get_current_conversation_error(self) -> None:
        """Test if the _create_conversation method returns an error code when
        the _get_current_conversation method returns an error code."""
        # Instantiate the class containing the function
        controller = SQLiteDatabase()

        telegram_id = 123456789
        user = User.objects.get(telegram_id=telegram_id)

        # Monkey patch the _get_current_conversation method to return an error code

        # Use patch to modify the behavior of _get_current_conversation
        with patch.object(
            controller, "_get_current_conversation"
        ) as mock_get_current_conversation:
            mock_get_current_conversation.return_value = ErrorCodes.exceptions.value

            # Call the _create_conversation function
            result = controller._create_conversation(
                user.telegram_id, "Test message", False
            )

            # Check if the function returns an error code
            self.assertEqual(result, ErrorCodes.exceptions.value)

    def test_insert_message_from_user(self) -> None:
        """Test if the message from user is inserted."""
        # Instantiate the class containing the function
        controller = SQLiteDatabase()

        telegram_id = 123456789

        # Monkey patch the _get_current_conversation method to return an error code
        messages_by_user_before = UserConversations.objects.filter(
            user__telegram_id=telegram_id, from_bot=False
        )
        messages_by_bot_before = UserConversations.objects.filter(
            user__telegram_id=telegram_id, from_bot=True
        )
        total_messages_by_user_before = len(messages_by_user_before)
        total_messages_by_bot_before = len(messages_by_bot_before)
        status = controller.insert_message_from_user("From User", telegram_id)
        assert status == ErrorCodes.success.value
        messages_by_user_after = UserConversations.objects.filter(
            user__telegram_id=telegram_id, from_bot=False
        )
        messages_by_bot_after = UserConversations.objects.filter(
            user__telegram_id=telegram_id, from_bot=True
        )
        total_messages_by_user_after = len(messages_by_user_after)
        total_messages_by_bot_after = len(messages_by_bot_after)
        self.assertEqual(
            total_messages_by_user_before + 1, total_messages_by_user_after
        )
        self.assertEqual(total_messages_by_bot_before, total_messages_by_bot_after)

    def test_insert_message_from_bot(self) -> None:
        """Test if the message from user is inserted."""
        # Instantiate the class containing the function
        controller = SQLiteDatabase()

        telegram_id = 123456789

        # Monkey patch the _get_current_conversation method to return an error code
        messages_by_user_before = UserConversations.objects.filter(
            user__telegram_id=telegram_id, from_bot=False
        )
        messages_by_bot_before = UserConversations.objects.filter(
            user__telegram_id=telegram_id, from_bot=True
        )
        total_messages_by_user_before = len(messages_by_user_before)
        total_messages_by_bot_before = len(messages_by_bot_before)
        status = controller.insert_message_from_gpt("From GPT", telegram_id)
        assert status == ErrorCodes.success.value
        messages_by_user_after = UserConversations.objects.filter(
            user__telegram_id=telegram_id, from_bot=False
        )
        messages_by_bot_after = UserConversations.objects.filter(
            user__telegram_id=telegram_id, from_bot=True
        )
        total_messages_by_user_after = len(messages_by_user_after)
        total_messages_by_bot_after = len(messages_by_bot_after)
        self.assertEqual(total_messages_by_user_before, total_messages_by_user_after)
        self.assertEqual(total_messages_by_bot_before + 1, total_messages_by_bot_after)


class DeleteAllUserMessagesTest(TestCase):
    fixtures = ["test_fixtures.json"]

    def test_delete_all_user_messages(self) -> None:
        """Test if the delete_all_user_messages method successfully deletes all
        conversations for a user."""
        telegram_id = 123456789
        user = User.objects.get(telegram_id=telegram_id)

        # Create a few conversations for the user
        conversations = [
            Conversation(user=user, title=f"Sample Conversation {i}")
            for i in range(1, 4)
        ]
        Conversation.objects.bulk_create(conversations)

        # Instantiate the class containing the function
        controller = SQLiteDatabase()

        # Call the delete_all_user_messages function
        controller.delete_all_user_messages(user.telegram_id)

        # Check if the conversations are deleted
        remaining_conversations = Conversation.objects.filter(
            user__telegram_id=user.telegram_id
        )
        self.assertFalse(remaining_conversations.exists())

    @patch("sqlitedb.models.Conversation.objects.filter")
    def test_exception_in_delete_all_user_messages(
        self, mock_conversations_filter: MagicMock
    ) -> None:
        # Mock the Conversation.objects.filter method to raise an exception
        mock_conversations_filter.side_effect = Exception("Simulated exception")

        # Call the delete_all_user_messages method and check if it returns the error code
        telegram_id = 123456789
        controller = SQLiteDatabase()
        result = controller.delete_all_user_messages(telegram_id)
        self.assertEqual(result, ErrorCodes.exceptions.value)


class TestInitiateNewConversation(TestCase):
    fixtures = ["test_fixtures.json"]

    def test_initiate_new_conversation_success(self) -> None:
        """Test if the initiate_new_conversation method successfully creates a
        new conversation."""
        telegram_id = 123456789
        user = User.objects.get(telegram_id=telegram_id)
        # Instantiate the class containing the function
        controller = SQLiteDatabase()
        # Call the initiate_new_conversation method
        result = controller.initiate_new_conversation(telegram_id, "Test Title")

        # Check if the function returns a success value
        self.assertEqual(result, ErrorCodes.success.value)

        # Check if the new conversation is created in the database
        conversation = Conversation.objects.get(user=user, title="Test Title")
        self.assertIsNotNone(conversation)

        # Check if the current conversation is set to the new conversation
        current_conversation = CurrentConversation.objects.get(user=user)
        self.assertEqual(current_conversation.conversation, conversation)

    @patch("sqlitedb.models.CurrentConversation.save")
    def test_initiate_new_conversation_save_current_conversation_exception(
        self, mock_save: MagicMock
    ) -> None:
        """Test if the initiate_new_conversation method handles an exception
        raised during saving the CurrentConversation object."""
        telegram_id = 123456789
        user = User.objects.get(telegram_id=telegram_id)
        mock_save.side_effect = Exception("Saving current conversation failed.")

        # Call the initiate_new_conversation method
        # Instantiate the class containing the function
        controller = SQLiteDatabase()
        result = controller.initiate_new_conversation(telegram_id, "Test Title")

        # Check if the function returns an error value
        self.assertEqual(result, ErrorCodes.exceptions.value)

        # Check if the conversation is deleted from the database
        with self.assertRaises(Conversation.DoesNotExist):
            Conversation.objects.get(user=user, title="Test Title")
