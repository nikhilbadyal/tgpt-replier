"""Models."""

from typing import Self

from django.db import models
from django_stubs_ext.db.models import TypedModelMeta

from manage import init_django
from sqlitedb.utils import UserStatus

init_django()


class UserManager(models.Manager):  # type: ignore
    """Manager for the User model."""


class User(models.Model):
    """Model for storing user data.

    Attributes
    ----------
        id (int): The unique ID of the user.
        name (str or None): The name of the user, or None if no name was provided.
        telegram_id (int): The ID of the user.
        status (str): The current status of the user's account (active, suspended, or temporarily banned).
        joining_date (datetime): The date and time when the user was added to the database.
        last_updated (datetime): The date and time when the user's details were last updated.

    Managers:
        objects (UserManager): The custom manager for this model.

    Meta:
        db_table (str): The name of the database table used to store this model's data.

    Raises
    ------
        IntegrityError: If the user's Telegram ID is not unique.
    """

    # User ID, auto-generated primary key
    id = models.AutoField(primary_key=True)

    # User name, max length of 255, can be null
    name = models.CharField(max_length=255)

    # User Telegram ID, integer
    telegram_id = models.IntegerField(unique=True)

    # State of the user
    status = models.CharField(
        max_length=20,
        choices=[(status.value, status.name) for status in UserStatus],
        default=UserStatus.ACTIVE.value,
    )

    # Date and time when the user was added to the database, auto-generated
    joining_date = models.DateTimeField(auto_now_add=True)

    # Date and time when the user details was modified , auto-generated
    last_updated = models.DateTimeField(auto_now=True)

    # Conversation settings, stored as a JSON object
    settings = models.JSONField(default=dict)

    # Use custom manager for this model
    objects = UserManager()

    class Meta(TypedModelMeta):
        """Database table name."""

        db_table = "user"

    def __str__(self: Self) -> str:
        """Return a string representation of the user object."""
        return f"User(id={self.id}, name={self.name}, telegram_id={self.telegram_id}, status={self.status})"


class ConversationManager(models.Manager):  # type: ignore[type-arg]
    pass


class Conversation(models.Model):
    """Model for storing conversation data.

    Attributes
    ----------
        id (int): The unique ID of the conversation.
        user (ForeignKey): The user associated with the conversation.
        title (str or None): The title of the conversation, or None if no title was provided.
        start_time (datetime): The time when the conversation was started.

    Meta:
        db_table (str): The name of the database table used to store this model's data.
    """

    # Conversation ID, auto-generated primary key
    id = models.AutoField(primary_key=True)

    # User associated with the conversation
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # Conversation title, max length of 255, can be null
    title = models.CharField(max_length=255)

    # Start time of the conversation
    start_time = models.DateTimeField(auto_now_add=True, editable=False)

    objects = ConversationManager()

    class Meta(TypedModelMeta):
        """Database table name."""

        db_table = "conversation"

    def __str__(self: Self) -> str:
        """Return a string representation of the conversation object."""
        return f"Conversation(id={self.id}, user={self.user}, title={self.title}, start_time={self.start_time})"


class UserConversationsManager(models.Manager):  # type: ignore
    """Manager for the UserConversations model."""


class UserConversations(models.Model):
    """Model for storing user messages in a conversation.

    Attributes
    ----------
        id (int): The unique ID of the message.
        user (ForeignKey): The user associated with the message.
        message (str): The text of the message.
        from_bot (bool): True if the message was sent by the bot, False if it was sent by the user.
        conversation (ForeignKey): The conversation the message belongs to.
        message_date (datetime): The date and time the message was sent, auto-generated on creation.

    Meta:
        db_table (str): The name of the database table used to store this model's data.
    """

    # Message ID, auto-generated primary key
    id = models.AutoField(primary_key=True)

    # User associated with the message
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # Message text, stored as a string
    message = models.TextField()

    # Flag indicating if message is from the bot or user
    from_bot = models.BooleanField()

    # Conversation the message belongs to
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)

    # Date and time message was sent, auto-generated on creation
    message_date = models.DateTimeField(auto_now_add=True)

    objects = UserConversationsManager()

    class Meta(TypedModelMeta):
        """Database table name."""

        db_table = "user_conversations"

    def __str__(self: Self) -> str:
        """Return a string representation of the user conversation object."""
        return f"""
        UserConversations(id={self.id}, user={self.user}, message={self.message}, from_bot={self.from_bot},
        conversation={self.conversation}, message_date={self.message_date})
        """


class CurrentConversationManager(models.Manager):  # type: ignore
    """Manager for the CurrentConversation model."""


class CurrentConversation(models.Model):
    """Model for storing the current conversation of a user.

    Attributes
    ----------
        user (ForeignKey): The user associated with the current conversation.
        conversation (ForeignKey): The conversation the user is currently in.

    Managers:
        objects (CurrentConversationManager): The custom manager for this model.

    Meta:
        db_table (str): The name of the database table used to store this model's data.
    """

    # User associated with the current conversation
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # Conversation the user is currently in
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)

    # Use custom manager for this model
    objects = CurrentConversationManager()

    class Meta(TypedModelMeta):
        """Database table name."""

        db_table = "current_conversation"

    def __str__(self: Self) -> str:
        """Return a string representation of the current conversation object."""
        return f"CurrentConversation(user={self.user}, conversation={self.conversation})"


class ImagesManager(models.Manager):  # type: ignore
    """Manager for the UserImages model."""


class UserImages(models.Model):
    """Model for storing user images.

    Attributes
    ----------
        id (int): The unique ID of the image.
        user (ForeignKey): The user who sent the image.
        image_caption (str or None): The caption for the image, or None if no caption was provided.
        image_url (str): The URL where the image is stored.
        from_bot (bool): True if the image was sent by the bot, False if it was sent by the user.
        message_date (datetime): The date and time the image was sent, auto-generated on creation.

    Managers:
        objects (ImagesManager): The custom manager for this model.

    Meta:
        db_table (str): The name of the database table used to store this model's data.
    """

    # Image ID, auto-generated primary key
    id = models.AutoField(primary_key=True)

    # User who sent the image
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # Caption for the image, can be null
    image_caption = models.TextField()

    # URL where the image is stored
    image_url = models.TextField()

    # Flag indicating if image is from the bot or user
    from_bot = models.BooleanField()

    # Date and time image was sent, auto-generated on creation
    message_date = models.DateTimeField(auto_now_add=True)

    # Use custom manager for this model
    objects = ImagesManager()

    class Meta(TypedModelMeta):
        """Database table name."""

        db_table = "user_images"

    def __str__(self: Self) -> str:
        """Return a string representation of the user image object."""
        return f"""UserImages(id={self.id}, user={self.user}, image_caption={self.image_caption},
        image_url={self.image_url}, from_bot={self.from_bot}, message_date={self.message_date})"""
