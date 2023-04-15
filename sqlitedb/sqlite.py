"""SQLite database to store messages."""
from typing import Any, Tuple

from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from loguru import logger

from chatgpt.chatgpt import ChatGPT
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

    def get_messages_by_user(self, telegram_id: int) -> Any:
        """Retrieve a list of messages for a user from the database.

        Args:
            telegram_id (int): The ID of the user for which to retrieve messages.

        Returns:
            Any: A list of message tuples for the specified user. Each tuple contains two elements:
                                    - from_bot: a boolean indicating whether the message is from the bot
                                    - message: the text of the message
        """
        user = self._get_user(telegram_id)

        try:
            current_conversation = CurrentConversation.objects.get(user=user)
        except CurrentConversation.DoesNotExist:
            logger.error(f"No current conversation found for user with ID {user}.")
            # TODO: Handle properly
            return []

        messages = UserConversations.objects.filter(
            user=user, conversation=current_conversation.conversation
        ).values("from_bot", "message")
        messages = messages.order_by("message_date")

        return messages

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

    def _get_current_conversation(self, user: User, message: str) -> int:
        """Retrieve a CurrentConversation object from the database given a User
        object.

        Args:
            user (User): The User object for which to retrieve the current conversation.

        Returns:
            int: The ID of the user's current conversation, or -1 if an error occurs.
        """
        try:
            current_conversation = CurrentConversation.objects.get(user=user)
            conversation_id = int(current_conversation.conversation_id)
        except CurrentConversation.DoesNotExist:
            logger.info(f"No current conversation exists for user {user}")
            try:
                openai_response = ChatGPT.send_text_completion_request(message)
                if isinstance(openai_response, int):
                    return ErrorCodes.exceptions.value
                chat_title = openai_response["choices"][0]["text"]
                conversation = Conversation(user=user, title=chat_title)
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
                conversation_id = self._get_current_conversation(user, message)
                if conversation_id <= ErrorCodes.exceptions.value:
                    logger.error("Unable to get current conversation")
                    return ErrorCodes.exceptions.value
                conversation = UserConversations(
                    user=user,
                    message=message,
                    from_bot=from_bot,
                    conversation_id=conversation_id,
                )
                conversation.save()
                return ErrorCodes.success.value
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
            conversations = Conversation.objects.filter(user__telegram_id=telegram_id)
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

    def initiate_new_conversation(self, telegram_id: int, title: str) -> int:
        """Initiates a new conversation for a user by creating a new
        Conversation object and a new CurrentConversation object.

        Args:
            telegram_id (int): The ID of the user for which to start a new conversation.
            title (str): The title of the new conversation.

        Returns:
            ConversationResult: The result of the conversation creation operation.
        """
        user = self._get_user(telegram_id)

        conversation = Conversation(user=user, title=title)
        try:
            conversation.save()
        except Exception as e:
            logger.error(
                f"An error occurred while saving conversation to the database: {e}"
            )
            return ErrorCodes.exceptions.value

        try:
            current_conversation = CurrentConversation.objects.get(user=user)
            current_conversation.conversation = conversation
        except CurrentConversation.DoesNotExist:
            current_conversation = CurrentConversation(
                user=user, conversation=conversation
            )

        try:
            current_conversation.save()
        except Exception as e:
            logger.error(
                f"An error occurred while saving current conversation to the database: {e}"
            )
            conversation.delete()
            return ErrorCodes.exceptions.value

        return ErrorCodes.success.value

    def initiate_empty_new_conversation(self, telegram_id: int) -> int:
        """Initiates a new empty conversation for a user by creating a new
        Conversation object and a new CurrentConversation object.

        Args:
            telegram_id (int): The ID of the user for which to start a new conversation.

        Returns:
            ConversationResult: The result of the conversation creation operation.
        """
        user = self._get_user(telegram_id)

        try:
            CurrentConversation.objects.get(user=user).delete()
        except CurrentConversation.DoesNotExist:
            logger.info(f"No current conversation for user {user}")
        return ErrorCodes.success.value

    def get_user_conversations(self, telegram_id: int, page: int, per_page: int) -> Any:
        """Return a paginated list of conversations for a given user.

        Args:
            telegram_id (int): The ID of the user.
            page (int): The current page number.
            per_page (int): The number of conversations to display per page.

        Returns:
            dict: A dictionary containing the paginated conversations and pagination details.
        """
        user = self._get_user(telegram_id)

        # Retrieve the conversations for the given user
        conversations = Conversation.objects.filter(user=user).order_by("-start_time")

        # Create a Paginator object
        paginator = Paginator(conversations, per_page)

        # Get the paginated conversations
        try:
            paginated_conversations = paginator.page(page)
        except PageNotAnInteger:
            # If the page is not an integer, show the first page
            paginated_conversations = paginator.page(1)
        except EmptyPage:
            # If the page is out of range, show the last available page
            paginated_conversations = paginator.page(paginator.num_pages)

        conversation_len = len(paginated_conversations)
        logger.debug(f"Found {conversation_len} conversations.")

        # Return the paginated conversations and pagination details
        return {
            "conversations": paginated_conversations,
            "total_conversations": paginator.count,
            "total_pages": paginator.num_pages,
            "current_page": paginated_conversations.number,
            "has_previous": paginated_conversations.has_previous(),
            "has_next": paginated_conversations.has_next(),
        }
