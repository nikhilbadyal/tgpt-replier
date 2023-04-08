"""Models."""
from django.db import models

from manage import init_django

init_django()


class UserManager(models.Manager):  # type: ignore
    """Manager for the User model."""

    pass


class User(models.Model):
    """Model for storing user data.

    Attributes:
        id (int): The unique ID of the user.
        name (str or None): The name of the user, or None if no name was provided.
        telegram_id (int): The ID of the user.
        joining_date (datetime): The date and time when the user was added to the database.

    Managers:
        objects (UserManager): The custom manager for this model.

    Meta:
        db_table (str): The name of the database table used to store this model's data.

    Raises:
        IntegrityError: If the user's Telegram ID is not unique.
    """

    # User ID, auto-generated primary key
    id = models.AutoField(primary_key=True)

    # User name, max length of 255, can be null
    name = models.CharField(max_length=255, null=True)

    # User Telegram ID, integer
    telegram_id = models.IntegerField(unique=True)

    # Date and time when the user was added to the database, auto-generated
    joining_date = models.DateTimeField(auto_now_add=True)

    # Use custom manager for this model
    objects = UserManager()

    class Meta:
        # Database table name
        db_table = "user"


class Conversation(models.Model):
    """Model for storing conversation data.

    Attributes:
        id (int): The unique ID of the conversation.
        user (ForeignKey): The user associated with the conversation.

    Meta:
        db_table (str): The name of the database table used to store this model's data.
    """

    # Conversation ID, auto-generated primary key
    id = models.AutoField(primary_key=True)

    # User associated with the conversation
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # Title of the conversation
    title = models.CharField(max_length=255, null=True)

    class Meta:
        # Database table name
        db_table = "conversation"


class UserConversations(models.Model):
    """Model for storing user messages in a conversation.

    Attributes:
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

    class Meta:
        # Database table name
        db_table = "user_conversations"


class CurrentConversationManager(models.Manager):  # type: ignore
    """Manager for the CurrentConversation model."""

    pass


class CurrentConversation(models.Model):
    """Model for storing the current conversation of a user.

    Attributes:
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

    class Meta:
        # Database table name
        db_table = "current_conversation"


class ImagesManager(models.Manager):  # type: ignore
    """Manager for the UserImages model."""

    pass


class UserImages(models.Model):
    """Model for storing user images.

    Attributes:
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
    image_caption = models.TextField(null=True)

    # URL where the image is stored
    image_url = models.TextField()

    # Flag indicating if image is from the bot or user
    from_bot = models.BooleanField()

    # Date and time image was sent, auto-generated on creation
    message_date = models.DateTimeField(auto_now_add=True)

    # Use custom manager for this model
    objects = ImagesManager()

    class Meta:
        # Database table name
        db_table = "user_images"
