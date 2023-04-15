"""Added /switch command."""
from asgiref.sync import sync_to_async
from loguru import logger
from telethon import TelegramClient, events

from sqlitedb.models import User
from telegram.commands.utils import SupportedCommands


def add_switch_handler(client: TelegramClient) -> None:
    """Add /switch command Event Handler."""
    client.add_event_handler(handle_switch_command)


# Register the function to handle the /switch command
@events.register(events.NewMessage(pattern=f"^{SupportedCommands.SWITCH.value}\\s+(\\d+)$"))  # type: ignore
async def handle_switch_command(event: events.NewMessage.Event) -> None:
    """Event handler for the /switch command.

    Args:
        event (NewMessage.Event): The new message event.
    """
    # Log that a request has been received to switch conversation
    logger.debug("Received request to switch conversation")

    conversation_id = event.pattern_match.group(1)
    if not conversation_id:
        await event.reply(
            "Please provide the conversation ID you want to switch to. Example: /switch 42"
        )
        return

    try:
        logger.debug(f"Switching to conversation {conversation_id} if possible.")
        conversation_id = int(conversation_id)
    except ValueError:
        await event.reply("Invalid conversation ID. Please provide a valid integer.")
        return

    telegram_id = event.message.sender_id
    from main import db

    user = await sync_to_async(db.get_user)(telegram_id=telegram_id)
    await switch_conversation(event, user, conversation_id)


# Handle the switch conversation callback
async def switch_conversation(
    event: events.NewMessage.Event, user: User, conversation_id: int
) -> None:
    """Switch the user's active conversation to the specified conversation.

    Args:
        event (NewMessage.Event): The new message event.
        user (User): The user object.
        conversation_id (int): The ID of the conversation to switch to.
    """
    from main import db

    # Check if the specified conversation belongs to the user
    conversation = await sync_to_async(db.get_conversation)(conversation_id, user)

    if conversation is None:
        await event.reply("The specified conversation does not exists.")
        return

    # If yes, switch the active conversation and send a confirmation message
    # This assumes that you have a method `set_active_conversation` in your database module
    # to set the active conversation for the user
    await sync_to_async(db.set_active_conversation)(user, conversation)
    await event.reply(
        f"Switched to conversation {conversation.title} (ID: {conversation.id})"
    )
