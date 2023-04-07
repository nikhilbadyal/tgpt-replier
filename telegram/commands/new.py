"""Handle new command."""

# Import necessary libraries and modules
from asgiref.sync import sync_to_async
from loguru import logger
from telethon import events
from telethon.tl.types import User

# Import some helper functions
from sqlitedb.utils import ErrorCodes
from telegram.commands.strings import something_bad_occurred
from telegram.commands.utils import get_user


# Register the function to handle the /new command
@events.register(events.NewMessage(pattern="^/new$"))  # type: ignore
async def handle_new_command(event: events.NewMessage.Event) -> None:
    """Handle /new command.

    Args:
        event (events.NewMessage.Event): A new message event.

    Returns:
        None: This function doesn't return anything.
    """
    # Import the main function for initiating a new conversation
    from main import gpt

    # Log that a request has been received to initiate a new conversation
    logger.debug("Received request to initiate new conversation")

    # Get the user associated with the message
    telegram_user: User = await get_user(event)

    # Call the function to initiate a new conversation
    status = await sync_to_async(gpt.initiate_new_conversation)(telegram_user)

    # Log the conversation ID
    logger.debug(f"Initiated new conversation with id {status}")

    # Send a success message if the conversation was initiated successfully, otherwise send an error message
    success = "Initiated new conversation."
    if status > ErrorCodes.exceptions.value:
        await event.respond(success)
    else:
        await event.respond(something_bad_occurred)
