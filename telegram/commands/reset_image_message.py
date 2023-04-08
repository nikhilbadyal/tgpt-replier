"""Handle resetimages/resetmessages."""
# Import necessary libraries and modules
import re
from re import Match

from asgiref.sync import sync_to_async
from loguru import logger
from telethon import Button, TelegramClient, events
from telethon.tl.custom import Message
from telethon.tl.types import User

# Import some helper functions
from sqlitedb.utils import ErrorCodes
from telegram.commands.strings import cleanup_success, ignore, something_bad_occurred
from telegram.commands.utils import SupportedCommands, get_user

# Define constants for the /resetimages and /resetmessage commands
reset_yes_data = b"reset_im_yes"
reset_yes_description = "Yes!"
reset_no_data = b"reset_im_no"
reset_no_description = "No!"


def add_reset_image_message_handlers(client: TelegramClient) -> None:
    """Add /resetimages /resetmessage command event handlers.

    This function adds two event handlers to the Telegram client: handle_reset_messages_images_command
    and handle_reset_image_message_confirm_response. These event handlers are used to handle the /resetimages
    and /resetmessage commands respectively.

    Args:
        client (TelegramClient): The Telegram client object.

    Returns:
        None: This function doesn't return anything.
    """
    client.add_event_handler(handle_reset_messages_images_command)
    client.add_event_handler(handle_reset_image_message_confirm_response)


@events.register(events.callbackquery.CallbackQuery(pattern="^reset_im_(yes|no)$"))  # type: ignore
async def handle_reset_image_message_confirm_response(
    event: events.callbackquery.CallbackQuery.Event,
):
    """Handle reset confirmation response for image/message deletion.

    This function is registered as an event handler to handle user responses to the confirmation message
    sent by the handle_reset_messages_images_command function. If the user clicks the "Yes!" button,
    this function deletes all user data associated with the message or image of the specified type.
    If the user clicks the "No!" button, the request is ignored.

    Args:
        event (events.callbackquery.CallbackQuery.Event): The event object associated with the user's response.

    Returns:
        None: This function doesn't return anything.
    """
    logger.debug("Received reset image/message callback")
    if event.data == reset_yes_data:
        # Import the main function for cleaning up user data
        from main import gpt

        # Get the user associated with the message
        telegram_user: User = await get_user(event)
        replied_message = await event.get_message()
        reply_obj: Message = await replied_message.get_reply_message()
        reply_message = reply_obj.message
        match = re.search(f"^{SupportedCommands.RESET.value}(.+)$", reply_message)
        if isinstance(match, Match):
            request = match.group(1)

            # Call the function to clean up user data
            result = await sync_to_async(gpt.clean_up_user_data)(
                reply_message, telegram_user
            )

            # Log the number of items deleted
            logger.debug(f"Removed {result} {request}")

            # Send a success message if items were deleted, otherwise send an error message
            if isinstance(result, int) and result > ErrorCodes.exceptions.value:
                await event.edit(cleanup_success)
            else:
                await event.edit(something_bad_occurred)
        else:
            await event.edit(something_bad_occurred)
    elif event.data == reset_no_data:
        await event.edit(ignore)


# Register the function to handle the /reset command
@events.register(events.NewMessage(pattern=f"^{SupportedCommands.RESET.value}(messages|images)$"))  # type: ignore
async def handle_reset_messages_images_command(event: events.NewMessage.Event) -> None:
    """Handle /resetmessages and /resetimages commands.

    This function is registered as an event handler to handle the /resetmessages and /resetimages
    commands. It sends a confirmation message to the user to confirm whether they really want
    to delete all their message or image history of the specified type. The confirmation message
    contains two buttons: "Yes!" and "No!". If the user clicks the "Yes!" button,
    the handle_reset_image_message_confirm_response
    function is called to delete all user data associated with the message or image of the specified type.
    If the user clicks the "No!" button, the request is ignored.

    Args:
        event (events.NewMessage.Event): The event object associated with the /resetmessages or /resetimages command.

    Returns:
        None: This function doesn't return anything.
    """
    # Get the original message text and extract the request type
    original_message = event.message.text
    match = re.search(f"^{SupportedCommands.RESET.value}(.+)$", original_message)
    if match:
        request = match.group(1)

        # Log that a request has been received to delete all message history of a certain type
        logger.debug(f"Received request to delete all {request}")
        # Send confirmation message with two buttons: "Yes!" and "No!"
        await event.reply(
            "Are you sure you want to delete everything?",
            buttons=[
                [Button.inline(reset_yes_description, data=reset_yes_data)],
                [Button.inline(reset_no_description, data=reset_no_data)],
            ],
        )
