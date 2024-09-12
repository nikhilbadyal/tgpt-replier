"""Handle new command."""

# Import necessary libraries and modules
from typing import TYPE_CHECKING

from asgiref.sync import sync_to_async
from loguru import logger
from telethon import events

# Import some helper functions
from telegram.commands.utils import SupportedCommands, get_user

if TYPE_CHECKING:
    from telethon.tl.types import User


# Register the function to handle the /new command
@events.register(events.NewMessage(pattern=f"^{SupportedCommands.NEW.value}"))  # type: ignore
async def handle_new_command(event: events.NewMessage.Event) -> None:
    """Handle /new command.

    Args:
        event (events.NewMessage.Event): A new message event.

    Returns
    -------
        None: This function doesn't return anything.
    """
    # Import the main function for initiating a new conversation
    from main import gpt

    # Log that a request has been received to initiate a new conversation
    logger.debug("Received request to initiate new conversation")

    # Get the user associated with the message
    telegram_user: User = await get_user(event)

    # Define a prefix for the image URL
    prefix = f"{SupportedCommands.NEW.value}"
    # Pad by 1 to consider the space after command
    prefix = prefix.ljust(len(prefix) + 1)

    # Extract the image query from the message text
    prefix_len = len(prefix)
    title = event.message.text[prefix_len:]
    if len(title) == 0:
        title = None
    # Call the function to initiate a new conversation
    await sync_to_async(gpt.initiate_new_conversation)(telegram_user, title)

    # Send a success message if the conversation was initiated successfully, otherwise send an error message
    success = "Initiated new conversation."
    await event.respond(success)
