"""SQLite database to store messages."""
from typing import Any, Tuple

from loguru import logger

from sqlitedb.models import (
    Conversation,
    CurrentConversation,
    User,
    UserConversations,
    UserImages,
)
from sqlitedb.utils import ErrorCodes


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

    def _get_user(self, telegram_id: int) -> User | int:
        """Retrieve a User object from the database for a given user_id. If the
        user does not exist, create a new user.

        Args:
            telegram_id (int): The ID of the user to retrieve or create.

        Returns:
            Union[User, int]: The User object corresponding to the specified user ID, or -1 if an error occurs.
        """
        try:
            user: User = User.objects.get(telegram_id=telegram_id)
        except User.DoesNotExist:
            # User does not exist, create a new user
            try:
                new_user = User(telegram_id=telegram_id, name=f"User {telegram_id}")
                new_user.save()
                return new_user
            except Exception as e:
                logger.error(f"Unable to create new user {e}")
                return ErrorCodes.exceptions.value
        return user

    def _get_current_conversation(self, user: User) -> int:
        """Retrieve a CurrentConversation object from the database given a User
        object.

        Args:
            user (User): The User object for which to retrieve the current conversation.

        Returns:
            int: The ID of the user's current conversation, or -1 if an error occurs.
        """
        try:
            current_conversation = CurrentConversation.objects.get(id=user.id)
            conversation_id = int(current_conversation.conversation_id)
        except CurrentConversation.DoesNotExist:
            # Current conversation does not exist, create a new conversation
            try:
                conversation = Conversation(user=user)
                conversation.save()
                current_conversation = CurrentConversation(
                    user=user, conversation=conversation
                )
                current_conversation.save()
                conversation_id = int(current_conversation.conversation_id)
            except Exception as e:
                logger.error(f"Unable to create new conversation {e}")
                return ErrorCodes.exceptions.value
        return conversation_id

    def _create_conversation(self, user_id: int, message: str, from_bot: bool) -> int:
        """Create a new Conversations object and save it to the database.

        Args:
            user_id (int): The ID of the user who sent the message.
            message (str): The message text to be saved in the Conversations object.
            from_bot (bool): Whether the message is from the bot.

        Returns:
            int: 0 if the conversation is successfully created and saved, or -1 if an error occurs.
        """
        try:
            user = self._get_user(user_id)
            if isinstance(user, User):
                conversation_id = self._get_current_conversation(user)
                conversation = UserConversations(
                    user=user,
                    message=message,
                    from_bot=from_bot,
                    conversation_id=conversation_id,
                )
                conversation.save()
                return 0
            return user
        except Exception as e:
            logger.error(f"Unable to save conversation {e}")
            return ErrorCodes.exceptions.value

    def insert_message_from_user(self, message: str, user_id: int) -> int:
        """Insert a new conversation message into the database for a user.

        Args:
            message (str): The message text to be saved in the Conversations object.
            user_id (int): The ID of the user who sent the message.
        Returns:
            int: 0 if the conversation is successfully created and saved, or -1 if an error occurs.
        """
        return self._create_conversation(user_id, message, False)

    def insert_message_from_gpt(self, message: str, user_id: int) -> int:
        """Insert a new conversation message into the database from the GPT
        model.

        Args:
            message (str): The message text to be saved in the Conversations object.
            user_id (int): The ID of the user who received the message from the GPT model.
        Returns:
            int: 0 if the conversation is successfully created and saved, or -1 if an error occurs.
        """
        return self._create_conversation(user_id, message, True)

    def insert_images_from_gpt(
        self, image_caption: str, image_url: str, telegram_id: int
    ) -> int:
        """Insert a new image record into the database for a user.

        Args:
            image_caption (str): The caption text for the image (optional).
            image_url (str): The URL of the image file.
            telegram_id (int): The ID of the user who uploaded the image.
        Returns:
            int: 0 if the image is successfully created and saved, or -1 if an error occurs.
        """
        try:
            user = self._get_user(telegram_id)
            image = UserImages(
                user=user,
                image_caption=image_caption,
                image_url=image_url,
                from_bot=True,
            )
            image.save()
            return 0
        except Exception as e:
            logger.error(f"Unable to save image {e}")
            return ErrorCodes.exceptions.value

    def delete_all_user_messages(self, telegram_id: int) -> int:
        """Delete all conversations for a user from the database.

        Args:
            telegram_id (int): The ID of the user for which to delete conversations.

        Returns:
        int: The number of conversations deleted, or -1 if an error occurs.
        """
        try:
            conversations = Conversation.objects.filter(
                user__telegram_id=telegram_id
            )
            num_deleted = int(conversations.delete()[0])
            return num_deleted
        except Exception as e:
            logger.error(f"Error deleting {e}")
            return ErrorCodes.exceptions.value

    def delete_all_user_images(self, telegram_id: int) -> int:
        """Delete all images for a user from the database.

        Args:
            telegram_id (int): The ID of the user for which to delete images.

        Returns:
        int: The number of images deleted, or -1 if an error occurs.
        """
        try:
            images = UserImages.objects.filter(user__telegram_id=telegram_id)
            num_deleted = int(images.delete()[0])
            return num_deleted
        except Exception as e:
            logger.error(f"Error deleting {e}")
            return ErrorCodes.exceptions.value

    def delete_all_user_data(self, telegram_id: int) -> Tuple[int, int]:
        """Delete all conversations and images for a user from the database.

        Args:
            telegram_id (int): The ID of the user for which to delete data.

        Returns:
            Tuple[int, int]: A tuple containing the number of conversations and images that were deleted, respectively,
             or (-1,-1) if an error occurs.
        """
        num_conv_deleted, num_img_deleted = self.delete_all_user_messages(
            telegram_id
        ), self.delete_all_user_images(telegram_id)
        return num_conv_deleted, num_img_deleted
