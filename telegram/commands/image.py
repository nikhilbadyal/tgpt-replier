"""Handle Image Command."""
# Import necessary libraries and modules
import requests
from asgiref.sync import sync_to_async
from loguru import logger
from telethon import events
from telethon.tl.types import User

from sqlitedb.utils import ErrorCodes

# Import some helper functions
from telegram.commands.strings import no_input, something_bad_occurred
from telegram.commands.utils import SupportedCommands, get_user


# Define a function to download an image from a URL and send it to the user
async def send_image_from_url(
    event: events.NewMessage.Event, user: User, url: str, caption: str
) -> None:
    """Downloads an image from a URL and sends it to the user in Telegram.

    Args:
        event (events.NewMessage.Event): A new message event.
        user (User): A user entity.
        url (str): The URL of the image to download.
        caption (str): The caption for the image.

    Returns:
        None: This function doesn't return anything.
    """

    response = requests.get(url)
    file_bytes = response.content
    await event.send_file(entity=user, file=file_bytes, caption=caption)


# Register the function to handle the /image command
@events.register(events.NewMessage(pattern=f"^{SupportedCommands.IMAGE.value}$"))  # type: ignore
async def handle_image_command(event: events.NewMessage.Event) -> None:
    """Handle /image command.

    Args:
        event (events.NewMessage.Event): A new message event.

    Returns:
        None: This function doesn't return anything.
    """
    # Import the main function for generating image URLs
    from main import gpt

    # Log that an image request has been received
    logger.debug("Received image request")

    # Define a prefix for the image URL
    prefix = f"{SupportedCommands.IMAGE.value}"
    # Pad by 1 to consider the space after command
    prefix = prefix.ljust(len(prefix) + 1)

    # Get the user associated with the message
    telegram_user: User = await get_user(event)

    # Extract the image query from the message text
    result = event.message.text[len(prefix) :]

    # Generate an image URL based on the query
    if result:
        url = await sync_to_async(gpt.image_gen)(telegram_user, result)
        if isinstance(url, ErrorCodes):
            await event.respond(something_bad_occurred)

        # Send the image to the user
        await send_image_from_url(event, telegram_user, url, result)
    else:
        # Send an error message if no input was provided
        await event.respond(no_input)
