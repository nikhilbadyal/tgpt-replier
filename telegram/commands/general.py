"""Handle any other commands."""

# Import necessary libraries and modules
from asgiref.sync import sync_to_async
from loguru import logger
from telethon import events
from telethon.tl.types import User

from sqlitedb.utils import ErrorCodes

# Import some helper functions
from telegram.commands.strings import something_bad_occurred
from telegram.commands.utils import get_regex, get_user


# Register the function to handle any new message that matches the specified pattern
@events.register(events.NewMessage(pattern=get_regex()))  # type: ignore
async def handle_any_message(event: events.NewMessage.Event) -> None:
    """Handle any new message.

    Args:
        event (events.NewMessage.Event): A new message event.

    Returns:
        None: This function doesn't return anything.
    """
    # Import the main function for generating responses
    from main import gpt

    # Log that a request has been received
    logger.debug("Received request in general handler")

    # Check if the message is a private chat
    if event.is_private:
        # Get the user associated with the message
        user: User = await get_user(event)
        if user and not user.bot:
            # Check if the message contains text
            if event.message.text:
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
                await event.respond(something_bad_occurred)
        # If the user cannot be retrieved or is a bot, log an error
        else:
            logger.info("Cannot get Entity or a bot")
    # If the message is not a private chat, log a message
    else:
        logger.debug("Not a private message")
