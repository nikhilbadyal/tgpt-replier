"""Handle Reset Command."""
# Import necessary libraries and modules
from typing import TYPE_CHECKING

from asgiref.sync import sync_to_async
from loguru import logger
from telethon import Button, TelegramClient, events

# Import some helper functions
from sqlitedb.utils import ErrorCodes
from telegram.commands.strings import cleanup_success, ignore, something_bad_occurred
from telegram.commands.utils import SupportedCommands, get_user

if TYPE_CHECKING:
    from telethon.tl.types import User

reset_yes_data = b"reset_yes"
reset_yes_description = "Yes!"
reset_no_data = b"reset_no"
reset_no_description = "No!"


def add_reset_handlers(client: TelegramClient) -> None:
    """Add /reset command Event Handler."""
    client.add_event_handler(handle_reset_command)
    client.add_event_handler(handle_reset_confirm_response)


@events.register(events.callbackquery.CallbackQuery(pattern="^reset_(yes|no)$"))  # type: ignore
async def handle_reset_confirm_response(
    event: events.callbackquery.CallbackQuery.Event,
) -> None:
    """Handle reset confirmation response.

    This function is registered as an event handler to handle the callback query
    generated when the user clicks one of the buttons in the confirmation message
    after sending the /reset command. If the user clicks the "Hell yes!" button,
    it imports the main function for cleaning up user data and calls it to delete
    all user data. If the user clicks the "Fuck, No!" button, it ignores the request.

    Args:
        event (events.callbackquery.CallbackQuery.Event): The event object associated with the callback query.

    Returns
    -------
        None: This function doesn't return anything.
    """
    await event.answer()
    logger.debug("Received reset callback")
    if event.data == reset_yes_data:
        # Import the main function for cleaning up user data
        from main import gpt

        # Get the user associated with the message
        telegram_user: User = await get_user(event)
        # Call the function to clean up user data
        num_conv_deleted, num_img_deleted = await sync_to_async(gpt.clean_up_user_data)(
            SupportedCommands.RESET.value,
            telegram_user,
        )

        # Log the number of items deleted
        logger.debug(f"Removed {num_conv_deleted} convo and {num_img_deleted} images")

        # Send a success message if items were deleted, otherwise send an error message
        if not isinstance(num_conv_deleted, ErrorCodes) and not isinstance(
            num_img_deleted,
            ErrorCodes,
        ):
            await event.edit(cleanup_success)
        else:
            await event.edit(something_bad_occurred)
    elif event.data == reset_no_data:
        await event.edit(ignore)


# Register the function to handle the /reset command
@events.register(events.NewMessage(pattern=f"^{SupportedCommands.RESET.value}$"))  # type: ignore
async def handle_reset_command(event: events.NewMessage.Event) -> None:
    """Handle /reset command Delete all message history for a user.

    Args:
        event (events.NewMessage.Event): A new message event.

    Returns
    -------
        None: This function doesn't return anything.
    """
    # Log that a request has been received to delete all user data
    logger.debug("Received request to delete all user data")

    await event.reply(
        "Are you sure you want to delete everything?",
        buttons=[
            [Button.inline(reset_yes_description, data=reset_yes_data)],
            [Button.inline(reset_no_description, data=reset_no_data)],
        ],
    )
