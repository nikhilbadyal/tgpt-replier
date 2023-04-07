"""Handle resetimages/resetmessages."""
# Import necessary libraries and modules
import re

from asgiref.sync import sync_to_async
from loguru import logger
from telethon import events
from telethon.tl.types import User

# Import some helper functions
from sqlitedb.utils import ErrorCodes
from telegram.commands.strings import cleanup_success, something_bad_occurred
from telegram.commands.utils import get_user


# Register the function to handle the /reset command
@events.register(events.NewMessage(pattern="^/reset(messages|images)$"))  # type: ignore
async def handle_reset_messages_images_command(event: events.NewMessage.Event) -> None:
    """Handle /resetmessages or /resetimages command. Delete all message
    history of a certain type for a user.

    Args:
        event (events.NewMessage.Event): A new message event.

    Returns:
        None: This function doesn't return anything.
    """
    # Import the main function for cleaning up user data
    from main import gpt

    # Get the user associated with the message
    telegram_user: User = await get_user(event)

    # Get the original message text and extract the request type
    original_message = event.message.text
    match = re.search(r"^/reset(.+)$", original_message)
    if match:
        request = match.group(1)

        # Log that a request has been received to delete all message history of a certain type
        logger.debug(f"Received request to delete all {request}")

        # Call the function to clean up user data
        result = await sync_to_async(gpt.clean_up_user_data)(
            original_message, telegram_user
        )

        # Log the number of items deleted
        logger.debug(f"Removed {result} {request}")

        # Send a success message if items were deleted, otherwise send an error message
        if result > ErrorCodes.exceptions.value:
            await event.respond(cleanup_success)
        else:
            await event.respond(something_bad_occurred)
