"""Handle any other commands."""

# Import necessary libraries and modules
from typing import TYPE_CHECKING

from asgiref.sync import sync_to_async
from loguru import logger
from telethon import events

from sqlitedb.utils import ErrorCodes

# Import some helper functions
from telegram.commands.strings import no_input, something_bad_occurred
from telegram.commands.utils import SupportedCommands, get_regex

if TYPE_CHECKING:
    from telethon.tl.types import User


# Register the function to handle any new message that matches the specified pattern
@events.register(events.NewMessage(pattern=get_regex()))  # type: ignore
async def handle_any_message(event: events.NewMessage.Event) -> None:
    """Handle any new message.

    Args:
        event (events.NewMessage.Event): A new message event.

    Returns
    -------
        None: This function doesn't return anything.
    """
    # Import the main function for generating responses
    from main import gpt

    # Log that a request has been received
    logger.debug("Received request in general handler")

    user: User = await event.get_sender()
    if user and not user.bot:
        # Check if the message contains text
        if event.message.text.strip() and event.message.text.strip() != SupportedCommands.CHAT.value:
            # Generate a response based on the user and the message text
            message = await sync_to_async(gpt.chat)(user, event.message.text)
            # If the response is an integer, send a cleanup message instead
            if isinstance(message, ErrorCodes):
                await event.respond(something_bad_occurred)
            # Otherwise, send the response
            else:
                await event.respond(message)
        # If the message doesn't contain text, send a cleanup message
        else:
            logger.debug("No text received in event.")
            await event.respond(no_input)
    # If the user cannot be retrieved or is a bot, log an error
    else:
        logger.info("Cannot get Entity or a bot")
