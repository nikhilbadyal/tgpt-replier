"""Handle Reset Command."""
# Import necessary libraries and modules
from asgiref.sync import sync_to_async
from loguru import logger
from telethon import events
from telethon.tl.types import User

# Import some helper functions
from sqlitedb.utils import ErrorCodes
from telegram.commands.strings import cleanup_success, something_bad_occurred
from telegram.commands.utils import get_user


# Register the function to handle the /reset command
@events.register(events.NewMessage(pattern="^/reset$"))  # type: ignore
async def handle_reset_command(event: events.NewMessage.Event) -> None:
    """Handle /reset command Delete all message history for a user.

    Args:
        event (events.NewMessage.Event): A new message event.

    Returns:
        None: This function doesn't return anything.
    """
    # Import the main function for cleaning up user data
    from main import gpt

    # Log that a request has been received to delete all user data
    logger.debug("Received request to delete all user data")

    # Get the user associated with the message
    telegram_user: User = await get_user(event)

    # Call the function to clean up user data
    num_conv_deleted, num_img_deleted = await sync_to_async(gpt.clean_up_user_data)(
        "/reset", telegram_user
    )

    # Log the number of items deleted
    logger.debug(f"Removed {num_conv_deleted} convo and {num_img_deleted} images")

    # Send a success message if items were deleted, otherwise send an error message
    if (
        num_conv_deleted > ErrorCodes.exceptions.value
        and num_img_deleted > ErrorCodes.exceptions.value
    ):
        await event.respond(cleanup_success)
    else:
        await event.respond(something_bad_occurred)
