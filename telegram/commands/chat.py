"""Handle Chat Command."""

from loguru import logger
from telethon import TelegramClient, events

from telegram.commands.general import handle_any_message
from telegram.commands.utils import SupportedCommands


def add_chat_handler(client: TelegramClient) -> None:
    """Add /chat command Event Handler."""
    client.add_event_handler(handle_chat_command)


# Register the function to handle the /switch command
@events.register(events.NewMessage(pattern=f"^{SupportedCommands.CHAT.value}"))  # type: ignore
async def handle_chat_command(event: events.NewMessage.Event) -> None:
    """Event handler for the /chat command.

    Args:
        event (NewMessage.Event): The new message event.
    """
    # Log that a request has been received to switch conversation
    logger.debug("Received request for chat conversation")

    # It just forwards the request to the general handler
    await handle_any_message(event)
