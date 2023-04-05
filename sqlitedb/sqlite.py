"""SQLite database to store messages."""
from typing import Any, Tuple

from sqlitedb.models import (
    Conversation,
    CurrentConversation,
    User,
    UserConversations,
    UserImages,
)


class SQLiteDatabase(object):
    """SQLite database Object."""

    def get_messages_by_user(self, user_id: int) -> Any:
        """Retrieve a list of messages for a user from the database.

        Args:
            user_id (int): The ID of the user for which to retrieve messages.

        Returns:
            Any: A list of message tuples for the specified user. Each tuple contains two elements:
                                    - from_bot: a boolean indicating whether the message is from the bot
                                    - message: the text of the message
        """
        queryset = UserConversations.objects.filter(user__telegram_id=user_id).values(
            "from_bot", "message"
        )
        return queryset

    def _get_user(self, telegram_id: int) -> User:
        """Retrieve a User object from the database for a given user_id. If the
        user does not exist, create a new user.

        Args:
            telegram_id (int): The ID of the user to retrieve or create.

        Returns:
            User: The User object corresponding to the specified user_id.
        """
        try:
            user: User = User.objects.get(telegram_id=telegram_id)
        except User.DoesNotExist:
            # User does not exist, create a new user
            new_user = User(telegram_id=telegram_id, name=f"User {telegram_id}")
            new_user.save()
            return new_user
        return user

    def _get_current_conversation(self, user: User) -> int:
        """Retrieve a CurrentConversation object from the database given a User
        object.

        Args:
            user (User): The User object for which to retrieve the current conversation.

        Returns:
            CurrentConversation: The CurrentConversation object corresponding to the user's current conversation.
        """
        try:
            current_conversation = CurrentConversation.objects.get(id=user.id)
            conversation_id = int(current_conversation.conversation_id)
        except CurrentConversation.DoesNotExist:
            # Current conversation does not exist, create a new conversation
            conversation = Conversation(user=user)
            conversation.save()
            current_conversation = CurrentConversation(
                user=user, conversation=conversation
            )
            current_conversation.save()
            conversation_id = int(current_conversation.conversation_id)
        return conversation_id

    def _get_conversation_id(self, current_conversation: CurrentConversation) -> int:
        """Retrieve the conversation ID from a CurrentConversation object.

        Args:
            current_conversation (CurrentConversation):
            The CurrentConversation object from which to extract the conversation ID.

        Returns:
            int: The conversation ID extracted from the CurrentConversation object.
        """
        return int(current_conversation.conversation.id)

    def _create_conversation(self, user_id: int, message: str, from_bot: bool) -> None:
        """Create a new Conversations object and save it to the database.

        Args:
            user_id (int): The ID of the user who sent the message.
            message (str): The message text to be saved in the Conversations object.
            from_bot (bool): Whether the message is from the bot.
        """
        user = self._get_user(user_id)
        conversation_id = self._get_current_conversation(user)
        conversation = UserConversations(
            user=user,
            message=message,
            from_bot=from_bot,
            conversation_id=conversation_id,
        )
        conversation.save()

    def insert_message_from_user(self, message: str, user_id: int) -> None:
        """Insert a new conversation message into the database for a user.

        Args:
            message (str): The message text to be saved in the Conversations object.
            user_id (int): The ID of the user who sent the message.
        """
        self._create_conversation(user_id, message, False)

    def insert_message_from_gpt(self, message: str, user_id: int) -> None:
        """Insert a new conversation message into the database from the GPT
        model.

        Args:
            message (str): The message text to be saved in the Conversations object.
            user_id (int): The ID of the user who received the message from the GPT model.
        """
        self._create_conversation(user_id, message, True)

    def insert_images_from_gpt(
        self, image_caption: str, image_url: str, telegram_id: int
    ) -> None:
        """Insert a new image record into the database for a user.

        Args:
            image_caption (str): The caption text for the image (optional).
            image_url (str): The URL of the image file.
            user_id (int): The ID of the user who uploaded the image.
        """
        user = self._get_user(telegram_id)
        image = UserImages(
            user=user,
            image_caption=image_caption,
            image_url=image_url,
            from_bot=True,
        )
        image.save()

    def delete_all_user_messages(self, telegram_id: int) -> int:
        """Delete all conversations for a user from the database.

        Args:
            telegram_id (int): The ID of the user for which to delete conversations.

        Returns:
            int: The number of conversations deleted.
        """
        conversations = UserConversations.objects.filter(user__telegram_id=telegram_id)
        num_deleted = int(conversations.delete()[0])
        return num_deleted

    def delete_all_user_images(self, telegram_id: int) -> int:
        """Delete all the messages associated with the user."""
        """Delete all images for a user from the database.

        Args:
            user_id (int): The ID of the user for which to delete images.

        Returns:
            int: The number of images deleted.
        """
        images = UserImages.objects.filter(user__telegram_id=telegram_id)
        num_deleted = int(images.delete()[0])
        return num_deleted

    def delete_all_user_data(self, telegram_id: int) -> Tuple[int, int]:
        """Delete all the messages associated with the user."""
        """Delete all conversations and images for a user from the database.

        Args:
            user_id (int): The ID of the user for which to delete data.

        Returns:
            Tuple[int, int]: A tuple containing the number of conversations and images that were deleted, respectively.
        """
        num_conv_deleted, num_img_deleted = self.delete_all_user_messages(
            telegram_id
        ), self.delete_all_user_images(telegram_id)
        return num_conv_deleted, num_img_deleted
